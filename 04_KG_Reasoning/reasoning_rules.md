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

## Implemented Rules

### 1. Property Availability Rule

```text
IF relation maps to a Wikidata property
AND subject KG ID is available
AND object KG ID or literal comparison value is not available
THEN kg_status = unknown
```

This prevents the system from claiming support or contradiction when the KG
property is known but the object cannot be compared.

### 2. Description Class Match Rule

```text
IF relation is a copular relation such as "be"
AND subject has a Wikidata entity description
AND object is a simple class phrase such as "a city"
AND the description contains a matching class signal
THEN kg_status = supported
```

Example: `Austin is a city` can be supported if the Wikidata description for
Austin identifies it as a city, seat, or capital.

### 3. Description Class Mismatch Rule

```text
IF relation is a copular relation
AND object is a simple class phrase
AND the subject description clearly points to a conflicting class
THEN kg_status = contradicted
```

This rule is applied cautiously and avoids conditional or hypothetical claims.

### 4. Speech Relation Rule

```text
IF relation is "say", "said", "claim", or similar
THEN kg_status = unknown
```

Speech/reporting relations do not directly represent factual KG properties.

### 5. Low-Confidence Link Rule

```text
IF entity-linking confidence is low
THEN kg_status = unknown
```

The system keeps weak records for transparency but does not overclaim evidence.

## Evidence Requirements

Each result should include:

- the claim ID
- the status
- a confidence score
- a short evidence sentence
- the KG source or fallback source
