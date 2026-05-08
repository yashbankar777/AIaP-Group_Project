from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "LIAR_dataset").exists() and (candidate / "03_Entity_Linking_KR").exists():
            return candidate
    raise FileNotFoundError("Could not find project root.")


PROJECT_ROOT = find_project_root(Path(__file__))
for module_dir in [
    PROJECT_ROOT / "03_Entity_Linking_KR",
    PROJECT_ROOT / "04_KG_Reasoning",
    PROJECT_ROOT / "05_Bayesian_Inference",
]:
    sys.path.insert(0, str(module_dir))

from run_bayesian_inference import final_verdict_record  # noqa: E402
from run_entity_linking import build_prior_links, link_claim, normalize_input_records  # noqa: E402
from run_kg_reasoning import reason_over_claim  # noqa: E402


KNOWN_LOCATIONS = {
    "austin",
    "texas",
    "california",
    "florida",
    "oregon",
    "north carolina",
    "united states",
    "america",
    "iran",
    "iraq",
    "washington",
}
ORG_HINTS = {
    "act",
    "administration",
    "agency",
    "association",
    "campaign",
    "care",
    "committee",
    "company",
    "congress",
    "corporation",
    "department",
    "government",
    "group",
    "law",
    "list",
    "party",
    "university",
}
CLASS_WORDS = {
    "city",
    "town",
    "municipality",
    "state",
    "country",
    "nation",
    "person",
    "organization",
    "company",
    "group",
    "president",
    "governor",
    "senator",
    "representative",
    "mayor",
}


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"\s+", " ", value.strip())
    return value


def strip_leading_determiner(value: str) -> str:
    return re.sub(r"^(a|an|the)\s+", "", value.strip(), flags=re.IGNORECASE)


def detect_entity_type(value: str, role: str) -> str:
    text = strip_leading_determiner(clean_text(value))
    lowered = text.lower()
    if not text:
        return "UNKNOWN"
    if role == "object" and lowered in CLASS_WORDS:
        return "UNKNOWN"
    if re.fullmatch(r"\d{4}", text) or re.search(r"\b\d+(\.\d+)?\s*(percent|%)\b", lowered):
        return "DATE" if re.fullmatch(r"\d{4}", text) else "PERCENT"
    if lowered in KNOWN_LOCATIONS:
        return "LOC"
    if any(hint in lowered.split() for hint in ORG_HINTS):
        return "ORG"
    if len(text.split()) >= 2 and all(part[:1].isupper() for part in text.split()[:2]):
        return "PER"
    if text[:1].isupper():
        return "MISC"
    return "UNKNOWN"


def detect_date(claim: str) -> str | None:
    match = re.search(r"\b(18|19|20)\d{2}\b", claim)
    return match.group(0) if match else None


def extraction_confidence(subject: str, relation: str, obj: str, subject_type: str, object_type: str) -> float:
    score = 0.35
    if subject:
        score += 0.2
    if relation:
        score += 0.15
    if obj:
        score += 0.15
    if subject_type != "UNKNOWN":
        score += 0.1
    if object_type != "UNKNOWN":
        score += 0.05
    return round(min(score, 0.92), 3)


def first_title_span(text: str) -> str | None:
    matches = re.findall(r"\b[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*){0,3}\b", text)
    if not matches:
        return None
    return max(matches, key=len)


def extract_live_claim(claim: str, speaker: str = "live-user") -> dict[str, Any]:
    claim = clean_text(claim)
    date = detect_date(claim)
    subject = ""
    relation = ""
    obj = ""

    patterns = [
        (r"^(.+?)\s+(is|are|was|were)\s+(.+)$", "be"),
        (r"^(.+?)\s+(supports?|opposes?|supported|opposed)\s+(.+)$", None),
        (r"^(.+?)\s+(says?|said|claims?|claimed)\s+(.+)$", "say"),
        (r"^(.+?)\s+(agrees?|agreed)\s+with\s+(.+)$", "agree"),
        (r"^(.+?)\s+(voted|votes|vote)\s+(?:for|against|to)?\s*(.+)$", "vote"),
        (r"^(.+?)\s+(was\s+founded|founded|started|began)\s+(?:in\s+)?(.+)$", "founded_in"),
        (r"^(.+?)\s+(has|have|had)\s+(.+)$", "have"),
    ]

    for pattern, fixed_relation in patterns:
        match = re.match(pattern, claim, flags=re.IGNORECASE)
        if match:
            subject = clean_text(match.group(1))
            relation = fixed_relation or clean_text(match.group(2)).lower()
            obj = clean_text(match.group(3))
            break

    if not subject:
        title_span = first_title_span(claim)
        if title_span:
            subject = title_span
            remainder = clean_text(claim.replace(title_span, "", 1))
            relation = "state"
            obj = remainder or claim
        else:
            words = claim.split()
            subject = " ".join(words[: min(4, len(words))])
            relation = "state"
            obj = " ".join(words[min(4, len(words)) :])

    subject = strip_leading_determiner(subject)
    obj = clean_text(obj).strip(" .")
    subject_type = detect_entity_type(subject, "subject")
    object_type = detect_entity_type(obj, "object")
    confidence = extraction_confidence(subject, relation, obj, subject_type, object_type)

    entities = []
    if subject_type != "UNKNOWN":
        entities.append({"word": subject, "type": subject_type, "score": confidence})
    if object_type != "UNKNOWN":
        entities.append({"word": obj, "type": object_type, "score": confidence})

    return {
        "claim_id": "live-claim-00001",
        "raw_claim": claim,
        "label": None,
        "speaker": clean_text(speaker) or "live-user",
        "subject": subject,
        "subject_type": subject_type,
        "relation": relation,
        "object": obj,
        "object_type": object_type,
        "date": date,
        "confidence": confidence,
        "extraction_confidence": confidence,
        "entities": entities,
    }


def link_live_record(record: dict[str, Any], *, online: bool) -> dict[str, Any]:
    import pandas as pd

    df = normalize_input_records([record])
    prior_links = build_prior_links(PROJECT_ROOT / "03_Entity_Linking_KR" / "linked_entities.json")
    return link_claim(
        pd.Series(df.iloc[0]),
        cache={},
        prior_links=prior_links,
        offline=not online,
        sleep_seconds=0.05,
        timeout=8,
    )


def run_live_pipeline(claim: str, *, speaker: str = "live-user", online: bool = False) -> dict[str, Any]:
    extracted = extract_live_claim(claim, speaker=speaker)
    linked = link_live_record(extracted, online=online)
    kg = reason_over_claim(linked)
    final = final_verdict_record({**linked, **kg})
    return {
        "extracted": extracted,
        "linked": linked,
        "kg": kg,
        "final": final,
        "online": online,
    }
