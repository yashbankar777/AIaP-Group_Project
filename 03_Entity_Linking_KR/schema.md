# Claim Representation Schema

This module should convert extracted triples into a knowledge graph-compatible form.

## Input Claim Triple

```json
{
  "claim_id": "sample-001",
  "raw_claim": "OpenAI was founded in 2020.",
  "subject": "OpenAI",
  "relation": "founded_in",
  "object": "2020",
  "extraction_confidence": 0.89
}
```

## Linked Claim

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

`property_id` can be `null` where no suitable KG property is found.
