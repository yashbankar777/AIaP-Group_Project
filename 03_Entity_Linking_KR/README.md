# 03 Entity Linking and Knowledge Representation

Owner: Member 3

## Purpose

This module maps extracted claim text into structured knowledge graph-compatible representations.

Example:

```text
Barack Obama -> Wikidata Q76
United States -> Wikidata Q30
```

## Tasks

- Load extracted triples from Member 1.
- Link subject and object strings to Wikidata or DBpedia entities.
- Define the structured claim schema.
- Handle ambiguous or missing entity matches.
- Save linked output for KG reasoning.

## Input

Preferred input:

- `../01_Claim_Extraction/extracted_triples_filtered.json`

Fallback input:

- `../shared/sample_triples.json`

## Expected Output

- `linked_entities.json`

Expected fields:

```text
claim_id
raw_claim
subject
subject_kg_id
object
object_kg_id
relation
property_id
linking_confidence
linking_notes
```

## Report Sections Supported

- Theoretical Justification: structural knowledge representation
- Workflow and Methodology: entity linking
- Empirical Analysis: linking success rate and limitations
