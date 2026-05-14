import json
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Misinformation Verification System",
    page_icon="🔍",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root {
        --bg: #f6f8fb;
        --panel: #ffffff;
        --text: #1f2937;
        --muted: #64748b;
        --border: #dce3ec;
        --blue: #2563eb;
        --blue-soft: #dbeafe;
        --green: #16a34a;
        --green-soft: #dcfce7;
        --red: #dc2626;
        --red-soft: #fee2e2;
        --amber: #d97706;
        --amber-soft: #fef3c7;
        --purple: #7c3aed;
        --purple-soft: #ede9fe;
        --muted-green: #5f9f73;
        --muted-green-soft: #f1f8f3;
        --muted-red: #b96464;
        --muted-red-soft: #fbf1f1;
        --muted-amber: #b98235;
        --muted-amber-soft: #fff8ec;
    }

    * {
        box-sizing: border-box;
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(37, 99, 235, 0.08), transparent 32rem),
            var(--bg);
        color: var(--text);
    }

    .block-container,
    [data-testid="stMainBlockContainer"] {
        max-width: 1180px;
        margin-left: auto;
        margin-right: auto;
        padding-left: 2rem;
        padding-right: 2rem;
        padding-top: 1.6rem;
        padding-bottom: 3rem;
    }

    h1 {
        color: var(--text);
        font-weight: 800;
        text-align: center;
    }

    h2, h3 {
        color: var(--text);
    }

    hr {
        border-color: var(--border);
    }

    div[data-testid="stSelectbox"] label {
        color: var(--text);
        font-weight: 700;
    }

    div[data-testid="stTextInput"] label {
        color: var(--text);
        font-weight: 700;
    }

    div[data-testid="stTextInput"] input {
        background: #eef3f8;
        border: 1px solid #e3e9f1;
        border-radius: 8px;
        min-height: 3.25rem;
        color: var(--text);
    }

    div[data-testid="stTextInput"] input::placeholder {
        color: var(--muted);
        opacity: 1;
    }

    div[data-testid="stTextInput"] input::-webkit-input-placeholder {
        color: var(--muted);
        opacity: 1;
    }

    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background: #eef3f8;
        border: 1px solid #e3e9f1;
        border-radius: 8px;
        min-height: 3.5rem;
        color: var(--text);
    }

    .metric-card,
    .info-card,
    .stage-card,
    .verdict-card,
    .explanation-card {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 8px;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
    }

    .metric-card {
        min-height: 8.5rem;
        padding: 1.35rem 1.45rem;
        border-top: 5px solid var(--blue);
    }

    .metric-card.green {
        border-top-color: var(--green);
    }

    .metric-card.amber {
        border-top-color: var(--amber);
    }

    .metric-label,
    .stage-caption,
    .info-label {
        color: var(--muted);
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .metric-value {
        color: var(--text);
        font-size: 2.35rem;
        font-weight: 800;
        line-height: 1.1;
        margin-top: 0.65rem;
    }

    .metric-note {
        color: var(--muted);
        font-size: 0.9rem;
        margin-top: 0.35rem;
    }

    .section-spacer {
        height: 1.2rem;
    }

    .small-spacer {
        height: 0.35rem;
    }

    .info-card {
        min-height: 15.25rem;
        padding: 1.25rem 1.35rem;
        border-top: 4px solid var(--blue);
    }

    .info-card.claim {
        border-top-color: var(--blue);
    }

    .claim-display-card {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 8px;
        border-top: 5px solid var(--blue);
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
        padding: 1.1rem 1.35rem 1.2rem;
    }

    .info-card.context {
        border-top-color: var(--amber);
    }

    .info-title,
    .stage-title {
        color: var(--text);
        font-size: 1.02rem;
        font-weight: 800;
        margin-bottom: 0.75rem;
    }

    .claim-text {
        color: var(--text);
        font-size: 1.05rem;
        line-height: 1.5;
    }

    .context-row {
        border-top: 1px solid #edf2f7;
        padding-top: 0.7rem;
        margin-top: 0.7rem;
    }

    .context-value {
        color: var(--text);
        font-size: 1.05rem;
        font-weight: 800;
        margin-top: 0.15rem;
    }

    .stage-card {
        min-height: 15rem;
        padding: 1.25rem;
        border-top: 5px solid var(--blue);
    }

    .claim-entry-note {
        color: var(--muted);
        font-size: 0.92rem;
        margin-top: -0.3rem;
        margin-bottom: 1rem;
    }

    .pipeline-flow {
        margin-top: 1rem;
    }

    .pipeline-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 1rem;
        margin-bottom: 0.75rem;
    }

    .pipeline-card,
    .fusion-card,
    .final-flow-card {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 8px;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
        padding: 1.15rem 1.25rem;
    }

    .pipeline-card {
        border-top: 5px solid var(--blue);
        min-height: 12rem;
    }

    .pipeline-card.signal-true {
        background: var(--muted-green-soft);
        border-top-color: var(--muted-green);
    }

    .pipeline-card.signal-false {
        background: var(--muted-red-soft);
        border-top-color: var(--muted-red);
    }

    .pipeline-card.signal-unverifiable {
        background: var(--muted-amber-soft);
        border-top-color: var(--muted-amber);
    }

    .pipeline-card-title {
        color: var(--text);
        font-size: 1.02rem;
        font-weight: 850;
        margin-bottom: 0.85rem;
    }

    .pipeline-card-value {
        align-items: center;
        color: var(--text);
        display: flex;
        font-size: 1.55rem;
        font-weight: 900;
        gap: 0.55rem;
        line-height: 1.15;
        margin: 0.45rem 0;
    }

    .status-dot {
        border-radius: 50%;
        display: inline-block;
        flex: 0 0 auto;
        height: 1.1rem;
        width: 1.1rem;
    }

    .status-dot.true {
        background: var(--muted-green);
    }

    .status-dot.false {
        background: var(--muted-red);
    }

    .status-dot.unverifiable {
        background: var(--muted-amber);
    }

    .status-text.true {
        color: #356f46;
    }

    .status-text.false {
        color: #8f3f3f;
    }

    .status-text.unverifiable {
        color: #805916;
    }

    .pipeline-card-detail {
        color: var(--muted);
        font-size: 0.92rem;
        line-height: 1.45;
        margin-top: 0.55rem;
    }

    .flow-arrow {
        color: var(--muted);
        font-size: 1.7rem;
        font-weight: 900;
        text-align: center;
        margin: 0.3rem 0;
    }

    .fusion-card {
        border-top: 6px solid var(--blue);
        margin: 0 auto;
        max-width: 760px;
        text-align: center;
    }

    .fusion-title {
        color: var(--blue);
        font-size: 1.25rem;
        font-weight: 900;
        margin-bottom: 0.55rem;
    }

    .fusion-probs {
        display: flex;
        gap: 1rem;
        justify-content: center;
        margin-top: 0.9rem;
    }

    .prob-chip {
        background: #eef3f8;
        border: 1px solid #dbe4ee;
        border-radius: 999px;
        color: var(--text);
        font-weight: 800;
        padding: 0.45rem 0.75rem;
    }

    .final-flow-card {
        border-top: 6px solid var(--green);
        margin: 0 auto;
        max-width: 760px;
        text-align: center;
    }

    .final-flow-card.false {
        border-top-color: var(--red);
    }

    .final-flow-card.unverifiable {
        border-top-color: var(--amber);
    }

    .stage-card.true {
        border-top-color: var(--green);
    }

    .stage-card.false {
        border-top-color: var(--red);
    }

    .stage-card.unverifiable {
        border-top-color: var(--amber);
    }

    .stage-title {
        color: var(--blue);
        margin-bottom: 1rem;
    }

    .verdict-pill {
        align-items: center;
        border-radius: 999px;
        display: inline-flex;
        font-size: 0.95rem;
        font-weight: 900;
        gap: 0.4rem;
        padding: 0.5rem 0.75rem;
    }

    .verdict-pill.true {
        background: var(--green-soft);
        color: #166534;
    }

    .verdict-pill.false {
        background: var(--red-soft);
        color: #991b1b;
    }

    .verdict-pill.unverifiable {
        background: var(--amber-soft);
        color: #92400e;
    }

    .confidence-row {
        align-items: baseline;
        display: flex;
        justify-content: space-between;
        margin-top: 1.15rem;
    }

    .confidence-value {
        color: var(--text);
        font-size: 1.25rem;
        font-weight: 900;
    }

    .progress-track {
        background: #e8eef5;
        border-radius: 999px;
        height: 0.75rem;
        margin: 0.8rem 0 1.15rem;
        overflow: hidden;
    }

    .progress-fill {
        border-radius: 999px;
        height: 100%;
    }

    .progress-fill.true {
        background: var(--green);
    }

    .progress-fill.false {
        background: var(--red);
    }

    .progress-fill.unverifiable {
        background: var(--amber);
    }

    .pipeline-note {
        background: #fff7ed;
        border: 1px solid #fed7aa;
        border-left: 5px solid var(--amber);
        border-radius: 8px;
        color: #7c2d12;
        font-weight: 650;
        margin: 0.75rem 0 1.25rem;
        padding: 0.9rem 1.05rem;
    }

    .verdict-card {
        min-height: 9.5rem;
        padding: 1.25rem 1.35rem;
        border-top: 5px solid var(--red);
    }

    .metric-card.final-confidence {
        min-height: 9.5rem;
    }

    .verdict-card.true {
        border-top-color: var(--green);
    }

    .verdict-card.false {
        border-top-color: var(--red);
    }

    .final-label {
        font-size: 2rem;
        font-weight: 900;
        line-height: 1.1;
        margin-top: 0.55rem;
    }

    .final-label.true {
        color: var(--green);
    }

    .final-label.false {
        color: var(--red);
    }

    .final-label.unverifiable {
        color: var(--amber);
    }

    .explanation-card {
        border-left: 5px solid var(--blue);
        margin-top: 1rem;
        padding: 1.15rem 1.25rem;
    }

    .explanation-card ul {
        margin-bottom: 0;
    }

    @media (max-width: 768px) {
        .block-container,
        [data-testid="stMainBlockContainer"] {
            max-width: 100%;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .pipeline-grid {
            grid-template-columns: 1fr;
        }

        .fusion-probs {
            flex-direction: column;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


DATA_FILE = Path(__file__).parent / "final_verdicts.json"


@st.cache_data(show_spinner=False)
def load_verdicts() -> pd.DataFrame:
    with DATA_FILE.open("r", encoding="utf-8") as file:
        records = json.load(file)

    df = pd.DataFrame(records)
    required_columns = {
        "claim_id",
        "raw_claim",
        "speaker",
        "speaker_lie_rate",
        "roberta_pred",
        "roberta_true_prob",
        "kg_verdict",
        "kg_confidence",
        "p_true",
        "p_false",
        "final_verdict",
        "final_confidence",
    }
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"{DATA_FILE.name} is missing required columns: {missing}")

    return df


def clamp_probability(value: float) -> float:
    return max(0.0, min(float(value), 1.0))


def format_percent(value: float) -> str:
    return f"{clamp_probability(value):.1%}"


def verdict_badge(verdict: str, true_probability: float | None = None) -> tuple[str, str, str]:
    normalized = str(verdict).strip().lower()
    if normalized in {"true", "likely_true"}:
        return "true", "🟢", normalized.replace("_", " ").upper()
    if normalized in {"false", "likely_false"}:
        return "false", "🔴", normalized.replace("_", " ").upper()
    if normalized == "unverifiable":
        return "unverifiable", "🟡", "UNVERIFIABLE"
    if true_probability is not None and true_probability >= 0.5:
        return "true", "🟢", "TRUE"
    if true_probability is not None:
        return "false", "🔴", "FALSE"
    return "unverifiable", "🟡", normalized.replace("_", " ").upper()


def find_processed_claim(verdicts: pd.DataFrame, claim_text: str) -> pd.Series | None:
    query = claim_text.strip().lower()
    if not query:
        return None

    normalized_claims = verdicts["raw_claim"].astype(str).str.lower()
    exact_matches = verdicts[normalized_claims == query]
    if not exact_matches.empty:
        return exact_matches.iloc[0]

    contains_matches = verdicts[normalized_claims.str.contains(query, na=False, regex=False)]
    if not contains_matches.empty:
        return contains_matches.iloc[0]

    token_matches = verdicts[normalized_claims.apply(lambda claim: all(token in claim for token in query.split()))]
    if not token_matches.empty:
        return token_matches.iloc[0]

    return None


def render_pipeline_flow(selected: pd.Series) -> None:
    roberta_true_prob = clamp_probability(selected["roberta_true_prob"])
    roberta_verdict = "true" if roberta_true_prob >= 0.5 else "false"
    roberta_confidence = max(roberta_true_prob, 1 - roberta_true_prob)
    roberta_status, _, roberta_label = verdict_badge(roberta_verdict)

    kg_confidence = clamp_probability(selected["kg_confidence"])
    kg_status, _, kg_label = verdict_badge(selected["kg_verdict"])

    speaker_lie_rate = clamp_probability(selected["speaker_lie_rate"])
    prior_status = "true" if speaker_lie_rate < 0.5 else "false"
    prior_label = "LOW RISK" if speaker_lie_rate < 0.5 else "HIGH RISK"
    p_true = clamp_probability(selected["p_true"])
    p_false = clamp_probability(selected["p_false"])
    final_confidence = clamp_probability(selected["final_confidence"])
    final_status, final_icon, final_label = verdict_badge(selected["final_verdict"])

    st.markdown(
        f"""
        <div class="pipeline-flow">
            <div class="pipeline-grid">
                <div class="pipeline-card signal-{roberta_status}">
                    <div class="pipeline-card-title">1. Text Model Evidence</div>
                    <div class="metric-label">RoBERTa</div>
                    <div class="pipeline-card-value">
                        <span class="status-dot {roberta_status}"></span>
                        <span class="status-text {roberta_status}">{escape(roberta_label)}</span>
                    </div>
                    <div class="pipeline-card-detail">
                        Text signal confidence: {format_percent(roberta_confidence)}<br>
                        True probability: {format_percent(roberta_true_prob)}
                    </div>
                </div>
                <div class="pipeline-card signal-{kg_status}">
                    <div class="pipeline-card-title">2. Knowledge Graph Evidence</div>
                    <div class="metric-label">Structured reasoning</div>
                    <div class="pipeline-card-value">
                        <span class="status-dot {kg_status}"></span>
                        <span class="status-text {kg_status}">{escape(kg_label)}</span>
                    </div>
                    <div class="pipeline-card-detail">
                        KG confidence: {format_percent(kg_confidence)}<br>
                        Uses structured claim evidence where available.
                    </div>
                </div>
                <div class="pipeline-card signal-{prior_status}">
                    <div class="pipeline-card-title">3. Speaker Prior</div>
                    <div class="metric-label">Historical speaker credibility</div>
                    <div class="pipeline-card-value">
                        <span class="status-dot {prior_status}"></span>
                        <span class="status-text {prior_status}">{format_percent(speaker_lie_rate)} {prior_label}</span>
                    </div>
                    <div class="pipeline-card-detail">
                        Speaker: {escape(str(selected["speaker"]))}<br>
                        Historical false-rate used as the Bayesian prior.
                    </div>
                </div>
            </div>
            <div class="flow-arrow">↓</div>
            <div class="fusion-card">
                <div class="fusion-title">4. Bayesian Fusion</div>
                <div class="pipeline-card-detail">
                    Combines text evidence, knowledge graph evidence, and speaker prior into a posterior probability.
                </div>
                <div class="fusion-probs">
                    <div class="prob-chip">P(True): {p_true:.4f}</div>
                    <div class="prob-chip">P(False): {p_false:.4f}</div>
                </div>
            </div>
            <div class="flow-arrow">↓</div>
            <div class="final-flow-card {final_status}">
                <div class="metric-label">Final verdict</div>
                <div class="final-label {final_status}">{final_icon} {escape(final_label)}</div>
                <div class="pipeline-card-detail">Confidence: {format_percent(final_confidence)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    try:
        verdicts = load_verdicts()
    except Exception as exc:
        st.error(f"Could not load verdict data: {exc}")
        st.stop()

    st.title("🔍 Misinformation Verification System")
    st.divider()

    st.markdown("## Verify a Claim")
    claim_text = st.text_input(
        "Claim text",
        placeholder="Write or paste a claim here...",
        label_visibility="collapsed",
    ).strip()

    if not claim_text:
        st.info("Write or paste a claim from the processed dataset to view its pipeline result.")
        st.stop()

    selected = find_processed_claim(verdicts, claim_text)
    if selected is None:
        st.warning("No saved verdict matched that claim. Try pasting the exact processed claim or a shorter phrase.")
        st.stop()

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="claim-display-card">
            <div class="info-title">Claim Being Verified</div>
            <div class="claim-text">{escape(str(selected["raw_claim"]))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Pipeline Flow")
    render_pipeline_flow(selected)


if __name__ == "__main__":
    main()
