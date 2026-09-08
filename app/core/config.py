import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent.parent
CORPUS_DIR = BASE_DIR / "corpus"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# How many candidates to pull back before deciding the response type.
TOP_K_POOL = 8
# How many of those are actually shown/handed to the generator for an
# "answered" response.
TOP_K_ANSWER = 4

# Cosine-similarity floor below which we skip the LLM call entirely and
# say the rulebook doesn't cover the question -- a cheap short-circuit for
# queries with no meaningful match at all. Calibration
# (scripts/calibrate_threshold.py) showed that a single similarity
# threshold CANNOT reliably separate "adjacent but uncovered" from
# "actually answered" -- hard not-covered questions often score as high
# as, or higher than, real answers, because they're topically close by
# design. So this floor only catches the clearly-irrelevant tail; for
# everything above it, the LLM itself judges whether the retrieved
# passages actually answer the question (see app/services/generation.py).
RETRIEVAL_FLOOR = float(os.getenv("RETRIEVAL_FLOOR", "0.30"))

# Below this, retrieval is confident enough to skip the LLM's coverage
# check and treat the top passage as a genuine answer's basis.
HIGH_CONFIDENCE_SCORE = 0.55

# A conflict pair only fires if *both* sides are at least this relevant to
# the question, so a barely-related section riding along in the top-k pool
# can't falsely trigger a conflict response. Calibrated against real
# queries (scripts/calibrate_threshold.py's conflict rows plus manual
# probing): genuine conflict questions have both sides at 0.45+, while a
# question that's merely in the same topic area (e.g. attendance) but
# doesn't actually hit the conflict tends to top out below that.
CONFLICT_SCORE_FLOOR = float(os.getenv("CONFLICT_SCORE_FLOOR", "0.44"))
