from __future__ import annotations

import json
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from live_pipeline import run_live_pipeline


APP_TITLE = "Live Misinformation Verifier"
VERDICT_COLORS = {
    "likely true": "#247c52",
    "likely false": "#b42318",
    "uncertain": "#8a5a00",
}
KG_COLORS = {
    "supported": "#247c52",
    "contradicted": "#b42318",
    "unknown": "#667085",
}


def project_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in [current.parent, *current.parents]:
        if (candidate / "LIAR_dataset").exists() and (candidate / "05_Bayesian_Inference").exists():
            return candidate
    return current.parents[1]


ROOT = project_root()


@st.cache_data(show_spinner=False)
def load_json(relative_path: str, default: Any) -> Any:
    path = ROOT / relative_path
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def load_processed_data() -> dict[str, Any]:
    final = load_json("05_Bayesian_Inference/final_verdicts.json", [])
    linked = load_json("03_Entity_Linking_KR/linked_entities.json", [])
    kg = load_json("04_KG_Reasoning/kg_results.json", [])
    summary = load_json("05_Bayesian_Inference/final_verdict_summary.json", {})

    linked_by_id = {record.get("claim_id"): record for record in linked}
    kg_by_id = {record.get("claim_id"): record for record in kg}
    final_by_id = {record.get("claim_id"): record for record in final}

    rows = []
    for record in final:
        rows.append(
            {
                "claim_id": record.get("claim_id"),
                "claim": record.get("raw_claim", ""),
                "speaker": record.get("speaker") or "unknown",
                "reference_label": record.get("reference_label"),
                "final_verdict": record.get("final_verdict", "uncertain"),
                "kg_status": record.get("kg_status", "unknown"),
                "probability_true": float(record.get("probability_true") or 0),
                "probability_false": float(record.get("probability_false") or 0),
                "decision_confidence": float(record.get("decision_confidence") or 0),
            }
        )

    return {
        "final": final,
        "linked_by_id": linked_by_id,
        "kg_by_id": kg_by_id,
        "final_by_id": final_by_id,
        "summary": summary,
        "df": pd.DataFrame(rows),
    }


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1180px;
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }
        h1, h2, h3 { letter-spacing: 0; }
        .muted { color: #667085; font-size: 0.9rem; }
        .panel {
            border: 1px solid #d0d5dd;
            border-radius: 8px;
            padding: 1rem;
            background: #ffffff;
        }
        .claim-box {
            border: 1px solid #d0d5dd;
            border-radius: 8px;
            padding: 1rem;
            background: #fcfcfd;
        }
        .badge {
            display: inline-block;
            border: 1px solid rgba(0,0,0,0.1);
            border-radius: 999px;
            padding: 0.22rem 0.58rem;
            font-weight: 700;
            background: #f9fafb;
        }
        .stage {
            border: 1px solid #d0d5dd;
            border-radius: 8px;
            padding: 0.85rem;
            min-height: 130px;
            background: #fff;
        }
        .evidence {
            border-left: 4px solid #475467;
            border-radius: 4px;
            background: #f9fafb;
            padding: 0.75rem 0.9rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def badge(label: str, palette: dict[str, str]) -> str:
    color = palette.get(label, "#475467")
    return f'<span class="badge" style="color:{color};">{label.title()}</span>'


def clamp01(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, number))


def score_similarity(query: str, claim: str) -> float:
    query = query.lower().strip()
    claim = claim.lower().strip()
    if not query:
        return 0.0
    if query in claim:
        return 1.0
    return SequenceMatcher(None, query, claim).ratio()


def render_header(data: dict[str, Any]) -> None:
    summary = data["summary"]
    st.title(APP_TITLE)
    st.markdown(
        "Enter a claim and test it through the implemented project pipeline, or inspect a processed claim "
        "from the saved project run."
    )
    cols = st.columns(4)
    cols[0].metric("Processed test claims", f"{summary.get('total_claims', len(data['final'])):,}")
    cols[1].metric("Likely true", f"{summary.get('verdict_counts', {}).get('likely true', 0)}")
    cols[2].metric("Likely false", f"{summary.get('verdict_counts', {}).get('likely false', 0)}")
    cols[3].metric("Uncertain", f"{summary.get('verdict_counts', {}).get('uncertain', 0)}")
    st.info(
        "Hybrid mode: saved claims are reliable and reproducible; live claims run the same downstream project modules "
        "after a lightweight extraction step."
    )


def render_probabilities(final: dict[str, Any]) -> None:
    true_prob = clamp01(final.get("probability_true"))
    false_prob = clamp01(final.get("probability_false"))
    st.progress(true_prob, text=f"P(true): {true_prob:.3f}")
    st.progress(false_prob, text=f"P(false): {false_prob:.3f}")
    cols = st.columns(3)
    cols[0].metric("Prior true", f"{clamp01(final.get('probability_prior_true')):.3f}")
    cols[1].metric("Evidence weight", f"{clamp01(final.get('evidence_weight')):.3f}")
    cols[2].metric("Decision confidence", f"{clamp01(final.get('decision_confidence')):.3f}")


def render_trace(extracted: dict[str, Any], linked: dict[str, Any], kg: dict[str, Any], final: dict[str, Any]) -> None:
    st.markdown("### Verdict")
    st.markdown(
        f"""
        <div class="claim-box">
        <div class="muted">{final.get('claim_id', extracted.get('claim_id'))}</div>
        <h3>{final.get('raw_claim') or extracted.get('raw_claim')}</h3>
        {badge(final.get('final_verdict', 'uncertain'), VERDICT_COLORS)}
        &nbsp;
        {badge(kg.get('kg_status', 'unknown'), KG_COLORS)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    left, right = st.columns([1, 1])
    with left:
        st.markdown("#### Bayesian result")
        render_probabilities(final)
    with right:
        st.markdown("#### Explanation")
        st.markdown(f'<div class="evidence">{final.get("reasoning", "No reasoning available.")}</div>', unsafe_allow_html=True)

    st.markdown("### Pipeline Trace")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""
            <div class="stage">
            <strong>Claim extraction</strong><br>
            <span class="muted">Subject</span><br>{extracted.get('subject') or 'not extracted'}<br>
            <span class="muted">Relation</span><br>{extracted.get('relation') or 'not extracted'}<br>
            <span class="muted">Object</span><br>{extracted.get('object') or 'not extracted'}<br>
            <span class="muted">Confidence</span><br>{clamp01(extracted.get('extraction_confidence') or extracted.get('confidence')):.3f}
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="stage">
            <strong>Entity linking</strong><br>
            <span class="muted">Subject KG</span><br>{linked.get('subject_kg_label') or linked.get('subject_kg_id') or 'not linked'}<br>
            <span class="muted">Object KG</span><br>{linked.get('object_kg_label') or linked.get('object_kg_id') or 'not linked'}<br>
            <span class="muted">Confidence</span><br>{clamp01(linked.get('linking_confidence')):.3f}
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="stage">
            <strong>KG reasoning</strong><br>
            {badge(kg.get('kg_status', 'unknown'), KG_COLORS)}<br><br>
            <span class="muted">Rule</span><br>{kg.get('reasoning_rule') or 'none'}<br>
            <span class="muted">Confidence</span><br>{clamp01(kg.get('kg_confidence')):.3f}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("#### KG evidence")
    st.markdown(f'<div class="evidence">{kg.get("evidence") or final.get("kg_evidence") or "No KG evidence."}</div>', unsafe_allow_html=True)

    with st.expander("Raw pipeline records"):
        tabs = st.tabs(["Extracted", "Linked", "KG", "Final"])
        tabs[0].json(extracted)
        tabs[1].json(linked)
        tabs[2].json(kg)
        tabs[3].json(final)


def render_live_mode() -> None:
    st.subheader("Test a New Claim Live")
    st.caption("Runs a typed claim through extraction, entity linking, KG reasoning, and Bayesian inference.")

    example = "Austin is a city that has basically doubled in size every 25 years or so since it was founded."
    claim = st.text_area("Claim", value=example, height=120)
    speaker = st.text_input("Speaker or source", value="live-user")
    mode = st.radio(
        "Entity-linking mode",
        ["Reliable offline mode", "Online Wikidata mode"],
        horizontal=True,
        help="Offline uses manual/prior links only. Online may find new Wikidata entities but depends on internet/API availability.",
    )
    online = mode == "Online Wikidata mode"

    if st.button("Run verification", type="primary", use_container_width=True):
        if not claim.strip():
            st.warning("Enter a claim first.")
            return
        with st.spinner("Running the project pipeline..."):
            result = run_live_pipeline(claim, speaker=speaker, online=online)
        render_trace(result["extracted"], result["linked"], result["kg"], result["final"])


def option_label(row: pd.Series) -> str:
    claim = row["claim"]
    if len(claim) > 90:
        claim = claim[:87] + "..."
    return f"{row['claim_id']} | {row['final_verdict']} | {claim}"


def render_saved_mode(data: dict[str, Any]) -> None:
    st.subheader("Test Saved Project Claims")
    st.caption("Uses the already processed 500-claim handoff for a reliable demo path.")

    df = data["df"].copy()
    col1, col2 = st.columns([1, 1])
    with col1:
        verdict = st.selectbox("Verdict", ["all", *sorted(df["final_verdict"].unique())])
    with col2:
        query = st.text_input("Search processed claims", "")
    if verdict != "all":
        df = df[df["final_verdict"] == verdict]
    if query.strip():
        needle = query.lower().strip()
        df = df[
            df["claim"].str.lower().str.contains(needle, regex=False)
            | df["speaker"].str.lower().str.contains(needle, regex=False)
            | df["claim_id"].str.lower().str.contains(needle, regex=False)
        ]

    if df.empty:
        st.warning("No processed claims match that filter.")
        return

    supported = df[df["kg_status"] == "supported"]
    default_id = supported.iloc[0]["claim_id"] if not supported.empty else df.iloc[0]["claim_id"]
    labels = [option_label(row) for _, row in df.iterrows()]
    default_index = df.index[df["claim_id"] == default_id].tolist()[0] if default_id in df["claim_id"].values else 0
    selected = st.selectbox("Processed claim", labels, index=default_index)
    selected_id = df.iloc[labels.index(selected)]["claim_id"]

    final = data["final_by_id"][selected_id]
    linked = data["linked_by_id"][selected_id]
    kg = data["kg_by_id"][selected_id]
    extracted = {
        "claim_id": selected_id,
        "raw_claim": final.get("raw_claim"),
        "subject": linked.get("subject"),
        "subject_type": linked.get("subject_type"),
        "relation": linked.get("relation"),
        "object": linked.get("object"),
        "object_type": linked.get("object_type"),
        "extraction_confidence": linked.get("extraction_confidence"),
    }
    render_trace(extracted, linked, kg, final)


def render_similarity_mode(data: dict[str, Any]) -> None:
    st.subheader("Find Similar Processed Claims")
    st.caption("Useful when a typed claim is close to one of the 500 claims already processed by the project.")
    claim = st.text_area("Claim to compare", height=100)
    if not claim.strip():
        st.info("Paste a claim to find similar processed examples.")
        return
    df = data["df"].copy()
    df["similarity"] = df["claim"].apply(lambda text: score_similarity(claim, text))
    st.dataframe(
        df.sort_values("similarity", ascending=False)[
            ["claim_id", "similarity", "final_verdict", "kg_status", "probability_true", "speaker", "claim"]
        ].head(8),
        hide_index=True,
        use_container_width=True,
    )


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon=":material/fact_check:", layout="wide")
    inject_css()
    data = load_processed_data()
    if data["df"].empty:
        st.error("No project outputs found. Run the pipeline first.")
        st.stop()

    render_header(data)
    tabs = st.tabs(["Live Claim Test", "Saved Claim Test", "Similarity Search"])
    with tabs[0]:
        render_live_mode()
    with tabs[1]:
        render_saved_mode(data)
    with tabs[2]:
        render_similarity_mode(data)


if __name__ == "__main__":
    main()
