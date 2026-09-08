"""Generates corpus/society_constitution.pdf from society_constitution_source.md.

The source is authored as markdown with '# ' chapter titles and '## §X.Y Title'
section headings. This script renders it as a real PDF (via fpdf2) so the
ingestion pipeline has to genuinely extract text from a PDF, not a
markdown file wearing a PDF extension.
"""
from pathlib import Path

from fpdf import FPDF

SOURCE = Path(__file__).parent / "society_constitution_source.md"
OUTPUT = Path(__file__).parent.parent / "corpus" / "society_constitution.pdf"

_REPLACEMENTS = {
    "—": " - ",
    "–": "-",
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    "₹": "Rs. ",
    # The core PDF font's non-embedded encoding does not round-trip the
    # section-sign glyph reliably through text extraction (it comes back
    # as U+FFFD). Spell it out instead so PDF-derived chunks parse the
    # same way as the markdown-derived ones.
    "§": "Section ",
}


def _sanitize(text: str) -> str:
    for src, dst in _REPLACEMENTS.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", errors="ignore").decode("latin-1")


def build_pdf() -> None:
    text = _sanitize(SOURCE.read_text(encoding="utf-8"))
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            pdf.ln(3)
            continue
        if line.startswith("# "):
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 10, line[2:], new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
        elif line.startswith("## "):
            pdf.set_font("Helvetica", "B", 13)
            pdf.ln(2)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 8, line[3:], new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
        else:
            pdf.set_font("Helvetica", "", 11)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")

    pdf.output(str(OUTPUT))
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    build_pdf()
