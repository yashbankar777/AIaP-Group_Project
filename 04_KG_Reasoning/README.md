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

Expected fields:

```text
claim_id
kg_status
kg_confidence
evidence
reasoning_rule
source
```

## Report Sections Supported

- Theoretical Justification: logic and symbolic reasoning
- Workflow and Methodology: KG reasoning rules
- Empirical Analysis: supported/contradicted/unknown counts
