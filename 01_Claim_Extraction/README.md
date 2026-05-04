# 01 Claim Extraction

Owner: Member 1

Status: completed initial implementation.

## Purpose

This module converts raw LIAR political claims into structured claim triples:

```text
subject, relation, object
```

It also extracts named entities, dates, labels, speakers, and confidence scores.

## Main Files

- `01_claim_extraction_roBERTa+spaCy.ipynb`
- `extracted_triples_filtered.json`

## Input

- `../LIAR_dataset/train.tsv`
- `../LIAR_dataset/valid.tsv`
- `../LIAR_dataset/test.tsv`

## Output

Expected output fields:

```text
claim_id or id
raw_claim
label
speaker
subject
subject_type
relation
object
object_type
date
confidence
entities
```

## Report Sections Supported

- Theoretical Justification: NLP, RoBERTa, NER, dependency parsing
- Workflow and Methodology: preprocessing and claim extraction
- Empirical Analysis: extraction output and confidence scores

## Notes

The notebook currently contains the core Phase 1 implementation. Other members should use `extracted_triples_filtered.json` as the main handoff file.
