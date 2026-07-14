# Morning Brief Evaluation Rubric

## Purpose

This rubric defines how to evaluate the quality of a TPM Copilot morning brief regardless of whether it was produced by deterministic rules, an AI model, or a human author.

Evaluation combines:

- Automated checks for objective requirements.
- Human review for meaning, usefulness, and judgment.
- Comparison with source data and human-approved golden examples.

## Critical Safety Gates

A brief fails evaluation regardless of its numerical score if it:

- Includes a substantive claim unsupported by the available source data.
- Uses information that was not authorized for the configured processing path.
- Omits provenance for a substantive claim.
- Presents inference as a confirmed fact.
- Silently changes the meaning of a source.
- Invents an owner, date, decision, commitment, risk, or status.
- Recommends a consequential external action without required human approval.

## Scoring Scale

Each quality dimension receives a score from 0 through 2:

| Score | Meaning |
|---|---|
| 0 | Requirement is missing, materially incorrect, or unsafe |
| 1 | Requirement is partially met but needs improvement |
| 2 | Requirement is fully met for the available evidence |

## Quality Dimensions

| Dimension | 0 — Does not meet | 1 — Partially meets | 2 — Fully meets |
|---|---|---|---|
| Faithfulness | Contains unsupported or distorted claims | Mostly grounded, with minor ambiguity | Every substantive claim is supported and accurately represented |
| Prioritization | Important items are missing or poorly ordered | Most important items are present, but ordering is debatable | The highest-impact and most urgent items receive appropriate prominence |
| Actionability | Provides no useful next step | Some actions are vague or unsupported | Actions are specific, proportionate, and supported by the sources |
| Concision and clarity | Difficult to scan, repetitive, or confusing | Generally understandable with avoidable verbosity | Clear, concise, and immediately skimmable |
| Citation quality | Citations are missing or do not support claims | Citations exist but are incomplete or imprecise | Every substantive item has a direct, accurate source reference |
| Uncertainty handling | Uncertainty is hidden or overstated as fact | Some uncertainty is disclosed | Missing, conflicting, or inferred information is clearly distinguished |
| BLUF 3×3 compliance | Required structure is absent | Structure is present with material inconsistencies | BLUF and all three three-bullet sections follow the defined contract |

## Score Interpretation

The maximum score is 14.

| Total score | Interpretation |
|---|---|
| 12–14 | Ready for normal human review |
| 9–11 | Useful draft that requires revision |
| 0–8 | Does not meet the quality threshold |

Critical safety gates override the numerical score. A brief that fails a safety gate is not acceptable even if its total score is otherwise high.

## Automated Evaluation Checks

Automated tests should verify objective requirements where possible:

- The BLUF heading is present.
- All three required sections are present.
- Each section contains exactly three bullets.
- Every substantive bullet includes a valid source reference.
- Every cited source identifier exists in the supplied dataset.
- No unauthorized source item enters an AI-assisted processing path.
- Required schema and governance fields are valid.
- Priority scores are reproducible.
- Items are ordered consistently with the configured prioritization method.
- Missing evidence is disclosed rather than replaced with invented content.

Automated checks should not claim to measure subjective communication quality that they cannot reliably determine.

## Human Evaluation Checks

A human evaluator should determine whether:

- The BLUF accurately captures the overall program condition.
- The most important items received appropriate prominence.
- Suggested actions are useful and proportionate.
- Wording preserves the meaning and level of certainty in each source.
- The brief is concise enough for rapid review.
- Conflicting or incomplete information is visible.
- The brief would help a TPM decide what to do next.

## Use of Golden Examples

A golden example represents a human-approved quality target for a known dataset.

It should be used to compare:

- Selected facts
- Relative prioritization
- Required citations
- Expected actions
- Treatment of uncertainty
- Overall communication quality

A generated brief does not need to match the golden example word for word. Semantically equivalent wording may be acceptable when it remains faithful, concise, and actionable.

## Evaluation Procedure

1. Preserve the exact source dataset and schema version.
2. Generate a fresh brief using the analysis method under evaluation.
3. Run all automated checks.
4. Review every substantive claim against its cited source.
5. Apply the critical safety gates.
6. Score all seven quality dimensions.
7. Compare the result with the golden example.
8. Record defects, false positives, false negatives, and questionable prioritization.
9. Decide whether the brief passes, requires revision, or fails.
10. Preserve the evaluation result for regression comparison.

## Evaluation Record Template

| Field | Value |
|---|---|
| Evaluation date | |
| Evaluator | |
| Dataset version | |
| Analysis method | |
| Critical safety gates | Pass / Fail |
| Automated tests | Pass / Fail |
| Faithfulness | 0 / 1 / 2 |
| Prioritization | 0 / 1 / 2 |
| Actionability | 0 / 1 / 2 |
| Concision and clarity | 0 / 1 / 2 |
| Citation quality | 0 / 1 / 2 |
| Uncertainty handling | 0 / 1 / 2 |
| BLUF 3×3 compliance | 0 / 1 / 2 |
| Total score | / 14 |
| Decision | Pass / Revise / Fail |
| Findings | |
