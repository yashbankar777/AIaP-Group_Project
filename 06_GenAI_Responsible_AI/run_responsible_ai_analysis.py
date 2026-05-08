from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "LIAR_dataset").exists() and (candidate / "06_GenAI_Responsible_AI").exists():
            return candidate
    raise FileNotFoundError("Could not find the project root.")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text())


def percent(part: int | float, total: int | float) -> float:
    if not total:
        return 0.0
    return round(float(part) / float(total) * 100, 1)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def project_relative_path(path: Path, project_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return str(path)


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return ""
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for row in rows:
        values = []
        for column in columns:
            value = str(row.get(column, "")).replace("\n", " ").replace("|", "/")
            values.append(value)
        body.append("| " + " | ".join(values) + " |")
    return "\n".join([header, divider, *body])


def load_project_evidence(project_root: Path) -> dict[str, Any]:
    dataset_summary = read_json(project_root / "02_Problem_Dataset_EDA" / "dataset_summary.json", {})
    entity_summary = read_json(project_root / "03_Entity_Linking_KR" / "entity_linking_summary.json", {})
    kg_summary = read_json(project_root / "04_KG_Reasoning" / "kg_reasoning_summary.json", {})
    bayes_summary = read_json(project_root / "05_Bayesian_Inference" / "final_verdict_summary.json", {})
    final_verdicts = read_json(project_root / "05_Bayesian_Inference" / "final_verdicts.json", [])
    extracted_triples = read_json(project_root / "01_Claim_Extraction" / "extracted_triples_filtered.json", [])

    return {
        "dataset_summary": dataset_summary,
        "entity_summary": entity_summary,
        "kg_summary": kg_summary,
        "bayes_summary": bayes_summary,
        "final_verdicts": final_verdicts,
        "extracted_triples": extracted_triples,
    }


def build_key_metrics(evidence: dict[str, Any]) -> dict[str, Any]:
    dataset_summary = evidence["dataset_summary"]
    extraction_handoff = dataset_summary.get("claim_extraction_handoff", {})
    entity_summary = evidence["entity_summary"]
    kg_summary = evidence["kg_summary"]
    bayes_summary = evidence["bayes_summary"]

    total_claims = int(entity_summary.get("total_claims") or kg_summary.get("total_claims") or 0)
    records_with_any_link = int(entity_summary.get("records_with_any_entity_link") or 0)
    kg_status_counts = kg_summary.get("status_counts", {})
    bayes_verdict_counts = bayes_summary.get("verdict_counts", {})

    return {
        "liar_total_rows": int(dataset_summary.get("total_rows") or 0),
        "liar_label_count": len(dataset_summary.get("label_order", [])),
        "claim_extraction_records": int(extraction_handoff.get("record_count") or len(evidence["extracted_triples"])),
        "mean_extraction_confidence": extraction_handoff.get("mean_extraction_confidence"),
        "unknown_subject_type_count": extraction_handoff.get("subject_type_distribution", {}).get("UNKNOWN", 0),
        "entity_link_coverage_percent": percent(records_with_any_link, total_claims),
        "property_mapping_percent": percent(int(entity_summary.get("relations_with_property_id") or 0), total_claims),
        "average_linking_confidence": entity_summary.get("average_linking_confidence"),
        "kg_unknown_percent": percent(int(kg_status_counts.get("unknown", 0)), total_claims),
        "kg_supported_count": int(kg_status_counts.get("supported", 0)),
        "bayesian_uncertain_percent": percent(int(bayes_verdict_counts.get("uncertain", 0)), total_claims),
        "bayesian_likely_true_count": int(bayes_verdict_counts.get("likely true", 0)),
        "average_decision_confidence": bayes_summary.get("average_decision_confidence"),
    }


def build_module_evidence(evidence: dict[str, Any], metrics: dict[str, Any]) -> list[dict[str, Any]]:
    dataset_summary = evidence["dataset_summary"]
    extraction_handoff = dataset_summary.get("claim_extraction_handoff", {})
    entity_summary = evidence["entity_summary"]
    kg_summary = evidence["kg_summary"]
    bayes_summary = evidence["bayes_summary"]

    return [
        {
            "module": "01 Claim Extraction",
            "method": "RoBERTa NER plus spaCy dependency parsing",
            "project_evidence": (
                f"{metrics['claim_extraction_records']} triples; mean extraction confidence "
                f"{metrics['mean_extraction_confidence']}; {metrics['unknown_subject_type_count']} UNKNOWN subjects"
            ),
            "responsible_ai_interpretation": (
                "The system creates auditable subject-relation-object evidence, but extraction confidence is not a "
                "truth score and parser errors can flow downstream."
            ),
        },
        {
            "module": "02 Dataset EDA",
            "method": "LIAR dataset profiling and preprocessing review",
            "project_evidence": (
                f"{metrics['liar_total_rows']} rows across {metrics['liar_label_count']} truth labels; "
                f"{dataset_summary.get('duplicate_statement_count', 0)} duplicate statements; "
                f"{dataset_summary.get('missing_values', {}).get('speaker_job', 0)} missing speaker jobs"
            ),
            "responsible_ai_interpretation": (
                "The political dataset is useful for benchmarking but carries selection, speaker, topic, and label "
                "bias risks."
            ),
        },
        {
            "module": "03 Entity Linking and KR",
            "method": "Wikidata-compatible entity and property representation",
            "project_evidence": (
                f"{entity_summary.get('records_with_any_entity_link', 0)} of {entity_summary.get('total_claims', 0)} "
                f"records have any entity link; property mapping coverage is {metrics['property_mapping_percent']}%; "
                f"average linking confidence is {metrics['average_linking_confidence']}"
            ),
            "responsible_ai_interpretation": (
                "Knowledge representation improves traceability, but low linking and property coverage create a major "
                "verification bottleneck."
            ),
        },
        {
            "module": "04 KG Reasoning",
            "method": "Conservative symbolic reasoning over KG evidence",
            "project_evidence": (
                f"{kg_summary.get('status_counts', {}).get('unknown', 0)} unknown, "
                f"{metrics['kg_supported_count']} supported, 0 contradicted; "
                f"average KG confidence {kg_summary.get('average_kg_confidence')}"
            ),
            "responsible_ai_interpretation": (
                "The KG layer avoids unsupported factual claims by abstaining when evidence is insufficient."
            ),
        },
        {
            "module": "05 Bayesian Inference",
            "method": "Conservative posterior probability and final verdict model",
            "project_evidence": (
                f"{bayes_summary.get('verdict_counts', {}).get('uncertain', 0)} uncertain and "
                f"{metrics['bayesian_likely_true_count']} likely true; average decision confidence "
                f"{metrics['average_decision_confidence']}"
            ),
            "responsible_ai_interpretation": (
                "The final model communicates uncertainty instead of converting weak evidence into definitive "
                "misinformation labels."
            ),
        },
    ]


def build_comparison_rows() -> list[dict[str, Any]]:
    return [
        {
            "dimension": "Evidence traceability",
            "current_pipeline": "High: triples, entity IDs, KG status, evidence text, and Bayesian reasoning are stored.",
            "llm_only": "Often weak unless explicitly forced to cite sources; generated rationales may sound plausible without evidence.",
            "rag_hybrid": "Potentially high if retrieved passages, KG IDs, prompts, and model outputs are logged together.",
        },
        {
            "dimension": "Coverage",
            "current_pipeline": "Low-to-moderate: strict entity linking and KG rules leave most claims unknown.",
            "llm_only": "High surface coverage because an LLM can answer almost every claim.",
            "rag_hybrid": "Moderate-to-high if retrieval expands evidence while abstention remains allowed.",
        },
        {
            "dimension": "Factuality risk",
            "current_pipeline": "Lower overclaiming risk because the system abstains when KG evidence is missing.",
            "llm_only": "Higher hallucination and overconfidence risk, especially on political or time-sensitive claims.",
            "rag_hybrid": "Lower than LLM-only when answers must be grounded in retrieved, checked sources.",
        },
        {
            "dimension": "Bias sensitivity",
            "current_pipeline": "Dataset and speaker-history bias remain, but the Bayesian prior is deliberately weak.",
            "llm_only": "May reproduce training-data, prompt, political, and source-selection biases with less visibility.",
            "rag_hybrid": "Can be audited through source diversity checks and topic/speaker fairness reporting.",
        },
        {
            "dimension": "Interpretability",
            "current_pipeline": "Strong: each stage has a specific representation and failure mode.",
            "llm_only": "Weak-to-moderate: natural-language explanations are readable but not necessarily faithful.",
            "rag_hybrid": "Strong if the LLM is used to summarise retrieved evidence rather than invent evidence.",
        },
        {
            "dimension": "Scalability",
            "current_pipeline": "Efficient once built, but KG lookup and relation coverage limit throughput and recall.",
            "llm_only": "Simple to prototype but expensive and harder to reproduce at scale.",
            "rag_hybrid": "Most realistic deployment path: batch retrieval, cached evidence, and selective LLM calls.",
        },
        {
            "dimension": "Best use",
            "current_pipeline": "Auditable verification, conservative decision support, and reportable uncertainty.",
            "llm_only": "Exploratory assistance, claim rewriting, and identifying possible evidence sources.",
            "rag_hybrid": "Human-in-the-loop fact checking with citations, calibrated uncertainty, and escalation.",
        },
    ]


def build_risk_register(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "risk_area": "Hallucinated or unsupported evidence",
            "project_evidence": f"KG reasoning returned {metrics['kg_unknown_percent']}% unknown results.",
            "potential_harm": "A system that still gives definitive answers could falsely accuse or falsely clear claims.",
            "current_control": "The KG and Bayesian modules abstain when evidence is weak.",
            "recommended_improvement": "Use RAG with citation verification and require source-level evidence before final labels.",
            "severity": "High",
        },
        {
            "risk_area": "False positives",
            "project_evidence": f"Bayesian output kept {metrics['bayesian_uncertain_percent']}% of claims uncertain.",
            "potential_harm": "True or nuanced claims could be labelled misinformation, harming public trust.",
            "current_control": "Conservative 0.65 threshold and explicit uncertainty class.",
            "recommended_improvement": "Route low-evidence or high-impact claims to human review.",
            "severity": "High",
        },
        {
            "risk_area": "False negatives",
            "project_evidence": "The current KG layer found no contradicted claims in the 500-record handoff.",
            "potential_harm": "False claims may pass through as uncertain rather than being challenged.",
            "current_control": "The output does not call uncertain claims true.",
            "recommended_improvement": "Improve relation extraction, claim decomposition, and live KG/source querying.",
            "severity": "High",
        },
        {
            "risk_area": "Dataset and speaker bias",
            "project_evidence": f"LIAR has {metrics['liar_total_rows']} political claims and concentrated top speakers/topics.",
            "potential_harm": "The model may encode political, media-selection, or speaker-history bias.",
            "current_control": "Speaker history is weakly weighted and labels are not used as probability evidence.",
            "recommended_improvement": "Report performance by speaker, party, topic, state, and label bucket.",
            "severity": "Medium",
        },
        {
            "risk_area": "Entity-linking error propagation",
            "project_evidence": (
                f"Only {metrics['entity_link_coverage_percent']}% of records have any entity link and "
                f"property mapping coverage is {metrics['property_mapping_percent']}%."
            ),
            "potential_harm": "Wrong or missing entity IDs can make correct KG reasoning impossible.",
            "current_control": "Low-confidence links remain visible and usually lead to unknown KG status.",
            "recommended_improvement": "Add candidate ranking, alias expansion, entity disambiguation, and confidence calibration.",
            "severity": "Medium",
        },
        {
            "risk_area": "Automation misuse",
            "project_evidence": "The project produces decision-support probabilities, not verified legal or journalistic rulings.",
            "potential_harm": "Users may treat probabilistic outputs as authoritative fact-checks.",
            "current_control": "Outputs include reasoning, uncertainty, and reference-label separation.",
            "recommended_improvement": "Add UI warnings, audit logs, appeal paths, and reviewer sign-off for public deployment.",
            "severity": "Medium",
        },
    ]


def build_future_work() -> list[dict[str, Any]]:
    return [
        {
            "priority": 1,
            "improvement": "Replace single-triple extraction with multi-claim decomposition and coreference resolution.",
            "why_it_matters": "Political claims often contain multiple factual units and pronouns that break simple triples.",
            "expected_effect": "Higher recall and cleaner downstream KG queries.",
        },
        {
            "priority": 2,
            "improvement": "Expand entity linking with candidate ranking, aliases, and confidence calibration.",
            "why_it_matters": "Entity-link coverage is the main bottleneck before KG reasoning.",
            "expected_effect": "More claims reach evidence-based support or contradiction decisions.",
        },
        {
            "priority": 3,
            "improvement": "Add live Wikidata/DBpedia/SPARQL property checks plus trusted web retrieval.",
            "why_it_matters": "The current KG layer mostly reasons over local descriptions and simple class rules.",
            "expected_effect": "Better factual coverage while keeping evidence traceable.",
        },
        {
            "priority": 4,
            "improvement": "Use an LLM only inside a retrieval-grounded workflow.",
            "why_it_matters": "LLMs can improve paraphrase handling and evidence synthesis but must not invent sources.",
            "expected_effect": "Improved usability without losing auditability.",
        },
        {
            "priority": 5,
            "improvement": "Calibrate Bayesian probabilities against a labelled validation set.",
            "why_it_matters": "Current probabilities are transparent assumptions rather than empirically calibrated truth rates.",
            "expected_effect": "More reliable decision thresholds and confidence estimates.",
        },
        {
            "priority": 6,
            "improvement": "Create a human-in-the-loop review workflow for high-impact or low-evidence claims.",
            "why_it_matters": "Responsible deployment needs accountability for decisions that affect people or public discourse.",
            "expected_effect": "Lower harm from false positives, false negatives, and automation bias.",
        },
    ]


def build_markdown(
    metrics: dict[str, Any],
    module_evidence: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    risk_register: list[dict[str, Any]],
    future_work: list[dict[str, Any]],
) -> str:
    module_table = markdown_table(
        module_evidence,
        ["module", "method", "project_evidence", "responsible_ai_interpretation"],
    )
    comparison_table = markdown_table(
        comparison_rows,
        ["dimension", "current_pipeline", "llm_only", "rag_hybrid"],
    )
    risk_table = markdown_table(
        risk_register,
        ["risk_area", "project_evidence", "potential_harm", "current_control", "recommended_improvement", "severity"],
    )
    future_work_table = markdown_table(
        future_work,
        ["priority", "improvement", "why_it_matters", "expected_effect"],
    )

    return f"""# Responsible AI Analysis

This module compares the project pipeline with GenAI and LLM-based alternatives, then evaluates the system through responsible AI risks, limitations, scalability, and future work.

## Executive Position

The current system is best understood as an interpretable decision-support pipeline, not a fully automated fact-checker. Its main strength is traceability: the project preserves extracted triples, entity links, KG reasoning status, Bayesian assumptions, and final uncertainty. Its main weakness is evidence coverage: KG reasoning returns unknown for {metrics['kg_unknown_percent']}% of the 500 processed claims, which leads Bayesian inference to keep {metrics['bayesian_uncertain_percent']}% of claims uncertain.

For a high-stakes misinformation setting, this conservative behaviour is ethically preferable to a GenAI-only system that answers every claim with fluent but potentially unsupported explanations. The strongest future direction is a hybrid RAG and KG workflow where an LLM helps decompose claims and summarise retrieved evidence, while citations, entity IDs, calibrated probabilities, and human review remain mandatory.

## Evidence From Project Modules

{module_table}

## GenAI and LLM Comparison

{comparison_table}

## Responsible AI Risk Register

{risk_table}

## Scalability and Deployment Reflection

- Claim extraction can be batched, but higher-quality relation extraction and coreference resolution are needed before scaling beyond the current 500-record handoff.
- Entity linking is the main coverage bottleneck: only {metrics['entity_link_coverage_percent']}% of records have any entity link, and property mapping coverage is {metrics['property_mapping_percent']}%.
- KG reasoning is computationally cheap once entities and properties are available, but external API calls, incomplete KG coverage, and political claim complexity limit recall.
- Bayesian inference is scalable and transparent, but its probabilities should be calibrated with validation data before deployment.
- LLM-only verification scales poorly in governance terms because cost, prompt sensitivity, hallucination risk, and reproducibility problems increase with volume.
- A hybrid system should cache retrieved evidence, log prompts and sources, enforce abstention, and escalate high-impact cases to human reviewers.

## Recommended Future Work

{future_work_table}

## Report-Ready Conclusion

The project demonstrates a responsible design trade-off: it sacrifices broad automated coverage in order to preserve interpretability, evidence traceability, and uncertainty. A GenAI-only approach would likely produce more complete-looking answers, but those answers would be harder to audit and more vulnerable to hallucination and overconfidence. The most defensible improvement is not to replace the pipeline with an LLM, but to integrate LLMs in a constrained RAG workflow that improves claim decomposition, source retrieval, and explanation quality while preserving KG evidence, calibrated Bayesian uncertainty, and human oversight.
"""


def run_responsible_ai_analysis(project_root: Path | None = None) -> dict[str, Any]:
    project_root = find_project_root(project_root)
    module_dir = project_root / "06_GenAI_Responsible_AI"
    report_tables_dir = project_root / "report_assets" / "tables"

    evidence = load_project_evidence(project_root)
    metrics = build_key_metrics(evidence)
    module_evidence = build_module_evidence(evidence, metrics)
    comparison_rows = build_comparison_rows()
    risk_register = build_risk_register(metrics)
    future_work = build_future_work()

    artifacts = {
        "module_evidence_table": report_tables_dir / "responsible_ai_module_evidence.csv",
        "comparison_table": report_tables_dir / "genai_pipeline_comparison.csv",
        "risk_register": report_tables_dir / "responsible_ai_risk_register.csv",
        "future_work_table": report_tables_dir / "responsible_ai_future_work.csv",
        "summary_json": module_dir / "responsible_ai_summary.json",
        "analysis_markdown": module_dir / "responsible_ai_analysis.md",
    }

    write_csv(artifacts["module_evidence_table"], module_evidence)
    write_csv(artifacts["comparison_table"], comparison_rows)
    write_csv(artifacts["risk_register"], risk_register)
    write_csv(artifacts["future_work_table"], future_work)

    markdown = build_markdown(metrics, module_evidence, comparison_rows, risk_register, future_work)
    artifacts["analysis_markdown"].write_text(markdown, encoding="utf-8")

    summary = {
        "metrics": metrics,
        "module_evidence": module_evidence,
        "comparison_rows": comparison_rows,
        "risk_register": risk_register,
        "future_work": future_work,
        "artifacts": {key: project_relative_path(value, project_root) for key, value in artifacts.items()},
    }
    artifacts["summary_json"].write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


if __name__ == "__main__":
    result = run_responsible_ai_analysis()
    print(json.dumps({"metrics": result["metrics"], "artifacts": result["artifacts"]}, indent=2))
