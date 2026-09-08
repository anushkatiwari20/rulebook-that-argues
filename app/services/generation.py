"""Turns retrieved passages into a final natural-language answer via Groq.

Every prompt path is instructed to use only the supplied passages and to
cite section numbers. If the Groq call fails for any reason (missing key,
network error, rate limit), we fall back to a deterministic template built
directly from the passage text so a network hiccup never crashes the demo
or produces a made-up answer.
"""
from groq import Groq

from app.core.config import GROQ_API_KEY, GROQ_MODEL
from app.services.ingestion import Chunk

_client: Groq | None = None


def _get_client() -> Groq | None:
    global _client
    if not GROQ_API_KEY:
        return None
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def _call_groq(system: str, user: str) -> str | None:
    client = _get_client()
    if client is None:
        return None
    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.1,
            max_tokens=500,
        )
        return completion.choices[0].message.content.strip()
    except Exception:
        return None


_NOT_COVERED_MARKER = "NOT_COVERED"
_COVERED_MARKER = "COVERED"


def assess_and_answer(question: str, passages: list[tuple[Chunk, float]]) -> tuple[bool, str]:
    """Returns (is_covered, answer_text).

    Calibration against the real corpus (scripts/calibrate_threshold.py)
    showed similarity score alone cannot separate "adjacent but silent" from
    "actually answers" -- hard not-covered questions routinely score as
    high as, or higher than, genuine answers, because they're topically
    close by design. So every question that clears the cheap RETRIEVAL_FLOOR
    still gets an explicit LLM coverage judgment here; there is no
    score-based shortcut past it.
    """
    context = "\n\n".join(
        f"[{chunk.display_id} {chunk.title}] (source: {chunk.source_file})\n{chunk.text}"
        for chunk, _ in passages
    )

    system = (
        "You are a precise assistant answering questions about a university "
        "rulebook, and you are strict about never guessing. The passages "
        "below were retrieved because they are topically related to the "
        "question, but being related is not the same as answering it -- "
        "many real student questions ask about something the rulebook "
        "simply never addresses (e.g. asking about a non-medical exam "
        "absence when only medical absence is covered).\n\n"
        "Do not extrapolate, generalize, or fill gaps with what seems "
        "reasonable. Two failure modes to specifically avoid: (1) treating "
        "a policy scoped to one named thing as if it covers a different, "
        "broader, or merely similar thing it doesn't name -- e.g. a "
        "policy about 'ragging' does not thereby cover 'harassment' in "
        "general, and a rule about visitors in common areas does not "
        "thereby settle whether an overnight guest may stay in a private "
        "room; (2) inventing a practical recommendation or judgment call "
        "the passage never makes -- e.g. listing domestic payment methods "
        "does not mean the passage addressed international/foreign "
        "payment feasibility, so don't editorialize about which method "
        "is 'most practical' for a case it doesn't mention. A chain of "
        "inference is fine ONLY when every step is something the "
        "passages explicitly state, with nothing assumed in between.\n\n"
        f"First, decide: do these passages actually state an answer to the "
        f"question, or do they just cover an adjacent topic? Respond with "
        f"exactly one word on the first line, '{_COVERED_MARKER}' or "
        f"'{_NOT_COVERED_MARKER}'.\n"
        f"If {_COVERED_MARKER}: on the following lines, answer the question "
        f"using only these passages, citing section references in plain "
        f"parentheses like (§1.4) -- never other bracket styles.\n"
        f"If {_NOT_COVERED_MARKER}: on the following lines, briefly explain "
        f"in one sentence what the passages actually cover instead, so the "
        f"student understands why their question wasn't answered."
    )
    user = f"Passages:\n{context}\n\nQuestion: {question}"
    result = _call_groq(system, user)
    if result:
        first_line, _, rest = result.partition("\n")
        if _NOT_COVERED_MARKER in first_line.upper():
            return False, rest.strip() or result
        return True, rest.strip() or result

    # Groq unavailable: fall back to the retrieval floor's own judgment
    # (already established by the caller) and hand back the raw passage.
    return True, _fallback_answer(passages)


def _fallback_answer(passages: list[tuple[Chunk, float]]) -> str:
    top_chunk, _ = passages[0]
    snippet = top_chunk.text.strip().split("\n")[0]
    return (
        f"Based on {top_chunk.display_id} ({top_chunk.title}): {snippet} "
        f"(Generation service unavailable — showing the most relevant "
        f"passage directly; see citations below for the full text.)"
    )


def generate_conflict_explanation(
    question: str, chunk_a: Chunk, score_a: float, chunk_b: Chunk, score_b: float
) -> str:
    system = (
        "You are a precise assistant. The user's question touches two "
        "sections of a university rulebook that directly contradict each "
        "other. Explain the contradiction neutrally in 2-4 sentences, "
        "quoting both sections by their reference number, without taking a "
        "side on which one governs. Do not invent a resolution the "
        "rulebook itself does not state."
    )
    user = (
        f"Question: {question}\n\n"
        f"[{chunk_a.display_id} {chunk_a.title}]\n{chunk_a.text}\n\n"
        f"[{chunk_b.display_id} {chunk_b.title}]\n{chunk_b.text}\n\n"
        "Explain the contradiction:"
    )
    result = _call_groq(system, user)
    if result:
        return result

    return (
        f"The rulebook contradicts itself here. {chunk_a.display_id} "
        f"({chunk_a.title}) says: “{chunk_a.text.strip().splitlines()[0]}” "
        f"— while {chunk_b.display_id} ({chunk_b.title}) says: "
        f"“{chunk_b.text.strip().splitlines()[0]}”. Both cannot be "
        "correct at once; this is a genuine conflict in the source "
        "document, not an error in retrieval."
    )
