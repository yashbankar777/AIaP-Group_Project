from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from tqdm import tqdm


WIKIDATA_API = "https://www.wikidata.org/w/api.php"
HEADERS = {"User-Agent": "AIaP-Entity-Linking-Student-Project/1.0"}

LINKABLE_TYPES = {"PER", "PERSON", "ORG", "LOC", "GPE", "MISC"}
LITERAL_TYPES = {"DATE", "TIME", "CARDINAL", "PERCENT", "MONEY", "QUANTITY", "ORDINAL", "NUMBER"}

BAD_ENTITY_VALUES = {
    "i",
    "it",
    "he",
    "she",
    "they",
    "them",
    "we",
    "us",
    "you",
    "one",
    "some",
    "most",
    "much",
    "more",
    "less",
    "this",
    "that",
    "the president",
    "the state",
    "the country",
    "the economy",
    "d",
}

VAGUE_MISC_VALUES = {
    "american",
    "americans",
    "democratic",
    "democrats",
    "republican",
    "republicans",
    "latino",
    "hispanic",
    "black",
    "white",
    "federal",
}

BAD_DESCRIPTION_TERMS = {
    "family name",
    "given name",
    "surname",
    "human name",
    "wikimedia disambiguation page",
    "academic journal",
    "scientific journal",
    "television station",
    "video game",
}

PERSON_DESCRIPTION_TERMS = {
    "politician",
    "president",
    "senator",
    "governor",
    "representative",
    "secretary",
    "mayor",
    "diplomat",
    "lawyer",
    "businessman",
    "activist",
    "journalist",
    "judge",
    "justice",
}

ORG_DESCRIPTION_TERMS = {
    "organization",
    "organisation",
    "company",
    "corporation",
    "party",
    "team",
    "agency",
    "institution",
    "government",
    "campaign",
    "association",
    "university",
}

LOC_DESCRIPTION_TERMS = {
    "country",
    "state",
    "city",
    "county",
    "territory",
    "region",
    "capital",
    "province",
    "district",
}

MANUAL_ALIASES = {
    "obama": "Barack Obama",
    "obamas": "Barack Obama",
    "president obama": "Barack Obama",
    "barack hussein obama": "Barack Obama",
    "mccain": "John McCain",
    "romney": "Mitt Romney",
    "trump": "Donald Trump",
    "donald trump": "Donald Trump",
    "clinton": "Hillary Clinton",
    "hillary": "Hillary Clinton",
    "bush": "George W. Bush",
    "george bush": "George W. Bush",
    "george w bush": "George W. Bush",
    "george w. bush": "George W. Bush",
    "george w.) bush": "George W. Bush",
    "reagan": "Ronald Reagan",
    "palin": "Sarah Palin",
    "kagan": "Elena Kagan",
    "warren": "Elizabeth Warren",
    "bernie": "Bernie Sanders",
    "sanders": "Bernie Sanders",
    "ryan": "Paul Ryan",
    "rush limbaugh": "Rush Limbaugh",
    "isis": "Islamic State",
    "islamic state": "Islamic State",
    "islamic state of iraq and syria": "Islamic State",
    "obamacare": "Patient Protection and Affordable Care Act",
    "barack obamas": "Barack Obama",
    "affordable care act": "Patient Protection and Affordable Care Act",
    "u.s.": "United States",
    "u.s": "United States",
    "us": "United States",
    "usa": "United States",
    "american": "United States",
    "americans": "Americans",
    "north carolinas": "North Carolina",
    "oregons": "Oregon",
}

MANUAL_ENTITIES = {
    "Barack Obama": {
        "kg_id": "Q76",
        "label": "Barack Obama",
        "description": "president of the United States from 2009 to 2017",
        "source": "manual_alias",
        "match_score": 0.98,
    },
    "John McCain": {
        "kg_id": "Q10390",
        "label": "John McCain",
        "description": "American politician",
        "source": "manual_alias",
        "match_score": 0.98,
    },
    "Mitt Romney": {
        "kg_id": "Q4496",
        "label": "Mitt Romney",
        "description": "American politician and businessman",
        "source": "manual_alias",
        "match_score": 0.98,
    },
    "Donald Trump": {
        "kg_id": "Q22686",
        "label": "Donald Trump",
        "description": "president of the United States",
        "source": "manual_alias",
        "match_score": 0.98,
    },
    "Hillary Clinton": {
        "kg_id": "Q6294",
        "label": "Hillary Clinton",
        "description": "American politician and diplomat",
        "source": "manual_alias",
        "match_score": 0.98,
    },
    "George W. Bush": {
        "kg_id": "Q207",
        "label": "George W. Bush",
        "description": "president of the United States from 2001 to 2009",
        "source": "manual_alias",
        "match_score": 0.98,
    },
    "Ronald Reagan": {
        "kg_id": "Q9960",
        "label": "Ronald Reagan",
        "description": "president of the United States from 1981 to 1989",
        "source": "manual_alias",
        "match_score": 0.98,
    },
    "Sarah Palin": {
        "kg_id": "Q43148",
        "label": "Sarah Palin",
        "description": "American politician",
        "source": "manual_alias",
        "match_score": 0.98,
    },
    "Elena Kagan": {
        "kg_id": "Q172035",
        "label": "Elena Kagan",
        "description": "associate justice of the Supreme Court of the United States",
        "source": "manual_alias",
        "match_score": 0.98,
    },
    "Elizabeth Warren": {
        "kg_id": "Q434706",
        "label": "Elizabeth Warren",
        "description": "American politician and senator",
        "source": "manual_alias",
        "match_score": 0.98,
    },
    "Bernie Sanders": {
        "kg_id": "Q359442",
        "label": "Bernie Sanders",
        "description": "American politician and senator",
        "source": "manual_alias",
        "match_score": 0.98,
    },
    "Paul Ryan": {
        "kg_id": "Q203966",
        "label": "Paul Ryan",
        "description": "American politician",
        "source": "manual_alias",
        "match_score": 0.98,
    },
    "Rush Limbaugh": {
        "kg_id": "Q319072",
        "label": "Rush Limbaugh",
        "description": "American political commentator",
        "source": "manual_alias",
        "match_score": 0.98,
    },
    "Islamic State": {
        "kg_id": "Q2429253",
        "label": "Islamic State",
        "description": "jihadist militant organization",
        "source": "manual_alias",
        "match_score": 0.98,
    },
    "Patient Protection and Affordable Care Act": {
        "kg_id": "Q1414593",
        "label": "Patient Protection and Affordable Care Act",
        "description": "United States federal statute",
        "source": "manual_alias",
        "match_score": 0.98,
    },
    "United States": {
        "kg_id": "Q30",
        "label": "United States",
        "description": "country in North America",
        "source": "manual_alias",
        "match_score": 0.98,
    },
    "North Carolina": {
        "kg_id": "Q1454",
        "label": "North Carolina",
        "description": "state of the United States",
        "source": "manual_alias",
        "match_score": 0.98,
    },
    "Oregon": {
        "kg_id": "Q824",
        "label": "Oregon",
        "description": "state of the United States",
        "source": "manual_alias",
        "match_score": 0.98,
    },
}

PROPERTY_MAP = {
    "founded_in": ("P571", "inception"),
    "founded": ("P571", "inception"),
    "was_founded": ("P571", "inception"),
    "born_in": ("P19", "place of birth"),
    "place_of_birth": ("P19", "place of birth"),
    "died_in": ("P20", "place of death"),
    "place_of_death": ("P20", "place of death"),
    "position_held": ("P39", "position held"),
    "president_of": ("P39", "position held"),
    "governor_of": ("P39", "position held"),
    "senator_of": ("P39", "position held"),
    "located_in": ("P131", "located in administrative territorial entity"),
    "part_of": ("P361", "part of"),
    "member_of": ("P463", "member of"),
    "belong": ("P463", "member of"),
    "citizen_of": ("P27", "country of citizenship"),
    "country": ("P17", "country"),
    "educated_at": ("P69", "educated at"),
    "spouse": ("P26", "spouse"),
    "capital_of": ("P1376", "capital of"),
    "population": ("P1082", "population"),
    "owned_by": ("P127", "owned by"),
    "headquarters": ("P159", "headquarters location"),
    "leader": ("P6", "head of government"),
}

POSITION_TERMS = {
    "president",
    "governor",
    "senator",
    "representative",
    "secretary",
    "mayor",
    "congressman",
    "congresswoman",
}


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "LIAR_dataset").exists() and (candidate / "01_Claim_Extraction").exists():
            return candidate
    raise FileNotFoundError("Could not find the project root.")


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"none", "nan", "null", "unknown"}:
        return None
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalized_key(value: Any) -> str:
    text = clean_text(value) or ""
    text = text.lower()
    text = text.replace("'", "")
    text = text.replace("`", "")
    text = re.sub(r"[\(\)\[\]\",]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .")


def normalize_relation(relation: Any) -> str | None:
    text = clean_text(relation)
    if text is None:
        return None
    text = text.lower().strip().replace("-", "_").replace(" ", "_")
    return re.sub(r"_+", "_", text)


def is_literal(value: Any, entity_type: Any = None) -> bool:
    text = clean_text(value)
    if text is None:
        return True
    if clean_text(entity_type) in LITERAL_TYPES:
        return True
    numberish = text.replace(",", "").replace(".", "").replace("%", "").replace("$", "").strip()
    if numberish.isdigit():
        return True
    if re.fullmatch(r"\d{4}", text):
        return True
    return False


def should_link_entity(value: Any, entity_type: Any) -> bool:
    text = clean_text(value)
    if text is None:
        return False
    entity_type_clean = clean_text(entity_type)
    if entity_type_clean not in LINKABLE_TYPES:
        return False
    key = normalized_key(text)
    if key in BAD_ENTITY_VALUES:
        return False
    if len(key) <= 1:
        return False
    if key.startswith(("the ", "a ", "an ")) and len(key.split()) > 3:
        return False
    if entity_type_clean == "MISC" and len(key) <= 2:
        return False
    if entity_type_clean == "MISC" and key in VAGUE_MISC_VALUES:
        return False
    return True


def parse_extracted_entities(value: Any) -> list[dict[str, Any]]:
    text = clean_text(value)
    if text is None:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def candidate_queries(value: Any, row: pd.Series) -> list[str]:
    text = clean_text(value)
    if text is None:
        return []

    key = normalized_key(text)
    queries: list[str] = []

    if key in MANUAL_ALIASES:
        queries.append(MANUAL_ALIASES[key])

    # Use the full extracted NER phrase when the triple only kept a surname.
    for entity in parse_extracted_entities(row.get("entities")):
        word = clean_text(entity.get("word"))
        entity_type = clean_text(entity.get("type"))
        if not word or entity_type not in LINKABLE_TYPES:
            continue
        word_key = normalized_key(word)
        if key and key in word_key.split() and len(word_key.split()) > 1:
            queries.append(word)

    title_removed = re.sub(
        r"^(president|sen\.|senator|gov\.|governor|rep\.|representative|secretary|justice)\s+",
        "",
        text,
        flags=re.IGNORECASE,
    )
    title_key = normalized_key(title_removed)
    if title_key in MANUAL_ALIASES:
        queries.append(MANUAL_ALIASES[title_key])

    possessive_removed = re.sub(r"'?s$", "", text).strip()
    if normalized_key(possessive_removed) in MANUAL_ALIASES:
        queries.append(MANUAL_ALIASES[normalized_key(possessive_removed)])

    punctuation_fixed = text.replace(".)", ".").replace("  ", " ").strip()
    if punctuation_fixed != text:
        queries.append(punctuation_fixed)

    queries.append(text)

    seen = set()
    unique = []
    for query in queries:
        query = clean_text(query)
        if query and query.lower() not in seen:
            seen.add(query.lower())
            unique.append(query)
    return unique


def description_is_bad(description: str | None) -> bool:
    desc = (description or "").lower()
    return any(term in desc for term in BAD_DESCRIPTION_TERMS)


def result_score(result: dict[str, Any], query: str, entity_type: str | None) -> float:
    label = (result.get("label") or "").lower()
    desc = (result.get("description") or "").lower()
    query_key = normalized_key(query)
    label_key = normalized_key(label)
    score = 0.5

    if label_key == query_key:
        score += 0.25
    elif query_key and query_key in label_key:
        score += 0.15
    elif label_key and label_key in query_key:
        score += 0.1

    if description_is_bad(desc):
        score -= 0.6

    if entity_type in {"PER", "PERSON"}:
        if any(term in desc for term in PERSON_DESCRIPTION_TERMS):
            score += 0.2
        else:
            score -= 0.15
        if any(term in desc for term in LOC_DESCRIPTION_TERMS):
            score -= 0.25
    elif entity_type == "ORG":
        if any(term in desc for term in ORG_DESCRIPTION_TERMS):
            score += 0.2
    elif entity_type in {"LOC", "GPE"}:
        if any(term in desc for term in LOC_DESCRIPTION_TERMS):
            score += 0.2

    return round(max(0.0, min(score, 0.99)), 3)


def wikidata_search(query: str, limit: int, timeout: int, sleep_seconds: float) -> list[dict[str, Any]]:
    time.sleep(sleep_seconds)
    response = requests.get(
        WIKIDATA_API,
        params={
            "action": "wbsearchentities",
            "format": "json",
            "language": "en",
            "search": query,
            "limit": limit,
        },
        headers=HEADERS,
        timeout=timeout,
    )
    if response.status_code == 429:
        time.sleep(5)
        response = requests.get(
            WIKIDATA_API,
            params={
                "action": "wbsearchentities",
                "format": "json",
                "language": "en",
                "search": query,
                "limit": limit,
            },
            headers=HEADERS,
            timeout=timeout,
        )
    response.raise_for_status()
    return response.json().get("search", [])


def manual_entity_for_query(query: str, original_value: Any) -> dict[str, Any] | None:
    query_key = normalized_key(query)
    original_key = normalized_key(original_value)
    canonical = MANUAL_ALIASES.get(original_key) or MANUAL_ALIASES.get(query_key)
    if canonical and canonical in MANUAL_ENTITIES:
        return dict(MANUAL_ENTITIES[canonical])
    if query in MANUAL_ENTITIES:
        return dict(MANUAL_ENTITIES[query])
    return None


def build_prior_links(output_path: Path) -> dict[str, dict[str, Any]]:
    """Reuse safe links from a previous output to avoid unnecessary API calls."""
    if not output_path.exists():
        return {}
    try:
        records = json.loads(output_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}

    prior: dict[str, dict[str, Any]] = {}
    for record in records:
        for role in ["subject", "object"]:
            value = clean_text(record.get(role))
            entity_type = clean_text(record.get(f"{role}_type"))
            kg_id = record.get(f"{role}_kg_id")
            label = record.get(f"{role}_kg_label")
            description = record.get(f"{role}_kg_description")
            if not value or not kg_id or not label:
                continue
            link = {
                "kg_id": kg_id,
                "label": label,
                "description": description,
                "source": "prior_output",
                "query": value,
            }
            score = result_score(link, value, entity_type)
            if score >= 0.65:
                link["match_score"] = score
                prior[f"{entity_type}|{normalized_key(value)}"] = link
    return prior


def search_entity(
    value: Any,
    entity_type: Any,
    row: pd.Series,
    cache: dict[str, Any],
    *,
    prior_links: dict[str, dict[str, Any]] | None = None,
    offline: bool = False,
    limit: int = 5,
    timeout: int = 15,
    sleep_seconds: float = 0.05,
) -> dict[str, Any] | None:
    if not should_link_entity(value, entity_type):
        return None

    entity_type_clean = clean_text(entity_type)
    queries = candidate_queries(value, row)

    for query in queries:
        manual = manual_entity_for_query(query, value)
        if manual:
            manual["query"] = query
            return manual

    prior_key = f"{entity_type_clean}|{normalized_key(value)}"
    if prior_links and prior_key in prior_links:
        return dict(prior_links[prior_key])

    if offline:
        return None

    best: dict[str, Any] | None = None
    for query in queries:
        cache_key = f"{entity_type_clean}|{query.lower()}"
        if cache_key in cache:
            results = cache[cache_key]
        else:
            try:
                results = wikidata_search(query, limit=limit, timeout=timeout, sleep_seconds=sleep_seconds)
            except requests.RequestException:
                results = []
            cache[cache_key] = results

        for candidate in results:
            link = {
                "kg_id": candidate.get("id"),
                "label": candidate.get("label"),
                "description": candidate.get("description"),
                "source": "wikidata_search",
                "query": query,
            }
            score = result_score(link, query, entity_type_clean)
            if score < 0.45:
                continue
            link["match_score"] = score
            if best is None or score > best["match_score"]:
                best = link

    return best


def infer_property(row: pd.Series) -> tuple[str | None, str | None, str]:
    relation = normalize_relation(row.get("relation"))
    raw_claim = (clean_text(row.get("raw_claim")) or "").lower()
    obj = (clean_text(row.get("object")) or "").lower()
    object_type = clean_text(row.get("object_type"))
    subject_type = clean_text(row.get("subject_type"))

    if relation in PROPERTY_MAP:
        property_id, label = PROPERTY_MAP[relation]
        return property_id, label, "exact relation mapping"

    if relation in {"say", "says", "said", "claim", "claims", "tell", "tells", "has_say"}:
        return None, None, "speech relation is not a factual Wikidata property"

    if (
        "founded" in raw_claim
        and (object_type in {"DATE", "TIME"} or clean_text(row.get("date")) or re.search(r"\b\d{4}\b", obj))
    ):
        return "P571", "inception", "claim pattern: founded/start"

    if "born" in raw_claim and subject_type in {"PER", "PERSON"}:
        if object_type in {"DATE", "TIME"} or re.search(r"\b\d{4}\b", obj):
            return "P569", "date of birth", "claim pattern: born with date"
        if object_type in {"LOC", "GPE"}:
            return "P19", "place of birth", "claim pattern: born with place"

    if ("died" in raw_claim or "death" in raw_claim) and subject_type in {"PER", "PERSON"}:
        if object_type in {"DATE", "TIME"} or re.search(r"\b\d{4}\b", obj):
            return "P570", "date of death", "claim pattern: died with date"
        if object_type in {"LOC", "GPE"}:
            return "P20", "place of death", "claim pattern: died with place"

    object_tokens = set(re.findall(r"[a-z]+", obj))
    if subject_type in {"PER", "PERSON"} and object_tokens.intersection(POSITION_TERMS):
        return "P39", "position held", "object contains public office"

    if (
        subject_type in {"PER", "PERSON"}
        and relation in {"be", "is", "was", "were"}
        and object_tokens.intersection(POSITION_TERMS)
    ):
        return "P39", "position held", "copular public-office claim"

    if relation in {"located", "located_in", "live", "has_live", "lived"} and object_type in {"LOC", "GPE"}:
        return "P131", "located in administrative territorial entity", "location relation"

    return None, None, "no reliable Wikidata property mapping"


def calculate_linking_confidence(
    subject_link: dict[str, Any] | None,
    object_link: dict[str, Any] | None,
    object_is_literal: bool,
    property_id: str | None,
    extraction_confidence: Any,
) -> float:
    try:
        extraction_score = float(extraction_confidence)
    except (TypeError, ValueError):
        extraction_score = 0.5

    subject_score = float(subject_link.get("match_score", 0.0)) if subject_link else 0.0
    if object_is_literal:
        object_score = 0.75
    else:
        object_score = float(object_link.get("match_score", 0.0)) if object_link else 0.0
    property_score = 1.0 if property_id else 0.0

    confidence = (
        0.35 * subject_score
        + 0.2 * object_score
        + 0.2 * property_score
        + 0.25 * extraction_score
    )
    return round(max(0.0, min(confidence, 0.99)), 3)


def build_linking_notes(
    subject_link: dict[str, Any] | None,
    object_link: dict[str, Any] | None,
    object_is_literal: bool,
    property_id: str | None,
    property_reason: str,
) -> str:
    notes = []
    if subject_link:
        notes.append(f"Subject linked via {subject_link.get('source')} using query '{subject_link.get('query')}'.")
    else:
        notes.append("Subject not linked or not suitable for linking.")

    if object_is_literal:
        notes.append("Object treated as literal value.")
    elif object_link:
        notes.append(f"Object linked via {object_link.get('source')} using query '{object_link.get('query')}'.")
    else:
        notes.append("Object not linked or not suitable for linking.")

    if property_id:
        notes.append(f"Relation mapped to Wikidata property by {property_reason}.")
    else:
        notes.append("No reliable Wikidata property mapping for relation.")
    return " ".join(notes)


def normalize_input_records(records: list[dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(records)
    if "claim_id" not in df.columns:
        df["claim_id"] = [f"claim-{index + 1:05d}" for index in range(len(df))]
    if "extraction_confidence" not in df.columns and "confidence" in df.columns:
        df["extraction_confidence"] = df["confidence"]

    required_columns = [
        "claim_id",
        "raw_claim",
        "label",
        "speaker",
        "subject",
        "subject_type",
        "relation",
        "object",
        "object_type",
        "date",
        "extraction_confidence",
        "entities",
    ]
    for column in required_columns:
        if column not in df.columns:
            df[column] = None
    return df[required_columns]


def link_claim(
    row: pd.Series,
    cache: dict[str, Any],
    *,
    prior_links: dict[str, dict[str, Any]],
    offline: bool,
    sleep_seconds: float,
    timeout: int,
) -> dict[str, Any]:
    subject = clean_text(row.get("subject"))
    obj = clean_text(row.get("object"))
    subject_type = clean_text(row.get("subject_type"))
    object_type = clean_text(row.get("object_type"))

    subject_link = search_entity(
        subject,
        subject_type,
        row,
        cache,
        prior_links=prior_links,
        offline=offline,
        timeout=timeout,
        sleep_seconds=sleep_seconds,
    )
    object_is_literal = is_literal(obj, object_type)
    object_link = None
    if not object_is_literal:
        object_link = search_entity(
            obj,
            object_type,
            row,
            cache,
            prior_links=prior_links,
            offline=offline,
            timeout=timeout,
            sleep_seconds=sleep_seconds,
        )

    property_id, property_label, property_reason = infer_property(row)
    linking_confidence = calculate_linking_confidence(
        subject_link,
        object_link,
        object_is_literal,
        property_id,
        row.get("extraction_confidence"),
    )

    return {
        "claim_id": row.get("claim_id"),
        "raw_claim": row.get("raw_claim"),
        "label": row.get("label"),
        "speaker": row.get("speaker"),
        "subject": subject,
        "subject_type": subject_type,
        "subject_kg_id": subject_link.get("kg_id") if subject_link else None,
        "subject_kg_label": subject_link.get("label") if subject_link else None,
        "subject_kg_description": subject_link.get("description") if subject_link else None,
        "subject_link_source": subject_link.get("source") if subject_link else None,
        "relation": row.get("relation"),
        "property_id": property_id,
        "property_label": property_label,
        "object": obj,
        "object_type": object_type,
        "object_kg_id": object_link.get("kg_id") if object_link else None,
        "object_kg_label": object_link.get("label") if object_link else None,
        "object_kg_description": object_link.get("description") if object_link else None,
        "object_link_source": object_link.get("source") if object_link else None,
        "date": row.get("date"),
        "extraction_confidence": row.get("extraction_confidence"),
        "linking_confidence": linking_confidence,
        "linking_notes": build_linking_notes(
            subject_link,
            object_link,
            object_is_literal,
            property_id,
            property_reason,
        ),
    }


def load_input_records(project_root: Path, input_path: Path | None) -> tuple[list[dict[str, Any]], Path]:
    if input_path is None:
        preferred = project_root / "01_Claim_Extraction" / "extracted_triples_filtered.json"
        fallback = project_root / "shared" / "sample_triples.json"
        input_path = preferred if preferred.exists() else fallback
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return json.loads(input_path.read_text()), input_path


def project_relative_path(path: Path, project_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return str(path)


def build_summary(
    linked_df: pd.DataFrame,
    input_path: Path,
    output_path: Path,
    project_root: Path,
) -> dict[str, Any]:
    relation_summary = (
        linked_df["relation"]
        .fillna("missing")
        .value_counts()
        .head(15)
        .rename_axis("relation")
        .reset_index(name="count")
        .to_dict(orient="records")
    )
    return {
        "input_path": project_relative_path(input_path, project_root),
        "output_path": project_relative_path(output_path, project_root),
        "total_claims": int(len(linked_df)),
        "subjects_linked": int(linked_df["subject_kg_id"].notna().sum()),
        "objects_linked": int(linked_df["object_kg_id"].notna().sum()),
        "records_with_any_entity_link": int(
            (linked_df["subject_kg_id"].notna() | linked_df["object_kg_id"].notna()).sum()
        ),
        "relations_with_property_id": int(linked_df["property_id"].notna().sum()),
        "average_linking_confidence": round(float(linked_df["linking_confidence"].mean()), 3),
        "low_confidence_records_below_0_4": int((linked_df["linking_confidence"] < 0.4).sum()),
        "manual_subject_links": int((linked_df["subject_link_source"] == "manual_alias").sum()),
        "manual_object_links": int((linked_df["object_link_source"] == "manual_alias").sum()),
        "top_relations": relation_summary,
    }


def run_entity_linking(
    project_root: Path | None = None,
    input_path: Path | None = None,
    output_path: Path | None = None,
    max_records: int | None = None,
    offline: bool = False,
    sleep_seconds: float = 0.05,
    timeout: int = 6,
) -> dict[str, Any]:
    project_root = find_project_root(project_root)
    module_dir = project_root / "03_Entity_Linking_KR"
    output_path = output_path or module_dir / "linked_entities.json"
    summary_path = module_dir / "entity_linking_summary.json"

    records, resolved_input_path = load_input_records(project_root, input_path)
    df = normalize_input_records(records)
    if max_records is not None:
        df = df.head(max_records)

    cache: dict[str, Any] = {}
    prior_links = build_prior_links(output_path)
    linked_records = [
        link_claim(
            row,
            cache,
            prior_links=prior_links,
            offline=offline,
            sleep_seconds=sleep_seconds,
            timeout=timeout,
        )
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Linking entities")
    ]
    linked_df = pd.DataFrame(linked_records)

    output_path.write_text(json.dumps(linked_records, indent=2, ensure_ascii=False))
    summary = build_summary(linked_df, resolved_input_path, output_path, project_root)
    summary_path.write_text(json.dumps(summary, indent=2))

    return {
        "linked_records": linked_records,
        "linked_df": linked_df,
        "summary": summary,
        "output_path": output_path,
        "summary_path": summary_path,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Link extracted claim triples to Wikidata entities.")
    parser.add_argument("--input", type=Path, default=None, help="Input extracted triples JSON path.")
    parser.add_argument("--output", type=Path, default=None, help="Output linked entities JSON path.")
    parser.add_argument("--max-records", type=int, default=None, help="Optional limit for quick test runs.")
    parser.add_argument("--offline", action="store_true", help="Use manual aliases only; skip Wikidata API calls.")
    parser.add_argument("--sleep", type=float, default=0.05, help="Delay between Wikidata API calls.")
    parser.add_argument("--timeout", type=int, default=6, help="Wikidata request timeout in seconds.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result = run_entity_linking(
        input_path=args.input,
        output_path=args.output,
        max_records=args.max_records,
        offline=args.offline,
        sleep_seconds=args.sleep,
        timeout=args.timeout,
    )
    print(json.dumps(result["summary"], indent=2))
