"""Parses the mixed-format corpus into a flat list of clause-level Chunks.

Each source format gets its own small parser (markdown headings, and PDF
extracted text) because the two don't look the same on disk: markdown
headings keep their '## ' prefix and the literal '§' section-sign
character, while text extracted from the PDF is unprefixed plain text with
the word 'Section' spelled out (see scripts/build_pdf.py for why). Both
converge on the same Chunk shape so retrieval doesn't care where a clause
came from.
"""
import re
from dataclasses import dataclass

from pypdf import PdfReader

from app.core.config import CORPUS_DIR

_MD_HEADING = re.compile(r"^##\s+§\s*(\d+\.\d+)\s+(.+)$")
_PDF_HEADING = re.compile(r"^Section\s+(\d+\.\d+)\s+(.+)$")


@dataclass(frozen=True)
class Chunk:
    section_id: str  # e.g. "1.4"
    title: str
    text: str
    source_file: str
    format: str  # "markdown" | "table" | "pdf"

    @property
    def display_id(self) -> str:
        return f"§{self.section_id}"


def _split_on_headings(lines: list[str], heading_re: re.Pattern) -> list[tuple[str, str, str]]:
    """Returns [(section_id, title, body_text), ...] for one document's lines."""
    sections: list[tuple[str, str, list[str]]] = []
    for line in lines:
        match = heading_re.match(line.strip())
        if match:
            sections.append((match.group(1), match.group(2).strip(), []))
        elif sections:
            sections[-1][2].append(line)
    return [(sid, title, "\n".join(body).strip()) for sid, title, body in sections]


def parse_markdown(path) -> list[Chunk]:
    lines = path.read_text(encoding="utf-8").splitlines()
    fmt = "table" if path.name == "fee_deadlines_table.md" else "markdown"
    return [
        Chunk(section_id=sid, title=title, text=body, source_file=path.name, format=fmt)
        for sid, title, body in _split_on_headings(lines, _MD_HEADING)
    ]


def parse_pdf(path) -> list[Chunk]:
    reader = PdfReader(str(path))
    full_text = "\n".join(page.extract_text() for page in reader.pages)
    lines = full_text.splitlines()
    return [
        Chunk(section_id=sid, title=title, text=body, source_file=path.name, format="pdf")
        for sid, title, body in _split_on_headings(lines, _PDF_HEADING)
    ]


def load_corpus() -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(CORPUS_DIR.iterdir()):
        if path.suffix == ".md":
            chunks.extend(parse_markdown(path))
        elif path.suffix == ".pdf":
            chunks.extend(parse_pdf(path))
    if not chunks:
        raise RuntimeError(f"No chunks parsed from corpus at {CORPUS_DIR}")
    return chunks
