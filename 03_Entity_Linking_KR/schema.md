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
  "raw_claim": "OpenAI was founded in 2020.",
  "label": "false",
  "speaker": "sample-speaker",
  "subject": "OpenAI",
  "subject_type": "ORG",
  "subject_kg_id": "Q21708200",
  "subject_kg_label": "OpenAI",
  "subject_kg_description": "American artificial intelligence research organization",
  "relation": "founded_in",
  "property_id": "P571",
  "property_label": "inception",
  "object": "2020",
  "object_type": "DATE",
  "object_kg_id": null,
  "date": "2020",
  "extraction_confidence": 0.89,
  "linking_confidence": 0.86,
  "linking_notes": "Subject linked to Wikidata. Object treated as literal value. Relation mapped to Wikidata property."
}
```

`property_id` can be `null` where no suitable KG property is found.

## Quality Notes

- Entity IDs should be treated as probabilistic links, not guaranteed truth.
- Low-confidence records should be passed downstream with caution rather than
  removed silently.
- Generic relations from claim extraction may not map cleanly to Wikidata
  properties. In those cases `property_id` remains `null`.
