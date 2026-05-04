# 05 Bayesian Inference

Owner: Member 5

## Purpose

This module combines uncertain evidence into a final credibility estimate.

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

Expected fields:

```text
claim_id
probability_true
probability_false
final_verdict
decision_confidence
reasoning
```

## Report Sections Supported

- Theoretical Justification: Bayesian/probabilistic reasoning
- Workflow and Methodology: final decision model
- Empirical Analysis: final credibility results
- Conclusion: key findings and future work
