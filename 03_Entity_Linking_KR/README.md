# Notebook 3: Entity Linking and Knowledge Representation

Owner: Member 3

## Purpose

This notebook converts the extracted claim triples from Notebook 1 into a knowledge graph-compatible JSON representation. It links named entities in the `subject` and `object` fields to Wikidata IDs, keeps literal values as literals, and adds confidence and notes so the next notebook can reason over the claims more consistently.

Example:

```text
Hillary Clinton -> Wikidata Q6294
John McCain -> Wikidata Q10390
```

## Input

Primary input:

- `../01_Claim_Extraction/extracted_triples_filtered.json`

The notebook is currently written for Google Colab and uses `files.upload()`. In Colab, upload the extracted triples JSON file when prompted. The notebook looks for:

```text
/content/extracted_triples_filtered.json
```

If a different file is uploaded, the notebook uses the uploaded filename instead.

## Method

The notebook performs the following steps:

1. Loads the extracted triples into a pandas DataFrame.
2. Normalises fields from Notebook 1, including `claim_id` and `extraction_confidence`.
3. Filters values before linking so only entity-like text is sent to Wikidata.
4. Searches Wikidata using the `wbsearchentities` API.
5. Caches repeated Wikidata lookups to reduce duplicate API calls.
6. Maps selected relation labels to Wikidata property IDs when there is a reliable match.
7. Calculates a `linking_confidence` score using entity links, literal handling, property mapping, and the original extraction confidence.
8. Saves the linked records to `linked_entities.json`.

## Linking Rules

Only entity-like types are linked:

```text
PER, PERSON, ORG, LOC, GPE, MISC
```

Literal values are not linked to Wikidata entities. This includes dates, times, numbers, percentages, money, quantities, ordinals, and similar numeric values.

Very vague or pronoun-like values such as `it`, `we`, `they`, `you`, `he`, and `she` are skipped to reduce false matches.

## Relation Mapping

The notebook includes a small relation-to-property map for relations that can be represented reliably in Wikidata, for example:

```text
founded_in / founded -> P571
born_in / place_of_birth -> P19
died_in / place_of_death -> P20
member_of -> P463
citizen_of -> P27
country -> P17
educated_at -> P69
spouse -> P26
population -> P1082
owned_by -> P127
headquarters -> P159
```

General claim verbs such as `say`, `claim`, `agree`, `support`, and `oppose` are intentionally not mapped to Wikidata properties because they are too broad for reliable KG reasoning in this dataset.

## Output

Generated output:

- `linked_entities.json`

Each linked record contains:

```text
claim_id
raw_claim
label
speaker
subject
subject_type
subject_kg_id
subject_kg_label
subject_kg_description
relation
property_id
object
object_type
object_kg_id
object_kg_label
object_kg_description
date
extraction_confidence
linking_confidence
linking_notes
```

Example output:

```json
{
  "claim_id": "claim-00003",
  "subject": "Hillary Clinton",
  "subject_type": "PER",
  "subject_kg_id": "Q6294",
  "subject_kg_label": "Hillary Clinton",
  "relation": "agree",
  "property_id": null,
  "object": "John McCain",
  "object_type": "PER",
  "object_kg_id": "Q10390",
  "object_kg_label": "John McCain",
  "linking_confidence": 0.85,
  "linking_notes": "Subject linked to Wikidata. Object linked to Wikidata. No reliable Wikidata property mapping for relation."
}
```

## Current Results

The current `linked_entities.json` file contains 500 processed claim triples.

Summary:

```text
Subjects linked to Wikidata: 207 / 500
Objects linked to Wikidata:   69 / 500
Both subject and object linked: 40 / 500
Mapped Wikidata properties:    0 / 500
Average linking confidence:    0.377
```

The low property-mapping count is expected for the current LIAR-derived extraction output because many extracted relations are generic verbs such as `say`, `do`, `be`, and `agree`. The notebook therefore prioritises reliable entity grounding over forcing weak property matches.

## Dependencies

The notebook uses:

```text
pandas
requests
tqdm
google.colab.files
```

These are covered by the project `requirements.txt`, except `google.colab`, which is provided automatically in Google Colab.

## Role in the Pipeline

This module receives extracted claims from Notebook 1 and produces linked records for Notebook 4 knowledge graph reasoning. The output supports downstream reasoning by preserving both the original claim text and the KG-compatible identifiers where reliable links were found.

## Limitations

- Wikidata search uses the top returned result, so ambiguous names may still be linked incorrectly.
- Some extracted subjects and objects are vague phrases rather than clean named entities.
- The relation extraction output often contains broad verbs that do not map cleanly to Wikidata properties.
- API rate limits are handled with sleeps and retry behaviour, so full runs can take time.
- Literal values are preserved but not normalised into Wikidata-compatible value formats.

## Report Sections Supported

- Theoretical Justification: knowledge representation and entity grounding
- Workflow and Methodology: filtering, Wikidata lookup, caching, and confidence scoring
- Empirical Analysis: linking coverage, property-mapping limitations, and error sources
