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
- `entity_linking_summary.json`

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

Additional metadata fields such as `subject_kg_label`, `object_kg_label`,
`property_label`, and link source are included to support error analysis and
the final report.

## How to Run

From the repository root:

```bash
python3 03_Entity_Linking_KR/run_entity_linking.py
```

For a quick offline smoke test that only uses the manual disambiguation map:

```bash
python3 03_Entity_Linking_KR/run_entity_linking.py --offline --max-records 20
```

The notebook `entity_linking.ipynb` uses the same runner and documents the
workflow step by step.

## Method Notes

- The module links only entity-like values: people, organisations, locations,
  geopolitical entities, and miscellaneous named entities.
- Literal objects such as dates, counts, percentages, and money values are kept
  as literal values instead of being forced into entity IDs.
- Common ambiguous political names are expanded before search, for example
  `Obama -> Barack Obama`, `McCain -> John McCain`, and `ISIS -> Islamic State`.
- Obvious bad Wikidata matches such as family-name pages, given-name pages,
  disambiguation pages, and unrelated academic journals are rejected.
- `property_id` is mapped only when the relation or claim pattern gives a
  defensible Wikidata property. Generic relations such as `say`, `be`, and
  `have` are left unmapped unless the surrounding claim pattern is specific
  enough.

## Report Sections Supported

- Theoretical Justification: structural knowledge representation
- Workflow and Methodology: entity linking
- Empirical Analysis: linking success rate and limitations
