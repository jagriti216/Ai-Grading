# Future Improvements (Not Yet Implemented)

Ideas that are deliberately scoped and understood, but not built — either because they're lower priority than what's currently in place, or because a simpler fix covers the same problem for now. Kept here as a concrete "here's what I'd do next" list rather than left implicit.

---

## Redis for pipeline intermediate storage

**Problem it solves:** Every graded submission writes its intermediate pipeline stage output (`qp_extracted.json`, `ak_extracted.json`, `grading_ready.json`, `graded_output.json`, etc.) to local disk under `outputs/{submission_id}/`. These files exist purely for debugging/auditability — they let you trace exactly what happened at each stage for any submission — but nothing ever deletes them, so disk usage grows without bound as more submissions get graded over time.

**Why Redis specifically:** Redis supports per-key TTL natively (`SET key value EX <seconds>`), so intermediate pipeline data could auto-expire after a fixed retention window (e.g. 7 days) with no custom cleanup job required. It's also much faster than disk I/O if this data were ever needed for a live "processing..." status view.

**Why it's deferred rather than built now:**
- It's a new infrastructure dependency (a Redis instance to provision/manage) for a problem that has a zero-dependency fix already in place (see below).
- Final results (scores, feedback) already live in MongoDB/local-JSON permanently — Redis would only ever hold *disposable* debugging data, so the durability trade-offs of an in-memory store are actually fine here, but the operational cost (managing another service) isn't justified yet at this project's scale.

**What the implementation would look like, when it's worth doing:**
1. `pip install redis`, add `REDIS_URL` to `.env`.
2. A `pipeline_store.py` module (mirroring the structure of `db/mongo.py`) with `save_stage_output(submission_id, stage_name, data)` / `get_stage_output(...)`, backed by `redis.from_url(...)`.
3. `pipeline/runner.py` writes each stage's intermediate output there (with a TTL) instead of to local JSON files.
4. Same graceful-degradation pattern already used everywhere else in this codebase (Gemini circuit breaker, Mongo→local-JSON fallback): if `REDIS_URL` is unset or Redis is unreachable, fall back to local files rather than hard-failing the pipeline.
5. Final results still go to MongoDB unconditionally — Redis never becomes the system of record for anything that must be durable.

**Interim fix actually shipped instead:** see `CHANGES.md` — local pipeline output directories are now deleted immediately after a submission's result is successfully persisted, since the intermediate files are no longer needed once grading is complete. This solves the unbounded-growth problem today without adding infrastructure; Redis would mainly buy *retention* (keep debugging data for N days instead of deleting it immediately) and *speed*, which isn't a current requirement.

---

## Other deferred ideas (brief)

- **Class/roster-based teacher permissions** instead of "teacher owns the subject-paper they created." Current model is simpler and already built; a full teacher↔class assignment system would be needed if permissions ever need to be more granular than subject ownership.
- **Task queue (Celery/RQ) instead of FastAPI `BackgroundTasks`** for grading jobs — needed once grading volume/concurrency grows past what a single in-process background task can handle reliably.

---

## Concept extraction — what was tried, what shipped, and why

`concept_scorer.py`'s original weakness (documented in `CHANGES.md`): splitting the expected answer purely on `.;\n` meant a comma-separated list of facts (e.g. "pollination, fertilization, and seed formation") collapsed into **one** concept instead of three, letting a partially-matching or even wrong-order answer read as 100% coverage (the Q14 case).

**First attempt — KeyBERT as the primary extractor — was tried and rejected after testing.** KeyBERT extracts representative keyphrases by ranking contiguous n-gram substrings of the source text via embedding similarity + MMR diversification. Tested against real cases, this made concept matching *worse*, not better: because the extracted "concepts" were often grammatically incomplete fragments of the answer key's own wording (e.g. `"seed formation happen in order in"`), a fully correct, fluently *rephrased* student answer scored **lower** coverage than a wrong, scrambled-order answer — the exact shallow-lexical-overlap trap this whole ensemble exists to avoid. Caught by directly testing both cases side by side before shipping it, rather than trusting that "more concepts found" meant "working correctly."

**What shipped instead:** clause-level splitting — extending the delimiter set from `.;\n` to also split on commas and coordinating conjunctions ("and"/"or"). This keeps each concept a complete, grammatical clause (so it embeds meaningfully), while actually fixing the original under-splitting bug. KeyBERT is kept only as a narrow secondary pass — invoked solely when a single clause is still a long run-on (>15 words) with no further delimiter to split on, to avoid leaving one unmatchable 40-word concept.

**What this does *not* fix:** concept coverage was never meant to detect *wrong order* — a scrambled-but-complete answer and a correctly-ordered answer now score the same coverage (as they should for a pure fact-presence check). Order/contradiction detection is `negation_checker.py`'s job, and its order-detection rule still doesn't reliably catch this phrasing (confirmed by testing) — this half of the Q14 case remains open, exactly as `CHANGES.md` already documents ("tighten order rule pattern").
