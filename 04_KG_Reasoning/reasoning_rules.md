# KG Reasoning Rules

Suggested output statuses:

- `supported`: KG evidence agrees with the extracted claim.
- `contradicted`: KG evidence conflicts with the extracted claim.
- `unknown`: no reliable KG evidence is found.

## Example Rule

```text
IF claim relation = founded_in
AND KG inception year exists
AND claim object year != KG inception year
THEN kg_status = contradicted
```

## Evidence Requirements

Each result should include:

- the claim ID
- the status
- a confidence score
- a short evidence sentence
- the KG source or fallback source
