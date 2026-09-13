# Stage 3 — Known Issues & Pending Changes

## ⚠️ Overfitting Risk Warning

The current `negation_checker.py` has hardcoded regex rules written
specifically to fix errors observed in the 15-question test set.
This is a form of **rule overfitting** — rules tuned to specific questions
may break on new inputs. Examples:

- `carbon vs oxygen` rule → written for Q1/Q6/Q13 specifically
- `four-chamber vs two-chamber` → written for Q7
- `voltage = power` → written for Q11
- `pollination → seed order` → written for Q14

**Risk:** A student who legitimately mentions oxygen in a photosynthesis
answer about oxygen release will be wrongly penalized. A question about
oxygen transport in blood would falsely trigger the carbon/oxygen rule.

**Fix (do before production):** Replace hardcoded relational rules with
a general NLI-based contradiction check that doesn't rely on specific
domain vocabulary. Use `cross-encoder/nli-deberta-v3-small` for ALL
contradiction detection, not just when negation words are present.

---

## Known Scoring Issues

### Q2 — Ohm's Law formula wrong, score too high (0.7/2)
- Student: "I = V + R" (wrong — should be V = IR)
- Issue: DeBERTa score high (0.66) because it recognizes Ohm's law context
- Root cause: Formula questions routed to text scorer instead of math scorer
- Fix: `detector.py` should detect formula questions even without
  "calculate" keyword. Add rule: if expected answer contains a formula
  AND student answer contains a formula → route to math scorer.
- File: `detector.py` → `is_math_question()`

### Q10 — Digestive system partial answer, score too high (2.6/4)
- Student: "Food is completely digested in the stomach and absorbed there"
- Issue: Misses intestine, but DeBERTa (0.70) and SBERT (0.80) both high
- Root cause: Student answer is topically correct but factually incomplete.
  Models reward topic overlap, not completeness.
- Fix: Concept coverage should penalize missing concepts more aggressively.
  When `matched/total < 0.5`, cap final score at `0.4 × max_marks`.
- File: `normalizer.py` → add completeness cap

### Q14 — Wrong order of pollination/seeds, score too high (3.4/4)
- Student: "Seeds are formed first and then pollination happens"
- Issue: Order contradiction rule not firing. Expected has
  "pollination, fertilization, seed formation" as a comma-separated
  list — concept extractor treats it as ONE concept, matches 1/1 = 100%
- Root cause: `concept_scorer.py` comma splitting works but
  negation_checker order rule regex doesn't match this exact phrasing
- Fix 1: `negation_checker.py` → tighten order rule pattern
- Fix 2: `concept_scorer.py` → when splitting comma lists, each item
  should be checked for order-sensitive contradictions separately
- Files: `negation_checker.py`, `concept_scorer.py`

### Q5 — Electrolyte wrong definition, score slightly high (0.5/2)
- Student: "Electrolyte is any liquid that has water"
- Issue: No contradiction caught, DeBERTa gives 0.48
- Root cause: Answer is wrong but not contradictory — just vague/incomplete
- Fix: Concept coverage = 0 with dynamic weights should push score lower.
  May need to lower the `w_deberta` floor when both concept=0 and DeBERTa < 0.5
- File: `normalizer.py`

---

## Architectural Issues (Do Before Production)

### 1. Hardcoded relational rules are brittle
- Location: `negation_checker.py` → `_RELATIONAL_ANTONYMS` list
- Problem: Rules written for specific test questions. New subjects will
  have contradictions the rules don't cover.
- Fix: Run NLI on ALL pairs (remove negation-word fast-path restriction).
  Use threshold 0.65+ for contradiction. Remove most relational rules
  except the most universal ones (increases/decreases, high/low).
- Cost: ~200ms per question (NLI call) vs current ~5ms

### 2. Concept extractor uses simple regex splitting
- Location: `concept_scorer.py` → `extract_concepts_from_text()`
- Problem: Splitting on `.;,\n` gives inconsistent fragments.
  "Four-chambered organ" becomes one concept even though it has
  multiple sub-facts (number of chambers + it's an organ).
- Fix: Use Gemini to extract key facts from expected answer as a
  structured list. More accurate than regex splitting.
- Prompt: "Extract the key facts from this answer as a JSON list of
  short statements, one fact per item."

### 3. SBERT similarity rewards topic overlap not correctness
- Location: `sbert_scorer.py`, `normalizer.py`
- Problem: A student writing anything related to the topic gets
  SBERT score of 0.7-0.85 even if factually wrong.
- Current fix: Reduced SBERT weight to 0.10 (from 0.20)
- Better fix: Replace SBERT with a cross-encoder that reads
  expected + student together (like DeBERTa does) for similarity too.
  Or remove SBERT entirely and rely on DeBERTa + concept coverage.

### 4. DeBERTa trained on SciEntsBank + Mohler only
- Location: `deberta_scorer.py`
- Problem: Training data is science + CS. Performance on other subjects
  (history, economics, literature) is untested and likely weaker.
- Fix: Add more diverse training data. ASAP-AES dataset covers more
  subjects. Alternatively, use Gemini as a fallback for non-science subjects.

### 5. No minimum score floor for partially correct answers
- Currently a student who mentions relevant terms but gets the core
  wrong gets nearly 0 in some cases (Q4: 0.1/2 for "remove waste")
- A human teacher might give 0.5/2 for effort/relevance
- Fix: Add `min_score = 0.05 × max_marks` floor for any non-empty answer
  that has relevance > 0.4 (student at least attempted the question)

---

## Quick Wins (Small Changes, High Impact)

1. **`detector.py`** — Add formula detection independent of "calculate" keyword
   ```python
   # if both expected AND student have formula patterns → math mode
   if has_formula(expected) and has_formula(student):
       return True
   ```

2. **`normalizer.py`** — Add completeness cap
   ```python
   if total_concepts > 0 and matched_concepts / total_concepts < 0.4:
       score = min(score, 0.4 * max_marks)
   ```

3. **`negation_checker.py`** — Remove overly specific rules, keep only
   universal ones. Run NLI for all pairs unconditionally.

4. **`concept_scorer.py`** — Use Gemini to extract concepts instead of regex

---

## Files to Change

| File | Priority | Change |
|---|---|---|
| `negation_checker.py` | HIGH | Remove brittle domain rules, use NLI unconditionally |
| `detector.py` | HIGH | Formula detection without "calculate" keyword |
| `normalizer.py` | MEDIUM | Completeness cap, min score floor |
| `concept_scorer.py` | MEDIUM | Gemini-based concept extraction |
| `sbert_scorer.py` | LOW | Consider removing, rely on DeBERTa + concept only |

---

## Test Cases to Validate After Changes

Run these specific cases to ensure fixes don't overfit:

```python
# Should NOT trigger carbon/oxygen contradiction:
expected = "Red blood cells carry oxygen to tissues"
student  = "Blood transports oxygen throughout the body"

# Should NOT trigger equal/double contradiction:
expected = "The investment doubled in value"
student  = "Returns were twice the initial amount"

# Should trigger formula contradiction:
expected = "V = IR"
student  = "V = I + R"

# Should give partial credit (not 0):
expected = "Decomposers break down dead matter and recycle nutrients"
student  = "They help break down dead things"
```
