from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

LIAR_COLUMNS = [
    "statement_id",
    "label",
    "statement",
    "subjects",
    "speaker",
    "speaker_job",
    "state",
    "party",
    "barely_true_count",
    "false_count",
    "half_true_count",
    "mostly_true_count",
    "pants_fire_count",
    "context",
]

CREDIT_COLUMNS = [
    "barely_true_count",
    "false_count",
    "half_true_count",
    "mostly_true_count",
    "pants_fire_count",
]

KG_LOG_BAYES_FACTORS = {
    "supported": 5.0,
    "contradicted": -5.0,
    "unknown": 0.0,
}

VERDICT_THRESHOLD = 0.55
SPEAKER_PRIOR_STRENGTH = 0.35
SPEAKER_HISTORY_SMOOTHING = 2.0


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "LIAR_dataset").exists() and (candidate / "04_KG_Reasoning").exists():
            return candidate
    raise FileNotFoundError("Could not find the project root.")


def load_json_records(path: Path) -> list[dict[str, Any]]:
    records = json.loads(path.read_text())
    if not isinstance(records, list):
        raise ValueError(f"Expected a list of records in {path}")
    return records


def load_kg_records(project_root: Path, input_path: Path | None) -> tuple[list[dict[str, Any]], Path]:
    if input_path is None:
        preferred = project_root / "04_KG_Reasoning" / "kg_results.json"
        fallback = project_root / "shared" / "sample_kg_results.json"
        input_path = preferred if preferred.exists() else fallback
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return load_json_records(input_path), input_path


def load_linked_records(project_root: Path, linked_input_path: Path | None) -> tuple[list[dict[str, Any]], Path | None]:
    if linked_input_path is None:
        linked_input_path = project_root / "03_Entity_Linking_KR" / "linked_entities.json"
    if not linked_input_path.exists():
        return [], None
    return load_json_records(linked_input_path), linked_input_path


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"none", "nan", "null", "unknown"}:
        return None
    return " ".join(text.split())


def normalize_claim_text(value: Any) -> str:
    return (clean_text(value) or "").casefold()


def normalize_status(value: Any) -> str:
    status = (clean_text(value) or "unknown").lower().replace("-", "_").replace(" ", "_")
    if status in {"support", "supports", "supported"}:
        return "supported"
    if status in {"contradict", "contradicts", "contradicted"}:
        return "contradicted"
    return "unknown"


def parse_probability(value: Any, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(number):
        return default
    return max(0.0, min(1.0, number))


def logit(probability: float) -> float:
    probability = max(0.001, min(0.999, probability))
    return math.log(probability / (1.0 - probability))


def sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def load_liar_dataset(project_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for split, filename in {
        "train": "train.tsv",
        "valid": "valid.tsv",
        "test": "test.tsv",
    }.items():
        path = project_root / "LIAR_dataset" / filename
        if not path.exists():
            continue
        with path.open(newline="") as file:
            reader = csv.reader(file, delimiter="\t")
            for values in reader:
                record = {
                    column: values[index] if index < len(values) else ""
                    for index, column in enumerate(LIAR_COLUMNS)
                }
                record["split"] = split
                for column in CREDIT_COLUMNS:
                    try:
                        record[column] = int(record.get(column) or 0)
                    except ValueError:
                        record[column] = 0
                record["statement_key"] = normalize_claim_text(record.get("statement"))
                record["speaker_key"] = (clean_text(record.get("speaker")) or "").casefold()
                rows.append(record)
    return rows


def enrich_with_linked_records(
    kg_records: list[dict[str, Any]], linked_records: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    linked_by_claim_id = {
        record.get("claim_id"): record for record in linked_records if record.get("claim_id") is not None
    }

    enriched = []
    for kg_record in kg_records:
        linked_record = linked_by_claim_id.get(kg_record.get("claim_id"), {})
        merged = dict(linked_record)
        merged.update(kg_record)
        if "extraction_confidence" not in merged and "confidence" in merged:
            merged["extraction_confidence"] = merged.get("confidence")
        enriched.append(merged)
    return enriched


def liar_metadata_lookup(
    liar_records: list[dict[str, Any]],
) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, dict[str, Any]]]:
    by_statement_and_speaker: dict[tuple[str, str], dict[str, Any]] = {}
    by_statement: dict[str, dict[str, Any]] = {}

    for record in liar_records:
        statement_key = record.get("statement_key", "")
        speaker_key = record.get("speaker_key", "")
        if not statement_key:
            continue
        by_statement_and_speaker[(statement_key, speaker_key)] = record
        by_statement.setdefault(statement_key, record)

    return by_statement_and_speaker, by_statement


def attach_liar_metadata(records: list[dict[str, Any]], liar_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not liar_records:
        return records

    exact_lookup, statement_lookup = liar_metadata_lookup(liar_records)
    enriched = []
    for record in records:
        claim_key = normalize_claim_text(record.get("raw_claim"))
        speaker_key = (clean_text(record.get("speaker")) or "").casefold()
        metadata = exact_lookup.get((claim_key, speaker_key)) or statement_lookup.get(claim_key)

        merged = dict(record)
        if metadata:
            for column in CREDIT_COLUMNS:
                merged[column] = metadata.get(column, 0)
            merged["liar_split"] = metadata.get("split")
            merged["liar_statement_id"] = metadata.get("statement_id")
        enriched.append(merged)
    return enriched


def speaker_history_prior(record: dict[str, Any]) -> tuple[float, str]:
    counts = {column: int(record.get(column) or 0) for column in CREDIT_COLUMNS}
    total_history = sum(counts.values())

    if total_history == 0:
        return 0.5, "neutral prior; no LIAR speaker-history counts were available"

    positive_history = counts["mostly_true_count"] + 0.5 * counts["half_true_count"]
    negative_history = (
        counts["false_count"]
        + counts["pants_fire_count"]
        + 0.75 * counts["barely_true_count"]
        + 0.5 * counts["half_true_count"]
    )

    raw_prior = (positive_history + SPEAKER_HISTORY_SMOOTHING) / (
        positive_history + negative_history + 2 * SPEAKER_HISTORY_SMOOTHING
    )
    coverage = min(total_history / 25.0, 1.0)
    adjusted_prior = 0.5 + SPEAKER_PRIOR_STRENGTH * coverage * (raw_prior - 0.5)
    note = (
        "speaker-history prior from LIAR credit counts "
        f"(positive={positive_history:.1f}, negative={negative_history:.1f}, total={total_history})"
    )
    return max(0.05, min(0.95, adjusted_prior)), note


def evidence_weight(record: dict[str, Any]) -> float:
    extraction_confidence = parse_probability(record.get("extraction_confidence"), default=0.7)
    linking_confidence = parse_probability(record.get("linking_confidence"), default=0.7)
    kg_confidence = parse_probability(record.get("kg_confidence"), default=0.5)

    # Stronger weighting of extraction & linking quality
    extraction_and_linking_quality = 0.5 * extraction_confidence + 0.5 * linking_confidence
    # Apply KG confidence multiplicatively, but with more impact on final weight
    combined_weight = kg_confidence * extraction_and_linking_quality
    
    # Boost weight if we have both extraction and linking confidence
    if extraction_confidence > 0.7 and linking_confidence > 0.5:
        combined_weight = min(1.0, combined_weight * 1.2)
    
    return max(0.0, min(1.0, combined_weight))


def probability_from_evidence(record: dict[str, Any]) -> dict[str, Any]:
    prior_true, prior_note = speaker_history_prior(record)
    status = normalize_status(record.get("kg_status"))
    weight = evidence_weight(record)
    log_bayes_factor = KG_LOG_BAYES_FACTORS.get(status, 0.0) * weight
    posterior_true = sigmoid(logit(prior_true) + log_bayes_factor)
    posterior_false = 1.0 - posterior_true

    if posterior_true >= VERDICT_THRESHOLD:
        final_verdict = "likely true"
    elif posterior_false >= VERDICT_THRESHOLD:
        final_verdict = "likely false"
    else:
        final_verdict = "uncertain"

    direction = {
        "supported": "increases the true odds",
        "contradicted": "decreases the true odds",
        "unknown": "adds no directional truth signal",
    }[status]
    if final_verdict == "uncertain":
        decision_note = "posterior probability stays near 0.50, so no binary verdict is forced"
    else:
        decision_note = f"posterior probability crosses the {VERDICT_THRESHOLD:.2f} threshold for {final_verdict}"
    reasoning = (
        f"Started with {prior_note}. KG status '{status}' at confidence "
        f"{parse_probability(record.get('kg_confidence'), default=0.5):.2f} {direction}; "
        f"{decision_note}."
    )

    return {
        "probability_true": round(posterior_true, 3),
        "probability_false": round(posterior_false, 3),
        "final_verdict": final_verdict,
        "decision_confidence": round(abs(posterior_true - posterior_false), 3),
        "probability_prior_true": round(prior_true, 3),
        "evidence_weight": round(weight, 3),
        "reasoning": reasoning,
    }


def final_verdict_record(record: dict[str, Any]) -> dict[str, Any]:
    probabilities = probability_from_evidence(record)
    return {
        "claim_id": record.get("claim_id"),
        "raw_claim": record.get("raw_claim"),
        "probability_true": probabilities["probability_true"],
        "probability_false": probabilities["probability_false"],
        "final_verdict": probabilities["final_verdict"],
        "decision_confidence": probabilities["decision_confidence"],
        "reasoning": probabilities["reasoning"],
        "probability_prior_true": probabilities["probability_prior_true"],
        "evidence_weight": probabilities["evidence_weight"],
        "kg_status": normalize_status(record.get("kg_status")),
        "kg_confidence": round(parse_probability(record.get("kg_confidence"), default=0.5), 3),
        "kg_evidence": record.get("evidence"),
        "reasoning_rule": record.get("reasoning_rule"),
        "extraction_confidence": round(parse_probability(record.get("extraction_confidence"), default=0.7), 3),
        "linking_confidence": round(parse_probability(record.get("linking_confidence"), default=0.7), 3),
        "speaker": record.get("speaker"),
        "reference_label": record.get("label"),
    }


def reference_bucket(label: Any) -> str | None:
    label_text = (clean_text(label) or "").lower()
    if label_text in {"true", "mostly-true"}:
        return "likely true"
    if label_text in {"false", "pants-fire"}:
        return "likely false"
    if label_text in {"half-true", "barely-true"}:
        return "uncertain"
    return None


def verdict_distribution_table(final_verdicts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(record["final_verdict"] for record in final_verdicts)
    total = len(final_verdicts) or 1
    rows = []
    for verdict in ["likely true", "likely false", "uncertain"]:
        count = counts.get(verdict, 0)
        rows.append({"final_verdict": verdict, "count": count, "percent": round(count / total * 100, 2)})
    return rows


def write_csv_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def average(records: list[dict[str, Any]], key: str) -> float:
    values = [float(record[key]) for record in records if record.get(key) is not None]
    return sum(values) / len(values) if values else 0.0


def project_relative_path(path: Path | None, project_root: Path) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return str(path)


def build_summary(
    final_verdicts: list[dict[str, Any]],
    input_path: Path,
    linked_input_path: Path | None,
    output_path: Path,
    report_table_path: Path,
    project_root: Path,
) -> dict[str, Any]:
    verdict_counts = Counter(record["final_verdict"] for record in final_verdicts)
    status_counts = Counter(record["kg_status"] for record in final_verdicts)

    summary: dict[str, Any] = {
        "input_path": project_relative_path(input_path, project_root),
        "linked_input_path": project_relative_path(linked_input_path, project_root),
        "output_path": project_relative_path(output_path, project_root),
        "report_table_path": project_relative_path(report_table_path, project_root),
        "total_claims": int(len(final_verdicts)),
        "verdict_counts": {key: int(value) for key, value in verdict_counts.items()},
        "kg_status_counts": {key: int(value) for key, value in status_counts.items()},
        "average_probability_true": round(average(final_verdicts, "probability_true"), 3),
        "average_decision_confidence": round(average(final_verdicts, "decision_confidence"), 3),
        "average_evidence_weight": round(average(final_verdicts, "evidence_weight"), 3),
        "model": {
            "prior": "neutral 0.50 adjusted only slightly by LIAR speaker-history counts when available",
            "kg_log_bayes_factors": KG_LOG_BAYES_FACTORS,
            "verdict_threshold": VERDICT_THRESHOLD,
            "speaker_prior_strength": SPEAKER_PRIOR_STRENGTH,
        },
    }

    evaluation_rows = []
    for record in final_verdicts:
        bucket = reference_bucket(record.get("reference_label"))
        if bucket is not None:
            evaluation_rows.append(
                {
                    "reference_bucket": bucket,
                    "final_verdict": record["final_verdict"],
                    "aligned": bucket == record["final_verdict"],
                }
            )

    if evaluation_rows:
        confusion_counts = Counter(
            (row["reference_bucket"], row["final_verdict"]) for row in evaluation_rows
        )
        confusion = [
            {"reference_bucket": reference_bucket_value, "final_verdict": verdict, "count": count}
            for (reference_bucket_value, verdict), count in sorted(confusion_counts.items())
        ]
        summary["reference_bucket_alignment"] = {
            "available_claims": int(len(evaluation_rows)),
            "alignment_rate": round(sum(row["aligned"] for row in evaluation_rows) / len(evaluation_rows), 3),
            "note": "Reference labels are used for evaluation only, not to compute final probabilities.",
            "confusion": confusion,
        }

    return summary


def run_bayesian_inference(
    project_root: Path | None = None,
    input_path: Path | None = None,
    linked_input_path: Path | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    project_root = find_project_root(project_root)
    module_dir = project_root / "05_Bayesian_Inference"
    output_path = output_path or module_dir / "final_verdicts.json"
    summary_path = module_dir / "final_verdict_summary.json"
    report_table_path = project_root / "report_assets" / "tables" / "bayesian_verdict_distribution.csv"

    kg_records, resolved_input_path = load_kg_records(project_root, input_path)
    linked_records, resolved_linked_input_path = load_linked_records(project_root, linked_input_path)
    enriched_records = enrich_with_linked_records(kg_records, linked_records)
    enriched_records = attach_liar_metadata(enriched_records, load_liar_dataset(project_root))

    final_verdicts = [final_verdict_record(record) for record in enriched_records]

    output_path.write_text(json.dumps(final_verdicts, indent=2, ensure_ascii=False))
    write_csv_rows(report_table_path, verdict_distribution_table(final_verdicts))

    summary = build_summary(
        final_verdicts,
        resolved_input_path,
        resolved_linked_input_path,
        output_path,
        report_table_path,
        project_root,
    )
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    return {
        "final_verdicts": final_verdicts,
        "summary": summary,
        "output_path": output_path,
        "summary_path": summary_path,
        "report_table_path": report_table_path,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Combine KG evidence into Bayesian final verdicts.")
    parser.add_argument("--input", type=Path, default=None, help="Input KG results JSON path.")
    parser.add_argument("--linked-input", type=Path, default=None, help="Optional linked entities JSON path.")
    parser.add_argument("--output", type=Path, default=None, help="Output final verdicts JSON path.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result = run_bayesian_inference(
        input_path=args.input,
        linked_input_path=args.linked_input,
        output_path=args.output,
    )
    print(json.dumps(result["summary"], indent=2, ensure_ascii=False))
