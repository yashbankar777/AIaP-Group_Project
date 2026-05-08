# 04 Knowledge Graph Reasoning

Owner: Member 4

## Purpose

This module checks whether linked claims are supported, contradicted, or unknown using knowledge graph evidence.

## Tasks

- Load linked entities from Member 3.
- Query or simulate trusted KG facts.
- Compare claim values against KG facts.
- Return support, contradiction, or unknown status.
- Save reasoning evidence for Bayesian inference.

## Input

Preferred input:

- `../03_Entity_Linking_KR/linked_entities.json`

Fallback input:

- `../shared/sample_linked_entities.json`

## Expected Output

- `kg_results.json`
- `kg_reasoning_summary.json`

Expected fields:

```text
claim_id
kg_status
kg_confidence
evidence
reasoning_rule
source
```

Additional context fields such as `raw_claim`, linked subject/object IDs, and
the original relation are preserved for traceability and downstream Bayesian
inference.

## How to Run

From the repository root:

```bash
python3 04_KG_Reasoning/run_kg_reasoning.py
```

The notebook `kg_reasoning.ipynb` uses the same runner and explains the
reasoning rules step by step.

## Method Notes

- The module is intentionally conservative. It returns `unknown` unless the
  linked entities and relation are strong enough for a simple rule.
- Description-based class rules can support or contradict narrow claims such as
  `Austin is a city`.
- Generic relations such as `say`, `be`, and `have` are not treated as factual
  KG properties without additional structure.
- Low-confidence entity links are passed through with low-confidence `unknown`
  reasoning instead of being silently removed.

## Report Sections Supported

- Theoretical Justification: logic and symbolic reasoning
- Workflow and Methodology: KG reasoning rules
- Empirical Analysis: supported/contradicted/unknown counts
