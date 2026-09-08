from app.core.config import (
    CONFLICT_SCORE_FLOOR,
    GROQ_API_KEY,
    HIGH_CONFIDENCE_SCORE,
    RETRIEVAL_FLOOR,
    TOP_K_ANSWER,
    TOP_K_POOL,
)
from app.schemas import AskResponse, Citation
from app.services.conflicts import find_conflict
from app.services.generation import assess_and_answer, generate_conflict_explanation
from app.services.retrieval import Retriever

_retriever: Retriever | None = None


def get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever


def _citation(chunk, score: float) -> Citation:
    return Citation(
        section_id=chunk.display_id,
        title=chunk.title,
        source_file=chunk.source_file,
        text=chunk.text,
        score=round(score, 4),
    )


def _confidence(score: float) -> str:
    if score >= HIGH_CONFIDENCE_SCORE:
        return "high"
    if score >= RETRIEVAL_FLOOR:
        return "medium"
    return "low"


def _not_covered_response(results) -> AskResponse:
    nearest = results[:2]
    answer = (
        "The rulebook does not address this. The closest related "
        f"provision I found is {nearest[0].chunk.display_id} "
        f"({nearest[0].chunk.title}), but it does not actually answer "
        "this question."
    )
    return AskResponse(
        type="not_covered",
        answer=answer,
        citations=[_citation(r.chunk, r.score) for r in nearest],
        confidence=None,
    )


def answer_question(question: str) -> AskResponse:
    retriever = get_retriever()
    results = retriever.search(question, top_k=TOP_K_POOL)

    conflict = find_conflict(results, CONFLICT_SCORE_FLOOR)
    if conflict:
        result_a, result_b = conflict
        explanation = generate_conflict_explanation(
            question, result_a.chunk, result_a.score, result_b.chunk, result_b.score
        )
        return AskResponse(
            type="conflict",
            answer=explanation,
            citations=[
                _citation(result_a.chunk, result_a.score),
                _citation(result_b.chunk, result_b.score),
            ],
            confidence=None,
        )

    top = results[0]
    if top.score < RETRIEVAL_FLOOR:
        return _not_covered_response(results)

    # Without a Groq key we can't ask an LLM to judge "adjacent vs.
    # actually answers", so degrade to a stricter score-only cutoff rather
    # than risk confidently answering a question the rulebook is silent on.
    if not GROQ_API_KEY and top.score < HIGH_CONFIDENCE_SCORE:
        return _not_covered_response(results)

    top_results = results[:TOP_K_ANSWER]
    is_covered, answer = assess_and_answer(question, [(r.chunk, r.score) for r in top_results])

    if not is_covered:
        return _not_covered_response(results)

    return AskResponse(
        type="answered",
        answer=answer,
        citations=[_citation(r.chunk, r.score) for r in top_results],
        confidence=_confidence(top.score),
    )
