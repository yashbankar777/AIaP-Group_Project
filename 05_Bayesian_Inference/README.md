# 05 Bayesian Inference

Owner: Member 5

## Purpose

This module combines uncertain evidence into a final credibility estimate.
It receives the symbolic KG result from Notebook 4 and converts it into
posterior probabilities and a final verdict.

## Tasks

- Load KG reasoning outputs.
- Combine extraction confidence, KG status, KG confidence, and optional LIAR metadata.
- Estimate `P(true)` and `P(false)`.
- Produce a final verdict.
- Explain the Bayesian assumptions clearly.

## Input

Preferred input:

- `../04_KG_Reasoning/kg_results.json`

Fallback input:

- `../shared/sample_kg_results.json`

## Expected Output

- `final_verdicts.json`
- `final_verdict_summary.json`
- `../report_assets/tables/bayesian_verdict_distribution.csv`

Expected fields:

```text
claim_id
probability_true
probability_false
final_verdict
decision_confidence
reasoning
```

Extra context fields such as `raw_claim`, `kg_status`, `kg_confidence`,
`extraction_confidence`, `linking_confidence`, and `reference_label` are kept
for traceability and report evaluation. The reference label is not used to
calculate the probability.

## How to Run

From the repository root:

```bash
python3 05_Bayesian_Inference/run_bayesian_inference.py
```

The notebook `bayesian_inference.ipynb` uses the same runner and explains the
Bayesian assumptions step by step.

## Method Notes

- The prior starts at `P(true)=0.50`.
- If LIAR speaker-history counts are available, they only make a small
  adjustment to the prior to avoid over-penalising speakers.
- KG support increases the true odds; KG contradiction decreases the true odds.
- Extraction and entity-linking confidence scale how strongly KG evidence is
  trusted.
- Unknown KG evidence adds no directional truth signal, so the model keeps the
  verdict uncertain instead of forcing a binary answer.

## Report Sections Supported

- Theoretical Justification: Bayesian/probabilistic reasoning
- Workflow and Methodology: final decision model
- Empirical Analysis: final credibility results
- Conclusion: key findings and future work
