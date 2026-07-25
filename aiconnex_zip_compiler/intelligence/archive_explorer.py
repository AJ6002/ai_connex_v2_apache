"""
intelligence/archive_explorer.py - Stage 1: Archive Exploration
===============================================================
Fully deterministic recursive archive exploration. No LLM.

Handles .zip, .tar, .tar.gz, .tgz, .gz and recursively unpacks nested archives
up to a depth limit. Produces a complete ArchiveTree that every later stage
reasons over.

This stage intentionally does NOT filter or classify anything - it reports
every file it finds, including readmes, PDFs, and unknown binaries, so the
LLM stages get the full picture rather than a pre-filtered view.
"""

from __future__ import annotations

import logging
import os
import tarfile
import zipfile
from pathlib import Path
from typing import List, Optional, Set

from .models import ArchiveNode, ArchiveTree

logger = logging.getLogger(__name__)

ARCHIVE_EXTENSIONS = {".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz"}
MAX_NESTING_DEPTH = 6


class ArchiveExplorer:
    """Recursively extracts and inventories an archive or directory."""

    def __init__(self, max_depth: int = MAX_NESTING_DEPTH) -> None:
        self.max_depth = max_depth
        self._nested_count = 0

    def explore(self, target_path: Path, extract_root: Path) -> ArchiveTree:
        """
        Extract (if needed) and walk the target, returning a complete ArchiveTree.

        Parameters
        ----------
        target_path : Path
            Input .zip / .tar.gz / directory / single file.
        extract_root : Path
            Temp directory to extract archives into.
        """
        target_path = Path(target_path)
        extract_root = Path(extract_root)
        extract_root.mkdir(parents=True, exist_ok=True)
        self._nested_count = 0

        if target_path.is_dir():
            scan_root = target_path
        elif self._is_archive(target_path):
            self._extract_archive(target_path, extract_root)
            self._unpack_nested(extract_root, depth=1)
            scan_root = extract_root
        else:
            # Single non-archive file - scan its parent but only report this file
            scan_root = target_path.parent

        nodes = self._walk(scan_root, target_path)

        directory_layout = sorted({
            str(Path(n.relative_path).parent).replace("\\", "/")
            for n in nodes
            if str(Path(n.relative_path).parent) not in (".", "")
        })

        return ArchiveTree(
            archive_name=target_path.name,
            root_path=str(scan_root),
            nodes=nodes,
            max_depth=max((n.depth for n in nodes), default=0),
            nested_archive_count=self._nested_count,
            total_size_bytes=sum(n.size_bytes for n in nodes),
            directory_layout=directory_layout,
        )

    # -- Internals ---------------------------------------------------------

    @staticmethod
    def _is_archive(path: Path) -> bool:
        name = path.name.lower()
        if name.endswith(".tar.gz") or name.endswith(".tar.bz2") or name.endswith(".tar.xz"):
            return True
        return path.suffix.lower() in ARCHIVE_EXTENSIONS

    def _extract_archive(self, archive_path: Path, destination: Path) -> bool:
        """Extract a single archive. Returns True on success."""
        destination.mkdir(parents=True, exist_ok=True)
        name = archive_path.name.lower()

        try:
            if name.endswith(".zip"):
                with zipfile.ZipFile(archive_path, "r") as zf:
                    zf.extractall(destination)
                return True

            if any(name.endswith(ext) for ext in (".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tar.xz")):
                with tarfile.open(archive_path, "r:*") as tf:
                    tf.extractall(destination)
                return True

            if name.endswith(".gz"):
                import gzip
                import shutil

                out_path = destination / archive_path.stem
                with gzip.open(archive_path, "rb") as fin, open(out_path, "wb") as fout:
                    shutil.copyfileobj(fin, fout)
                return True

        except Exception as e:
            logger.warning(f"[ArchiveExplorer] Failed to extract {archive_path.name}: {e}")

        return False

    def _unpack_nested(self, directory: Path, depth: int) -> None:
        """Recursively unpack nested archives found inside `directory`."""
        if depth >= self.max_depth:
            logger.warning(f"[ArchiveExplorer] Max nesting depth {self.max_depth} reached at {directory}")
            return

        # Snapshot the file list first so we don't walk newly created dirs mid-iteration
        pending: List[Path] = []
        for root, _, files in os.walk(directory):
            for fname in files:
                fpath = Path(root) / fname
                if self._is_archive(fpath):
                    pending.append(fpath)

        for archive_path in pending:
            extract_target = archive_path.parent / f"{archive_path.stem}_extracted"
            if extract_target.exists():
                continue
            if self._extract_archive(archive_path, extract_target):
                self._nested_count += 1
                logger.debug(f"[ArchiveExplorer] Unpacked nested archive: {archive_path.name}")
                self._unpack_nested(extract_target, depth + 1)

    def _walk(self, scan_root: Path, original_target: Path) -> List[ArchiveNode]:
        """Walk scan_root and build ArchiveNode entries for every file."""
        nodes: List[ArchiveNode] = []

        # Single non-archive file case
        if original_target.is_file() and not self._is_archive(original_target):
            nodes.append(
                ArchiveNode(
                    absolute_path=str(original_target),
                    relative_path=original_target.name,
                    filename=original_target.name,
                    extension=original_target.suffix.lower(),
                    size_bytes=original_target.stat().st_size,
                    depth=0,
                )
            )
            return nodes

        for path in sorted(scan_root.rglob("*")):
            if not path.is_file():
                continue

            try:
                rel = path.relative_to(scan_root)
            except ValueError:
                rel = Path(path.name)

            rel_str = str(rel).replace("\\", "/")

            # Identify whether this file came out of a nested archive
            parent_archive: Optional[str] = None
            for part in rel.parts:
                if part.endswith("_extracted"):
                    parent_archive = part.replace("_extracted", "")
                    break

            nodes.append(
                ArchiveNode(
                    absolute_path=str(path),
                    relative_path=rel_str,
                    filename=path.name,
                    extension=path.suffix.lower(),
                    size_bytes=path.stat().st_size,
                    depth=len(rel.parts) - 1,
                    parent_archive=parent_archive,
                )
            )

        return nodes
