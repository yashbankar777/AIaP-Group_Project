# Responsible AI Analysis

Use this file to draft the critical reflection material for the final report.

## Dataset and Bias Risks

- LIAR contains political claims, so the dataset may reflect political, media, and speaker-selection bias.
- Labels are simplified truth categories and may not capture nuance.
- Speaker history can encode historical bias if used without care.

## False Positive and False Negative Risks

- False positive: a true claim is marked as misinformation.
- False negative: a false claim is marked as credible.
- Both can harm public trust, especially in political settings.

## LLM and GenAI Risks

- LLMs may hallucinate evidence.
- LLMs can sound confident even when unsupported.
- Retrieval-augmented generation could help, but retrieved sources must be checked.

## Scalability Constraints

- RoBERTa/spaCy extraction can be slower on large datasets.
- Wikidata/DBpedia querying may hit API limits or return incomplete evidence.
- Bayesian assumptions may need calibration with more data.

## Alternative Methods

- Simple text classifier baseline.
- LLM-based verifier with retrieval.
- Fine-tuned transformer classifier.
- Human-in-the-loop fact-checking workflow.
