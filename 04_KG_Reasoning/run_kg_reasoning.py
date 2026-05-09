from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
import pandas as pd


BE_RELATIONS = {"be", "is", "was", "were", "are", "am", "has_be", "have_be"}
SPEECH_RELATIONS = {"say", "says", "said", "claim", "claims", "tell", "tells", "has_say"}

CLASS_RULES = {
    "city": {
        "object_terms": {"city", "town", "municipality"},
        "support_terms": {"city", "capital city", "seat of", "municipality"},
        "contradict_terms": {"country", "state of the united states", "organization", "politician"},
    },
    "state": {
        "object_terms": {"state"},
        "support_terms": {"state of the united states", "state in", "u.s. state"},
        "contradict_terms": {"city", "country", "organization", "politician"},
    },
    "country": {
        "object_terms": {"country", "nation"},
        "support_terms": {"country", "sovereign state", "nation in"},
        "contradict_terms": {"city", "state of the united states", "organization", "politician"},
    },
    "person": {
        "object_terms": {"person", "man", "woman"},
        "support_terms": {"politician", "president", "senator", "governor", "lawyer", "businessman"},
        "contradict_terms": {"city", "country", "organization", "statute"},
    },
    "organization": {
        "object_terms": {"organization", "organisation", "company", "group", "agency"},
        "support_terms": {"organization", "organisation", "company", "agency", "institution", "team"},
        "contradict_terms": {"city", "country", "state of the united states", "politician"},
    },
    "office": {
        "object_terms": {"president", "governor", "senator", "representative", "secretary", "mayor"},
        "support_terms": {"president", "governor", "senator", "representative", "secretary", "mayor"},
        "contradict_terms": {"city", "country", "organization"},
    },
}


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "LIAR_dataset").exists() and (candidate / "03_Entity_Linking_KR").exists():
            return candidate
    raise FileNotFoundError("Could not find the project root.")


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"none", "nan", "null", "unknown"}:
        return None
    return re.sub(r"\s+", " ", text)


def normalize_relation(value: Any) -> str | None:
    text = clean_text(value)
    if text is None:
        return None
    return re.sub(r"_+", "_", text.lower().replace("-", "_").replace(" ", "_"))


def tokenize(text: str | None) -> set[str]:
    if not text:
        return set()
    return set(re.findall(r"[a-z]+", text.lower()))


def contains_phrase(text: str | None, phrases: set[str]) -> bool:
    lowered = (text or "").lower()
    return any(phrase in lowered for phrase in phrases)


def is_conditional_claim(raw_claim: str | None) -> bool:
    lowered = (raw_claim or "").lower()
    conditional_markers = [
        "if ",
        "would ",
        "could ",
        "should ",
        "were a country",
        "hypothetical",
    ]
    return any(marker in lowered for marker in conditional_markers)


def simple_object_class(object_value: str | None) -> str | None:
    if not object_value:
        return None
    value = object_value.lower().strip()
    value = re.sub(r"[^a-z\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"^(a|an|the)\s+", "", value)

    for class_name, rule in CLASS_RULES.items():
        if value in rule["object_terms"]:
            return class_name
    return None


def load_linked_records(project_root: Path, input_path: Path | None) -> tuple[list[dict[str, Any]], Path]:
    if input_path is None:
        preferred = project_root / "03_Entity_Linking_KR" / "linked_entities.json"
        fallback = project_root / "shared" / "sample_linked_entities.json"
        input_path = preferred if preferred.exists() else fallback
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return json.loads(input_path.read_text()), input_path


def kg_unknown(record: dict[str, Any], reason: str, confidence: float = 0.35) -> dict[str, Any]:
    return {
        "claim_id": record.get("claim_id"),
        "raw_claim": record.get("raw_claim"),
        "kg_status": "unknown",
        "kg_confidence": round(confidence, 3),
        "evidence": reason,
        "reasoning_rule": "insufficient_kg_evidence",
        "source": "local KG reasoning rules",
    }


def class_reasoning(record: dict[str, Any]) -> dict[str, Any] | None:
    relation = normalize_relation(record.get("relation"))
    if relation not in BE_RELATIONS:
        return None

    raw_claim = clean_text(record.get("raw_claim"))
    obj = clean_text(record.get("object"))
    description = clean_text(record.get("subject_kg_description"))
    subject_label = clean_text(record.get("subject_kg_label")) or clean_text(record.get("subject"))
    linking_confidence = float(record.get("linking_confidence") or 0)

    if not record.get("subject_kg_id") or not obj or not description:
        return None
    if linking_confidence < 0.45:
        return None
    if is_conditional_claim(raw_claim):
        return kg_unknown(
            record,
            "Claim appears conditional or hypothetical, so KG class matching is not applied.",
            confidence=0.4,
        )

    class_name = simple_object_class(obj)
    if class_name is None:
        return None

    rule = CLASS_RULES[class_name]
    if contains_phrase(description, rule["support_terms"]):
        confidence = min(0.85, 0.45 + 0.4 * linking_confidence)
        return {
            "claim_id": record.get("claim_id"),
            "raw_claim": raw_claim,
            "kg_status": "supported",
            "kg_confidence": round(confidence, 3),
            "evidence": (
                f"Wikidata description for {subject_label} is '{description}', "
                f"which matches the simple claim object class '{obj}'."
            ),
            "reasoning_rule": f"description_class_match_{class_name}",
            "source": "Wikidata entity description from entity linking",
        }

    if contains_phrase(description, rule["contradict_terms"]):
        confidence = min(0.8, 0.4 + 0.35 * linking_confidence)
        return {
            "claim_id": record.get("claim_id"),
            "raw_claim": raw_claim,
            "kg_status": "contradicted",
            "kg_confidence": round(confidence, 3),
            "evidence": (
                f"Wikidata description for {subject_label} is '{description}', "
                f"which conflicts with the simple claim object class '{obj}'."
            ),
            "reasoning_rule": f"description_class_mismatch_{class_name}",
            "source": "Wikidata entity description from entity linking",
        }

    return None


def property_reasoning(record: dict[str, Any]) -> dict[str, Any] | None:
    property_id = clean_text(record.get("property_id"))
    if property_id is None:
        return None

    subject_label = clean_text(record.get("subject_kg_label")) or clean_text(record.get("subject"))
    object_label = clean_text(record.get("object_kg_label")) or clean_text(record.get("object"))
    property_label = clean_text(record.get("property_label")) or property_id

    if not record.get("subject_kg_id"):
        return kg_unknown(
            record,
            f"Relation maps to {property_label}, but the subject has no reliable KG ID.",
            confidence=0.35,
        )

    if not record.get("object_kg_id"):
        return kg_unknown(
            record,
            (
                f"Relation maps to Wikidata property {property_id} ({property_label}), "
                f"but object '{object_label}' is not linked to a KG entity or literal query value."
            ),
            confidence=0.45,
        )

    if record.get("subject_kg_id") == record.get("object_kg_id"):
        return kg_unknown(
            record,
            (
                f"Subject and object both link to {subject_label}; this is not enough to verify "
                f"property {property_id} ({property_label})."
            ),
            confidence=0.4,
        )

    return kg_unknown(
        record,
        (
            f"Subject '{subject_label}' and object '{object_label}' are linked and relation maps to "
            f"{property_id} ({property_label}), but this local run does not query full Wikidata claims."
        ),
        confidence=0.5,
    )


def linked_entity_coverage_reasoning(record: dict[str, Any]) -> dict[str, Any]:
    relation = normalize_relation(record.get("relation"))
    linking_confidence = float(record.get("linking_confidence") or 0)

    if not record.get("subject_kg_id") and not record.get("object_kg_id"):
        return kg_unknown(
            record,
            "No subject or object KG entity was linked, so KG reasoning cannot verify the claim.",
            confidence=0.25,
        )

    if relation in SPEECH_RELATIONS:
        return kg_unknown(
            record,
            "The extracted relation is a speech/reporting relation, not a factual KG property.",
            confidence=0.35,
        )

    if linking_confidence < 0.4:
        return kg_unknown(
            record,
            "Entity-linking confidence is too low for reliable KG reasoning.",
            confidence=0.3,
        )

    return kg_unknown(
        record,
        "Linked entities are available, but no safe KG rule applies to this extracted relation.",
        confidence=0.4,
    )


def reason_over_claim(record: dict[str, Any]) -> dict[str, Any]:
    for rule in [property_reasoning, class_reasoning]:
        result = rule(record)
        if result is not None:
            return attach_context(result, record)

    return attach_context(linked_entity_coverage_reasoning(record), record)


def attach_context(result: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    result.update(
        {
            "label": record.get("label"),
            "subject": record.get("subject"),
            "subject_kg_id": record.get("subject_kg_id"),
            "subject_kg_label": record.get("subject_kg_label"),
            "relation": record.get("relation"),
            "property_id": record.get("property_id"),
            "object": record.get("object"),
            "object_kg_id": record.get("object_kg_id"),
            "object_kg_label": record.get("object_kg_label"),
            "linking_confidence": record.get("linking_confidence"),
        }
    )
    return result


def project_relative_path(path: Path, project_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return str(path)


def build_summary(
    results_df: pd.DataFrame,
    input_path: Path,
    output_path: Path,
    project_root: Path,
) -> dict[str, Any]:
    status_counts = results_df["kg_status"].value_counts().to_dict()
    rule_counts = (
        results_df["reasoning_rule"]
        .value_counts()
        .rename_axis("reasoning_rule")
        .reset_index(name="count")
        .to_dict(orient="records")
    )
    return {
        "input_path": project_relative_path(input_path, project_root),
        "output_path": project_relative_path(output_path, project_root),
        "total_claims": int(len(results_df)),
        "status_counts": {key: int(value) for key, value in status_counts.items()},
        "average_kg_confidence": round(float(results_df["kg_confidence"].mean()), 3),
        "reasoning_rule_counts": rule_counts,
    }


def run_kg_reasoning(
    project_root: Path | None = None,
    input_path: Path | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    project_root = find_project_root(project_root)
    module_dir = project_root / "04_KG_Reasoning"
    output_path = output_path or module_dir / "kg_results.json"
    summary_path = module_dir / "kg_reasoning_summary.json"

    linked_records, resolved_input_path = load_linked_records(project_root, input_path)
    kg_results = [reason_over_claim(record) for record in linked_records]
    results_df = pd.DataFrame(kg_results)

    output_path.write_text(json.dumps(kg_results, indent=2, ensure_ascii=False))
    summary = build_summary(results_df, resolved_input_path, output_path, project_root)
    summary_path.write_text(json.dumps(summary, indent=2))

    return {
        "kg_results": kg_results,
        "results_df": results_df,
        "summary": summary,
        "output_path": output_path,
        "summary_path": summary_path,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply conservative KG reasoning to linked claims.")
    parser.add_argument("--input", type=Path, default=None, help="Input linked entities JSON path.")
    parser.add_argument("--output", type=Path, default=None, help="Output KG results JSON path.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result = run_kg_reasoning(input_path=args.input, output_path=args.output)
    print(json.dumps(result["summary"], indent=2))
