"""
intelligence/format_detector.py - Stage 2: True Format Detection
================================================================
Replaces extension-only detection with layered identification:

  1. Magic-byte signature matching (deterministic, high confidence)
  2. Text vs binary heuristic + encoding probe (deterministic)
  3. LLM reasoning for anything still unknown (extensionless files,
     custom binary .dat, proprietary sensor dumps)

The magic-byte table covers container/file-format signatures only - it encodes
no dataset-domain knowledge. Anything it cannot identify is escalated to the
LLM rather than guessed.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from .llm_client import LLMClient, LLMUnavailableError
except ImportError:
    class LLMUnavailableError(Exception): pass
    LLMClient = None

from .models import ArchiveNode, FileFingerprint

logger = logging.getLogger(__name__)

# (signature_bytes, offset, format_name)
MAGIC_SIGNATURES: List[Tuple[bytes, int, str]] = [
    (b"PK\x03\x04", 0, "zip_container"),
    (b"\x89HDF\r\n\x1a\n", 0, "hdf5"),
    (b"PAR1", 0, "parquet"),
    (b"MATLAB", 0, "matlab_v5"),
    (b"\x1f\x8b", 0, "gzip"),
    (b"BZh", 0, "bzip2"),
    (b"\xfd7zXZ", 0, "xz"),
    (b"SQLite format 3\x00", 0, "sqlite"),
    (b"%PDF", 0, "pdf"),
    (b"\x89PNG\r\n\x1a\n", 0, "png"),
    (b"\xff\xd8\xff", 0, "jpeg"),
    (b"TDMS", 0, "tdms"),
    (b"\x93NUMPY", 0, "numpy_npy"),
    (b"ARROW1", 0, "arrow_ipc"),
    (b"ORC", 0, "orc"),
    (b"Obj\x01", 0, "avro"),
]

SNIFF_BYTES = 512
LLM_SAMPLE_BYTES = 96

SYSTEM_PROMPT = """You are a binary file format forensics expert.

You are given metadata and a hex/ASCII sample of the first bytes of files whose
format could NOT be determined from magic-byte signatures or file extension.

Your job: identify the most likely true format of each file and how it should be read.

Respond with ONLY a JSON object in exactly this shape:
{
  "files": [
    {
      "relative_path": "<echo the path given>",
      "detected_format": "<short snake_case format id, e.g. whitespace_delimited_text, fixed_width_binary_float32, json_lines, ini_config, unknown_binary>",
      "is_text": true,
      "is_binary": false,
      "encoding_guess": "utf-8",
      "confidence": 0.85,
      "reasoning": "<one sentence>"
    }
  ]
}

Rules:
- Use "unknown_binary" only if you genuinely cannot tell.
- confidence must be a float between 0.0 and 1.0.
- Include one entry per file given. Echo relative_path exactly.
- Do not invent files that were not provided."""


class FormatDetector:
    """Layered file format identification: magic bytes -> heuristics -> LLM."""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self.llm = llm_client
        self.llm_model_used: Optional[str] = None
        self.used_llm = False

    def detect(self, nodes: List[ArchiveNode]) -> List[FileFingerprint]:
        """Fingerprint every node. LLM is consulted only for unresolved files."""
        fingerprints: List[FileFingerprint] = []
        unresolved: List[FileFingerprint] = []

        for node in nodes:
            fp = self._detect_single(node)
            fingerprints.append(fp)
            if fp.detected_format in ("unknown", "unknown_binary") or fp.confidence < 0.6:
                unresolved.append(fp)

        if unresolved and self.llm is not None:
            self._resolve_with_llm(unresolved)

        return fingerprints

    # -- Deterministic layers ----------------------------------------------

    def _detect_single(self, node: ArchiveNode) -> FileFingerprint:
        path = Path(node.absolute_path)
        head = b""
        try:
            with open(path, "rb") as f:
                head = f.read(SNIFF_BYTES)
        except Exception as e:
            logger.debug(f"[FormatDetector] Could not read {node.relative_path}: {e}")

        magic_hex = head[:16].hex()

        # Layer 1: magic-byte signatures
        for signature, offset, format_name in MAGIC_SIGNATURES:
            if head[offset : offset + len(signature)] == signature:
                return FileFingerprint(
                    relative_path=node.relative_path,
                    extension=node.extension,
                    magic_bytes_hex=magic_hex,
                    detected_format=format_name,
                    detection_method="magic_bytes",
                    confidence=0.99,
                    is_binary=format_name not in ("json_lines",),
                    is_text=False,
                )

        # Layer 2: text vs binary heuristic
        is_text, encoding = self._probe_text(head)
        if is_text:
            text_format = self._classify_text_shape(head, node.extension)
            return FileFingerprint(
                relative_path=node.relative_path,
                extension=node.extension,
                magic_bytes_hex=magic_hex,
                detected_format=text_format,
                detection_method="text_heuristic" if text_format != "unknown" else "extension",
                confidence=0.85 if text_format != "unknown" else 0.4,
                is_text=True,
                is_binary=False,
                encoding_guess=encoding,
            )

        # Unresolved binary - will be escalated to the LLM
        return FileFingerprint(
            relative_path=node.relative_path,
            extension=node.extension,
            magic_bytes_hex=magic_hex,
            detected_format="unknown_binary",
            detection_method="extension",
            confidence=0.2,
            is_text=False,
            is_binary=True,
        )

    @staticmethod
    def _probe_text(head: bytes) -> Tuple[bool, Optional[str]]:
        """Decide if the byte sample looks like decodable text."""
        if not head:
            return False, None
        if b"\x00" in head:
            return False, None

        for encoding in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                decoded = head.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                continue
            printable = sum(1 for ch in decoded if ch.isprintable() or ch in "\r\n\t")
            if printable / max(1, len(decoded)) > 0.9:
                return True, encoding

        return False, None

    @staticmethod
    def _classify_text_shape(head: bytes, extension: str) -> str:
        """
        Identify the structural shape of a text file from its first lines.
        Purely structural - no column-name or domain interpretation here.
        """
        try:
            text = head.decode("utf-8", errors="ignore")
        except Exception:
            return "unknown"

        stripped = text.lstrip()
        if not stripped:
            return "empty_text"

        # JSON / JSON Lines
        if stripped[0] in "{[":
            first_line = stripped.splitlines()[0] if stripped.splitlines() else ""
            try:
                json.loads(first_line)
                return "json_lines"
            except Exception:
                return "json"

        if stripped.startswith("<?xml") or stripped.startswith("<"):
            return "xml"

        # SQL dump detection
        upper = stripped[:400].upper()
        if any(kw in upper for kw in ("CREATE TABLE", "INSERT INTO", "DROP TABLE")):
            return "sql_dump"

        # Delimiter frequency analysis. Requires at least 2 non-empty lines with a
        # consistent delimiter count - a single line containing one comma is prose,
        # not a delimited table.
        lines = [ln for ln in text.splitlines() if ln.strip()][:6]
        if not lines:
            return "unknown"

        # Drop a possibly-truncated final line (the byte sample may cut mid-row)
        comparable = lines[:-1] if len(lines) > 2 else lines
        if len(comparable) < 2:
            return "plain_text"

        delimiter_scores: Dict[str, int] = {}
        for delim, name in ((",", "csv"), ("\t", "tsv"), (";", "semicolon_delimited")):
            counts = [ln.count(delim) for ln in comparable]
            if counts[0] > 0 and len(set(counts)) == 1:
                delimiter_scores[name] = counts[0]

        if delimiter_scores:
            return max(delimiter_scores, key=delimiter_scores.get)

        # Whitespace-delimited numeric matrix (headerless sensor matrix style)
        token_counts = [len(ln.split()) for ln in comparable]
        if token_counts[0] > 1 and len(set(token_counts)) == 1:
            return "whitespace_delimited_text"

        return "plain_text"

    # -- LLM escalation ----------------------------------------------------

    def _resolve_with_llm(self, unresolved: List[FileFingerprint]) -> None:
        """Ask the LLM to identify formats we could not resolve deterministically."""
        # Deduplicate by (extension, magic prefix) so we spend one slot per distinct shape
        representatives: Dict[str, FileFingerprint] = {}
        for fp in unresolved:
            key = f"{fp.extension}|{fp.magic_bytes_hex[:8]}"
            representatives.setdefault(key, fp)

        payload = []
        for fp in list(representatives.values())[:25]:
            payload.append({
                "relative_path": fp.relative_path,
                "extension": fp.extension or "(none)",
                "first_bytes_hex": fp.magic_bytes_hex,
                "ascii_preview": self._ascii_preview(fp),
            })

        user_prompt = (
            "Identify the true format of these files.\n\n"
            + json.dumps({"files": payload}, indent=2)
        )

        try:
            response = self.llm.complete_json(SYSTEM_PROMPT, user_prompt)
        except LLMUnavailableError as e:
            logger.warning(f"[FormatDetector] LLM unavailable for format resolution: {e}")
            return

        self.used_llm = True
        self.llm_model_used = response.model_used

        results = response.data.get("files", [])
        if not isinstance(results, list):
            logger.warning("[FormatDetector] LLM returned unexpected shape for 'files'")
            return

        # Index the LLM answers, then apply to every fingerprint sharing the shape key
        answers: Dict[str, dict] = {}
        for item in results:
            if isinstance(item, dict) and item.get("relative_path"):
                answers[item["relative_path"]] = item

        for key, representative in representatives.items():
            answer = answers.get(representative.relative_path)
            if not answer:
                continue

            for fp in unresolved:
                if f"{fp.extension}|{fp.magic_bytes_hex[:8]}" != key:
                    continue
                fp.detected_format = str(answer.get("detected_format", fp.detected_format))
                fp.detection_method = "llm"
                fp.is_text = bool(answer.get("is_text", fp.is_text))
                fp.is_binary = bool(answer.get("is_binary", fp.is_binary))
                fp.encoding_guess = answer.get("encoding_guess") or fp.encoding_guess
                fp.llm_reasoning = answer.get("reasoning")
                try:
                    fp.confidence = float(answer.get("confidence", fp.confidence))
                except (TypeError, ValueError):
                    pass

    @staticmethod
    def _ascii_preview(fp: FileFingerprint) -> str:
        """Reconstruct a short printable preview from the stored hex sample."""
        try:
            raw = bytes.fromhex(fp.magic_bytes_hex)
        except ValueError:
            return ""
        return "".join(chr(b) if 32 <= b < 127 else "." for b in raw[:LLM_SAMPLE_BYTES])
