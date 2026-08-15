"""
aiconnex_agent/platform_kb/normalizer.py

Markdown AST Structural Normalizer for Platform Knowledge Base.
Parses Markdown documents into structured section hierarchies (NormalizedSection objects),
extracting heading breadcrumb paths, prose, fenced code blocks, and markdown tables.

Saves output JSON records under Tier `aiconnex_knowledge/07_normalized_documents/`
per the content-first discipline.
"""

import os
import re
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Literal

logger = logging.getLogger(__name__)

NORMALIZED_DOCS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "aiconnex_knowledge",
    "07_normalized_documents",
)


@dataclass
class NormalizedSection:
    section_id: str
    document_id: str
    heading_level: int
    heading_text: str
    section_path: str
    content: str
    content_type: Literal["prose", "code", "table", "mixed"] = "prose"
    code_blocks: List[Dict[str, str]] = field(default_factory=list)
    tables: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MarkdownNormalizer:
    """
    Structural Markdown AST Parser and Normalizer.
    Converts raw markdown text into a flat sequence of NormalizedSection objects,
    preserving heading hierarchy breadcrumbs, code blocks, and markdown tables.
    """

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or NORMALIZED_DOCS_DIR

    def parse_markdown(self, markdown_text: str, document_id: str = "DOC-UNKNOWN") -> List[NormalizedSection]:
        """
        Parses raw markdown text into structured NormalizedSection records.
        """
        lines = markdown_text.splitlines()
        sections: List[NormalizedSection] = []

        # Heading hierarchy stack: list of (level, heading_text)
        heading_stack: List[tuple[int, str]] = []

        current_heading_level = 0
        current_heading_text = "Overview"
        current_content_lines: List[str] = []
        current_code_blocks: List[Dict[str, str]] = []
        current_tables: List[str] = []

        in_code_block = False
        code_block_lang = ""
        code_block_lines: List[str] = []

        in_table = False
        table_lines: List[str] = []

        sec_counter = 1

        def flush_current_section():
            nonlocal sec_counter, current_content_lines, current_code_blocks, current_tables
            content_str = "\n".join(current_content_lines).strip()
            if not content_str and not current_code_blocks and not current_tables:
                return

            # Generate breadcrumb path
            breadcrumb_parts = [h_text for _, h_text in heading_stack]
            if not breadcrumb_parts:
                breadcrumb_parts = [current_heading_text]
            section_path = " > ".join(breadcrumb_parts)

            # Determine content type
            has_text = bool(content_str)
            has_code = len(current_code_blocks) > 0
            has_table = len(current_tables) > 0

            if has_code and not has_text and not has_table:
                c_type = "code"
            elif has_table and not has_text and not has_code:
                c_type = "table"
            elif (has_code and has_text) or (has_table and has_text) or (has_code and has_table):
                c_type = "mixed"
            else:
                c_type = "prose"

            sec_id = f"SEC-{sec_counter:04d}"
            sec = NormalizedSection(
                section_id=sec_id,
                document_id=document_id,
                heading_level=current_heading_level,
                heading_text=current_heading_text,
                section_path=section_path,
                content=content_str,
                content_type=c_type,
                code_blocks=list(current_code_blocks),
                tables=list(current_tables),
            )
            sections.append(sec)
            sec_counter += 1

            # Reset section buffers
            current_content_lines = []
            current_code_blocks = []
            current_tables = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # 1. Handle Code Fences (```)
            if line.strip().startswith("```"):
                if not in_code_block:
                    # Starting code block
                    in_code_block = True
                    code_block_lang = line.strip().lstrip("`").strip()
                    code_block_lines = []
                else:
                    # Ending code block
                    in_code_block = False
                    code_text = "\n".join(code_block_lines)
                    current_code_blocks.append({"language": code_block_lang or "text", "code": code_text})
                    current_content_lines.append(f"``` {code_block_lang}\n{code_text}\n```")
                    code_block_lines = []
                i += 1
                continue

            if in_code_block:
                code_block_lines.append(line)
                i += 1
                continue

            # 2. Handle Markdown Tables (| col1 | col2 |)
            if "|" in line and line.strip().startswith("|") and line.strip().endswith("|"):
                if not in_table:
                    in_table = True
                    table_lines = [line]
                else:
                    table_lines.append(line)
                i += 1
                continue

            if in_table:
                # Table ended
                in_table = False
                raw_table = "\n".join(table_lines)
                current_tables.append(raw_table)
                current_content_lines.append(raw_table)
                table_lines = []

            # 3. Handle Headings (#, ##, ###, etc.)
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
            if heading_match:
                # Flush previous section
                flush_current_section()

                level = len(heading_match.group(1))
                h_text = heading_match.group(2).strip()

                # Clean heading text from badges or icons if present
                h_text_clean = re.sub(r"^[\W_]+", "", h_text).strip() or h_text

                # Update heading stack for breadcrumbs
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                heading_stack.append((level, h_text_clean))

                current_heading_level = level
                current_heading_text = h_text_clean
                i += 1
                continue

            # 4. Standard Prose Line
            current_content_lines.append(line)
            i += 1

        # Handle trailing table if file ended on table
        if in_table:
            raw_table = "\n".join(table_lines)
            current_tables.append(raw_table)
            current_content_lines.append(raw_table)

        # Flush final section
        flush_current_section()

        return sections

    def normalize_file(self, file_path: str, document_id: str = "DOC-UNKNOWN") -> List[NormalizedSection]:
        """
        Reads a markdown file from disk, normalizes it, and returns NormalizedSection records.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Markdown file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return self.parse_markdown(content, document_id=document_id)

    def save_normalized_document(self, sections: List[NormalizedSection], document_id: str) -> str:
        """
        Saves normalized sections as a JSON file under Tier 07 (aiconnex_knowledge/07_normalized_documents/).
        Creates Tier 07 directory on demand if it does not exist.
        """
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
            # Add a README to document Tier 07
            readme_path = os.path.join(self.output_dir, "README.md")
            if not os.path.exists(readme_path):
                with open(readme_path, "w", encoding="utf-8") as f:
                    f.write("# Tier 07 — Normalized Documents\n\nContains structured Markdown AST sections with heading hierarchy breadcrumbs, prose, code blocks, and markdown tables.\n")

        output_filename = f"{document_id}_normalized.json"
        output_path = os.path.join(self.output_dir, output_filename)

        data = {
            "document_id": document_id,
            "section_count": len(sections),
            "sections": [s.to_dict() for s in sections],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved normalized document to: {output_path}")
        return output_path
