"""Prints top-match similarity scores for every question in
tests_manual/questions.md so the NOT_COVERED_THRESHOLD in app/config.py can
be picked from real data rather than guessed. Run after any corpus or
question-set change:

    python scripts/calibrate_threshold.py
"""
import json
import re
from pathlib import Path

from app.services.retrieval import Retriever

QUESTIONS_PATH = Path(__file__).parent.parent / "tests_manual" / "questions.md"


def load_questions() -> list[dict]:
    """Parses the '- [type] question text' lines out of questions.md."""
    pattern = re.compile(r"^-\s*\[(answered|not_covered|conflict)\]\s*(.+)$")
    questions = []
    for line in QUESTIONS_PATH.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if match:
            questions.append({"expected": match.group(1), "question": match.group(2).strip()})
    return questions


def main() -> None:
    retriever = Retriever()
    questions = load_questions()
    rows = []
    for q in questions:
        results = retriever.search(q["question"], top_k=3)
        rows.append(
            {
                "expected": q["expected"],
                "question": q["question"],
                "top_score": round(results[0].score, 4),
                "top_section": results[0].chunk.display_id,
                "top_title": results[0].chunk.title,
            }
        )

    rows.sort(key=lambda r: r["top_score"])
    for r in rows:
        print(f"{r['top_score']:.4f}  [{r['expected']:<12}] {r['question'][:60]:<60} -> {r['top_section']} {r['top_title']}")

    not_covered_scores = [r["top_score"] for r in rows if r["expected"] == "not_covered"]
    answered_scores = [r["top_score"] for r in rows if r["expected"] in ("answered", "conflict")]
    if not_covered_scores and answered_scores:
        print()
        print(f"not_covered: min={min(not_covered_scores):.4f} max={max(not_covered_scores):.4f}")
        print(f"answered/conflict: min={min(answered_scores):.4f} max={max(answered_scores):.4f}")
        gap_low, gap_high = max(not_covered_scores), min(answered_scores)
        if gap_low < gap_high:
            print(f"Clean separation. Suggested threshold: {(gap_low + gap_high) / 2:.4f}")
        else:
            print("WARNING: overlapping ranges -- no single threshold cleanly separates the sets.")


if __name__ == "__main__":
    main()
