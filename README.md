# AI Exam Grading System

This project grades exam answers automatically. You give it three PDFs — the question paper, the answer key, and a student's answer sheet (even handwritten ones) — and it hands back a score for every question, plus feedback explaining *why* that score was given.

It comes with a web app: a FastAPI backend that does all the grading work, and a React frontend where a teacher can upload papers and see results.

## Why not just ask an AI chatbot to grade it?

You could — a lot of tools do exactly that. But "ask an LLM to grade this" is hard to trust: it can't tell you *why* it gave a score, and it can silently change its mind between runs.

This project takes a more careful approach. The actual grading decision is made by a **small transformer model that was trained specifically for grading** (not a general chatbot), backed up by a few plain, checkable rules — did the student mention the right facts, does their answer contradict the correct one, is their math actually equivalent to the expected formula. Every score comes with a breakdown of exactly which of these checks contributed to it, so nothing is a black box.

AI (Gemini) is only used for the "boring" parts — reading messy handwriting and pulling out structured text. It never makes the actual grading call.

## How it works, step by step

Think of it as an assembly line with five stations. Your three PDFs go in one end, and a graded, explained result comes out the other.

1. **Read the PDFs.** If a PDF has selectable text, we just read it directly. If it's a scan or handwriting, we send it to Gemini's vision model to transcribe it into text.
2. **Make sense of the text.** Raw transcribed text is messy. This step figures out where one question ends and the next begins, and lines up each question with its marks, its correct answer, and the student's answer.
3. **Grade each answer.** This is the heart of the system:
   - Math and formula questions are checked with actual algebra (via SymPy) — so "x + 2" and "2 + x" are correctly treated as identical, even though they're not the same string.
   - Everything else goes through the trained grading model, which is double-checked against two extra signals: how semantically similar the student's answer is to the correct one, and how many of the expected key facts they actually mentioned. If the model looks like it's being fooled by an answer that "sounds right" but doesn't say the right things, its vote gets down-weighted automatically.
   - A separate check looks for outright contradictions (e.g., the student says the opposite of the correct answer) and penalizes those regardless of how similar the wording sounds.
4. **Write feedback.** For each question, Gemini generates a short, human-readable note: what the student got right, what they missed, and a tip for improvement.
5. **Serve it all through the app.** The FastAPI backend ties steps 1–4 together, saves everything to a database (MongoDB, with a local backup if the database is unreachable), and the React frontend is what a teacher actually interacts with — uploading sheets, watching grading progress, and reading results.

**If something external breaks, the system doesn't fall over.** If Gemini's API is down or MongoDB can't be reached, each step quietly falls back to a simpler local method instead of crashing the whole pipeline.

## The grading model, briefly

The model at the center of step 3 is a fine-tuned version of `deberta-v3-base`, trained on about 12,000 real graded answers pulled from two public grading-research datasets (one science-focused, one CS-focused). It learned to read a question, the expected answer, and a student's answer, and output a correctness score between 0 and 1.

Rather than trusting that model alone, its score is blended with two other signals — how similar the wording is, and how many key facts are actually covered — so a fluent-sounding but factually empty answer doesn't slip through with a high score.

If you want the deeper technical details (training setup, exact scoring formulas, evaluation metrics), see [`CHANGES.md`](CHANGES.md).

## What it's built with

- **Grading brain:** PyTorch, HuggingFace Transformers, Sentence-Transformers, SymPy, scikit-learn
- **Backend:** FastAPI, MongoDB
- **Frontend:** React, Vite, Tailwind CSS
- **Reading PDFs:** pdfplumber, PyMuPDF, and Gemini Vision for handwriting/scans

## Honest limitations

This is a working prototype, not a polished commercial product. A few things worth knowing before you rely on it:

- The model was only trained on science and CS answers — grading history, literature, or economics answers is untested territory.
- The "did they contradict the answer" check uses hand-written rules that were tuned on a small set of examples, so it may miss contradictions in subjects it hasn't seen before.
- Splitting an answer into "key facts" is done with simple text rules, not true language understanding, so it can occasionally miscount.
- Nobody has load-tested this at scale yet — it's been built and tested for correctness, not for handling thousands of simultaneous uploads.

See [`CHANGES.md`](CHANGES.md) for the full, detailed history of bugs found and fixed.

## Running it yourself

Full step-by-step instructions are in [`RUN.md`](RUN.md). The short version:

```bash
# Backend
pip install -e ".[dev]"
cp .env.example .env   # add your own API keys here
uvicorn stage5_fastapi.main:app --reload

# Frontend (in a second terminal)
cd frontend
npm install
npm run dev
```

Then open the frontend URL it prints in your browser.

## Running the tests

```bash
pip install -e ".[dev]"
pytest -v
```

This checks the parts of the system that don't need to download large AI models — the math/formula scorer, the scoring-blend logic, and the contradiction checks — so it runs fast and doesn't need internet access. The AI-model parts (the trained grader, similarity checks, handwriting OCR) are tested by hand rather than automatically, since they need multi-hundred-megabyte models downloaded first.
