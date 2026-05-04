# Shared Data Schemas

Use these schemas so each member's work can connect cleanly.

## Extracted Triple

Produced by Member 1.

```json
{
  "claim_id": "sample-001",
  "raw_claim": "OpenAI was founded in 2020.",
  "label": "false",
  "speaker": "sample-speaker",
  "subject": "OpenAI",
  "subject_type": "ORG",
  "relation": "founded_in",
  "object": "2020",
  "object_type": "DATE",
  "date": "2020",
  "extraction_confidence": 0.89
}
```

## Linked Entity Record

Produced by Member 3.

```json
{
  "claim_id": "sample-001",
  "subject": "OpenAI",
  "subject_kg_id": "Q21708200",
  "relation": "founded_in",
  "property_id": "P571",
  "object": "2020",
  "object_kg_id": null,
  "linking_confidence": 0.86
}
```

## KG Reasoning Record

Produced by Member 4.

```json
{
  "claim_id": "sample-001",
  "kg_status": "contradicted",
  "kg_confidence": 0.88,
  "evidence": "Wikidata inception year for OpenAI is 2015.",
  "reasoning_rule": "founded_in_year_mismatch"
}
```

## Final Verdict Record

Produced by Member 5.

```json
{
  "claim_id": "sample-001",
  "probability_true": 0.09,
  "probability_false": 0.91,
  "final_verdict": "likely false",
  "decision_confidence": 0.82,
  "reasoning": "High extraction confidence and KG contradiction evidence."
}
```
