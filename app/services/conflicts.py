"""Registry of the 3 deliberately planted contradictions.

Detection is deterministic and metadata-driven, not dynamic LLM inference:
if a query's retrieved pool surfaces both sides of one of these pairs
above the relevance floor, the response type is `conflict`. See
CONTRADICTIONS.md for the full rationale behind each pair.
"""
from app.services.retrieval import RetrievalResult

CONFLICT_PAIRS: list[tuple[str, str]] = [
    ("1.4", "2.2"),  # attendance eligibility threshold: 75% vs 65%
    ("1.6", "8.3"),  # who may waive attendance: HOD vs Examination Committee only
    ("5.2", "5.5"),  # late fee: flat Rs.500 vs Rs.100/day
]


def find_conflict(
    results: list[RetrievalResult], score_floor: float
) -> tuple[RetrievalResult, RetrievalResult] | None:
    """Returns the best-evidenced conflicting pair present in `results`, if any.

    More than one registered pair can clear the floor at once -- e.g. any
    attendance-related question tends to pull in several attendance
    sections together, so both the eligibility-threshold pair and the
    waiver-authority pair might both technically qualify. We don't just
    take the first pair in CONFLICT_PAIRS: we score every qualifying pair
    by its weaker side and return the one with the strongest evidence on
    both sides, which in practice matches the pair the question is
    actually about.
    """
    relevant = {r.chunk.section_id: r for r in results if r.score >= score_floor}
    candidates = [
        (relevant[id_a], relevant[id_b])
        for id_a, id_b in CONFLICT_PAIRS
        if id_a in relevant and id_b in relevant
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda pair: min(pair[0].score, pair[1].score))
