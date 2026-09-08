# The Rulebook That Argues With Itself

A question-answering service over a deliberately self-contradictory
university rulebook. It cites the section it's quoting, admits when the
rulebook doesn't say, and tells you when the rulebook says two different
things.

## What this is

- **Corpus**: an original ~6,100-word rulebook for a fictional
  "Bannerworth University" — attendance/exam rules, medical exemptions,
  grading, hostel handbook, fee policy (with a deadlines table), a
  scholarship policy, an academic integrity code, a grievance/committee
  chapter, library rules, an IT acceptable-use policy, a campus safety
  chapter, and a society constitution — spread across markdown files, a
  markdown table, and a genuinely-parsed PDF. See `corpus/`.
- **3 planted contradictions**, deliberately written in and documented in
  [`CONTRADICTIONS.md`](CONTRADICTIONS.md): the attendance eligibility
  threshold (75% vs. 65%), who may waive it (Head of Department vs. the
  Examination Committee), and the late fee amount (a flat fee in prose vs.
  a per-day fine in a table).
- **One `POST /ask` endpoint** plus a static frontend that always shows
  the answer next to the passages it came from — section reference,
  source file, and similarity score, never behind a click.
- **Three response types**: `answered` (with citations), `not_covered`
  (the rulebook is silent), `conflict` (two sections disagree).

## Architecture

```
Browser (static HTML/JS)
        |  POST /ask {"question": "..."}
        v
FastAPI app                              app/
 |- main.py            app factory, startup warm-up, static mount
 |- api/routes.py       POST /ask route
 |- schemas.py          Pydantic request/response models
 |- core/config.py      env vars, thresholds, model names
 \- services/
     |- ingestion.py    parses corpus/*.md, the fee table, and the PDF
     |                   into clause-level chunks (one per §X.Y section)
     |- embeddings.py   sentence-transformers (all-MiniLM-L6-v2), local,
     |                   free, no API key
     |- retrieval.py    cosine-similarity search (numpy) over chunk
     |                   embeddings
     |- conflicts.py    registry of the 3 known conflicting section
     |                   pairs; picks the best-evidenced pair present
     |                   in a retrieval
     |- pipeline.py     orchestrates: retrieve -> conflict check ->
     |                   coverage check -> answer
     \- generation.py   Groq API (free tier) writes the final answer and
                         judges whether the passages actually cover the
                         question at all (see "Why not a similarity
                         threshold?" below); falls back to a template if
                         Groq is unavailable
```

No vector database — the corpus is ~65 clause-level chunks, so brute-force
cosine similarity in numpy is instant and keeps the dependency list short.

## Why not just a similarity threshold for "not covered"?

The obvious design is: if the top retrieval score is below some cutoff,
say "not covered." We tried that and calibrated it against the real
corpus (`scripts/calibrate_threshold.py`) — it doesn't work. Hard
not-covered questions are *deliberately* topically adjacent to real
content (that's what makes them hard), so they routinely score as high
as, or higher than, genuine answers. A single number can't separate them.

So retrieval keeps a cheap low floor (`RETRIEVAL_FLOOR`) that only catches
questions with no meaningful match at all. Everything above that floor is
handed to the LLM with an explicit instruction: decide whether these
specific passages actually state an answer, or whether they're just
adjacent — and say so. That's a judgment call, not a threshold, which is
the whole point of the exercise.

Conflict detection is the one place a fixed approach *does* work: the 3
contradictions are known in advance, so they're tagged by section ID in
`app/services/conflicts.py` and checked deterministically. When more than one
tagged pair clears the relevance floor for a given question (attendance
questions tend to pull in several attendance-related sections at once),
the pair with the strongest evidence on its weaker side wins, rather than
just the first one registered.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

copy .env.example .env          # Windows
# cp .env.example .env          # macOS/Linux
# then edit .env and set GROQ_API_KEY (free at https://console.groq.com)

python scripts/build_pdf.py     # regenerates corpus/society_constitution.pdf
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000.

Without `GROQ_API_KEY` set, the app still runs: it falls back to a
template answer built directly from the top retrieved passage, and to a
stricter score-only cutoff for the covered/not-covered decision (since
there's no LLM available to make that judgment call). Generation quality
and not-covered accuracy are both meaningfully better with the key set.

## Verifying it

```bash
python scripts/calibrate_threshold.py   # prints retrieval scores for every
                                         # test question; used to pick
                                         # RETRIEVAL_FLOOR and CONFLICT_SCORE_FLOOR
```

`tests_manual/questions.md` has the 3 conflict-triggering questions, a
handful of normal answered questions, and the 25 required not-covered
questions — this is the set used for manual verification and the demo
video. `CONTRADICTIONS.md` is the answer key for the 3 planted
contradictions.

## Repo layout

```
app/
  main.py         FastAPI app factory + startup + static mount
  schemas.py      Pydantic request/response models
  api/            HTTP routes
  core/           config (env vars, thresholds, model names)
  services/       ingestion, embeddings, retrieval, conflicts,
                  generation, pipeline (all the actual logic)
corpus/         the rulebook itself (mixed formats)
scripts/        PDF build script, threshold calibration script
static/         frontend (plain HTML/CSS/JS, no build step)
tests_manual/   the test question set
CONTRADICTIONS.md   answer key for the 3 planted contradictions
```
