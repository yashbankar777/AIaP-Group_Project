from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from live_pipeline import run_live_pipeline


APP_TITLE = "Misinformation Verifier"
APP_SUBTITLE = "Real-time claim verification with AI reasoning"

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
            max-width: 1200px;
            padding-top: 1rem;
            padding-bottom: 2rem;
        }
        h1 { font-size: 2.2rem; margin-bottom: 0.2rem; }
        h2 { font-size: 1.5rem; margin-top: 1.5rem; margin-bottom: 0.5rem; }
        .subtitle { color: #666; font-size: 1.1rem; margin-bottom: 2rem; }
        .pipeline-stage {
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 1rem;
            background: #f9f9f9;
            text-align: center;
            position: relative;
        }
        .pipeline-stage.active {
            border-color: #247c52;
            background: #f0f9f5;
        }
        .pipeline-stage.done {
            border-color: #247c52;
            background: #e8f5e9;
        }
        .verdict-box {
            border: 3px solid #247c52;
            border-radius: 12px;
            padding: 1.5rem;
            background: #f0f9f5;
            text-align: center;
            margin: 1rem 0;
        }
        .verdict-box.false {
            border-color: #b42318;
            background: #fff0ed;
        }
        .verdict-box.uncertain {
            border-color: #8a5a00;
            background: #fffbf0;
        }
        .verdict-text {
            font-size: 2rem;
            font-weight: 700;
            margin: 0.5rem 0;
        }
        .confidence-text {
            font-size: 0.95rem;
            color: #666;
        }
        .evidence-card {
            border-left: 4px solid #247c52;
            border-radius: 4px;
            background: #f9fafb;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        .badge {
            display: inline-block;
            border-radius: 999px;
            padding: 0.3rem 0.8rem;
            font-weight: 600;
            font-size: 0.85rem;
            margin: 0.2rem 0.2rem 0.2rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def badge(label: str, palette: dict[str, str]) -> str:
    color = palette.get(label, "#666")
    return f'<span class="badge" style="background-color: {color}20; color: {color};">{label.title()}</span>'


def clamp01(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, number))


def render_header(data: dict[str, Any]) -> None:
    """Render hero section with key stats."""
    st.title(APP_TITLE)
    st.markdown(f'<p class="subtitle">{APP_SUBTITLE}</p>', unsafe_allow_html=True)
    
    summary = data["summary"]
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Claims Tested", f"{summary.get('total_claims', len(data['final'])):,}")
    with col2:
        st.metric("✓ True", f"{summary.get('verdict_counts', {}).get('likely true', 0)}")
    with col3:
        st.metric("✗ False", f"{summary.get('verdict_counts', {}).get('likely false', 0)}")
    with col4:
        st.metric("? Uncertain", f"{summary.get('verdict_counts', {}).get('uncertain', 0)}")


def render_verdict_display(final: dict[str, Any], confidence: float) -> None:
    """Render the verdict box prominently."""
    verdict = final.get("final_verdict", "uncertain").lower()
    prob_true = clamp01(final.get("probability_true"))
    prob_false = clamp01(final.get("probability_false"))
    
    verdict_class = verdict.lower() if verdict in ["false", "uncertain"] else "true"
    
    verdict_display = {
        "likely true": "✓ LIKELY TRUE",
        "likely false": "✗ LIKELY FALSE",
        "uncertain": "? UNCERTAIN",
    }.get(verdict, "UNCERTAIN")
    
    st.markdown(
        f"""
        <div class="verdict-box {verdict_class}">
            <div class="verdict-text">{verdict_display}</div>
            <div class="confidence-text">Confidence: {confidence:.1%}</div>
            <div style="margin-top: 0.5rem; font-size: 0.9rem;">
                P(True): {prob_true:.1%} | P(False): {prob_false:.1%}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_pipeline_stages(extracted: dict[str, Any], linked: dict[str, Any], kg: dict[str, Any], final: dict[str, Any]) -> None:
    """Show 5 pipeline stages inline."""
    st.markdown("### Processing Pipeline")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(
            """
            <div class="pipeline-stage done">
            <strong>1. Extraction</strong><br>
            <span style="font-size: 0.8rem;">Triple: S-R-O</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col2:
        st.markdown(
            """
            <div class="pipeline-stage done">
            <strong>2. Linking</strong><br>
            <span style="font-size: 0.8rem;">Entity Resolution</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col3:
        st.markdown(
            """
            <div class="pipeline-stage done">
            <strong>3. KG Reasoning</strong><br>
            <span style="font-size: 0.8rem;">Logic Rules</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col4:
        st.markdown(
            """
            <div class="pipeline-stage done">
            <strong>4. Inference</strong><br>
            <span style="font-size: 0.8rem;">Bayesian Model</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col5:
        st.markdown(
            """
            <div class="pipeline-stage done">
            <strong>5. Verdict</strong><br>
            <span style="font-size: 0.8rem;">Final Decision</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    # Show evidence
    st.markdown("### Evidence & Reasoning")
    
    reasoning = final.get("reasoning", "No reasoning available.")
    kg_evidence = kg.get("evidence", final.get("kg_evidence", "No KG evidence."))
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Bayesian Reasoning**")
        st.markdown(f'<div class="evidence-card">{reasoning}</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("**Knowledge Graph Evidence**")
        st.markdown(f'<div class="evidence-card">{kg_evidence}</div>', unsafe_allow_html=True)
    
    # Expandable details
    with st.expander("📊 Detailed Pipeline Trace"):
        tabs = st.tabs(["Extraction", "Linking", "KG Reasoning", "Final Verdict"])
        
        with tabs[0]:
            st.json(extracted)
        
        with tabs[1]:
            st.json(linked)
        
        with tabs[2]:
            st.json(kg)
        
        with tabs[3]:
            st.json(final)


def render_live_verifier() -> None:
    """Tab 1: Live verification with pipeline visualization."""
    st.subheader("🚀 Test Any Claim Live")
    st.markdown("Enter a claim and watch it flow through our AI reasoning pipeline in real-time.")
    
    example = "Austin is a city that has basically doubled in size every 25 years or so since it was founded."
    claim = st.text_area("Enter your claim:", value=example, height=100, label_visibility="collapsed")
    
    col1, col2 = st.columns(2)
    with col1:
        speaker = st.text_input("Speaker/Source (optional):", "live-user")
    with col2:
        mode = st.selectbox(
            "Entity Linking Mode:",
            ["Offline (Reliable)", "Online (Wikidata)"],
            help="Offline is faster and reliable. Online may find more entities but depends on API availability."
        )
    
    if st.button("Verify Claim", type="primary", use_container_width=True, key="live_verify"):
        if not claim.strip():
            st.warning("⚠️ Please enter a claim to verify.")
            return
        
        with st.spinner("Running pipeline... ⏳"):
            try:
                result = run_live_pipeline(claim, speaker=speaker, online=(mode == "Online (Wikidata)"))
                
                st.markdown("---")
                st.markdown("### Verification Result")
                
                # Display the verdict prominently
                confidence = clamp01(result["final"].get("decision_confidence"))
                render_verdict_display(result["final"], confidence)
                
                # Show pipeline stages
                render_pipeline_stages(
                    result["extracted"],
                    result["linked"],
                    result["kg"],
                    result["final"]
                )
            except Exception as e:
                st.error(f"Pipeline error: {str(e)}")


def render_saved_claims_browser(data: dict[str, Any]) -> None:
    """Tab 2: Browse pre-processed claims."""
    st.subheader("📚 Explore Pre-Processed Claims")
    st.markdown("Browse and inspect 500 claims already verified by our pipeline.")
    
    df = data["df"].copy()
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        verdict_filter = st.selectbox(
            "Filter by verdict:",
            ["All"] + sorted([v for v in df["final_verdict"].unique() if v]),
            key="verdict_select"
        )
    with col2:
        speaker_filter = st.text_input("Filter by speaker:", placeholder="e.g., 'Obama'")
    with col3:
        claim_search = st.text_input("Search claim text:", placeholder="e.g., 'economy'")
    
    # Apply filters
    if verdict_filter != "All":
        df = df[df["final_verdict"] == verdict_filter]
    if speaker_filter:
        df = df[df["speaker"].str.lower().str.contains(speaker_filter.lower(), regex=False, na=False)]
    if claim_search:
        df = df[df["claim"].str.lower().str.contains(claim_search.lower(), regex=False, na=False)]
    
    if df.empty:
        st.info("No claims match your filters.")
        return
    
    # Select a claim to display
    st.markdown(f"**Showing {len(df)} claim(s)**")
    
    display_cols = ["claim_id", "final_verdict", "speaker", "probability_true", "decision_confidence"]
    selected_indices = st.dataframe(
        df[display_cols].head(10),
        use_container_width=True,
        selection_mode="single-row",
        on_select="rerun",
        key="claims_table"
    )
    
    if selected_indices and len(selected_indices.get("selected_rows", [])) > 0:
        idx = selected_indices["selected_rows"][0]
        selected_id = df.iloc[idx]["claim_id"]
        
        final = data["final_by_id"][selected_id]
        linked = data["linked_by_id"][selected_id]
        kg = data["kg_by_id"][selected_id]
        extracted = {
            "claim_id": selected_id,
            "raw_claim": final.get("raw_claim"),
            "subject": linked.get("subject"),
            "relation": linked.get("relation"),
            "object": linked.get("object"),
            "extraction_confidence": linked.get("extraction_confidence"),
        }
        
        st.markdown("---")
        st.markdown(f"## {final.get('raw_claim', '')}")
        
        confidence = clamp01(final.get("decision_confidence"))
        render_verdict_display(final, confidence)
        
        render_pipeline_stages(extracted, linked, kg, final)


def render_batch_processor(data: dict[str, Any]) -> None:
    """Tab 3: Batch process and export claims."""
    st.subheader("📤 Batch Process & Export")
    st.markdown("Upload a CSV file with claims to process in batch and export results.")
    
    # Quick reference
    st.markdown("**CSV Format:** Must have a `claim` column. Optional: `speaker` column.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Example:**")
        example_csv = """claim,speaker
The Earth is round.,NASA
Water boils at 100 degrees Celsius.,Science
Austin has doubled in size every 25 years.,Local News"""
        st.code(example_csv, language="csv")
    
    with col2:
        st.markdown("**Or download sample:**")
        sample_df = data["df"][["claim", "speaker"]].head(5).copy()
        csv_buffer = io.StringIO()
        sample_df.to_csv(csv_buffer, index=False)
        
        st.download_button(
            label="📥 Download Sample CSV",
            data=csv_buffer.getvalue(),
            file_name="sample_claims.csv",
            mime="text/csv"
        )
    
    # File uploader
    uploaded_file = st.file_uploader("Upload CSV file:", type=["csv"])
    
    if uploaded_file is not None:
        try:
            df_upload = pd.read_csv(uploaded_file)
            
            if "claim" not in df_upload.columns:
                st.error("CSV must have a 'claim' column.")
                return
            
            st.markdown(f"**Loaded {len(df_upload)} claim(s)**")
            st.dataframe(df_upload.head(3), use_container_width=True)
            
            if st.button("Process Claims", type="primary", key="process_batch"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                results = []
                
                for idx, row in df_upload.iterrows():
                    claim = row.get("claim", "")
                    speaker = row.get("speaker", "uploaded-user")
                    
                    if not claim.strip():
                        continue
                    
                    status_text.text(f"Processing {idx + 1}/{len(df_upload)}... {claim[:50]}...")
                    
                    try:
                        result = run_live_pipeline(claim, speaker=speaker, online=False)
                        results.append({
                            "claim": claim,
                            "speaker": speaker,
                            "verdict": result["final"].get("final_verdict", "uncertain"),
                            "probability_true": float(result["final"].get("probability_true", 0)),
                            "probability_false": float(result["final"].get("probability_false", 0)),
                            "confidence": float(result["final"].get("decision_confidence", 0)),
                        })
                    except Exception as e:
                        results.append({
                            "claim": claim,
                            "speaker": speaker,
                            "verdict": "error",
                            "probability_true": 0,
                            "probability_false": 0,
                            "confidence": 0,
                        })
                    
                    progress_bar.progress((idx + 1) / len(df_upload))
                
                progress_bar.empty()
                status_text.empty()
                
                results_df = pd.DataFrame(results)
                
                st.success(f"✓ Processed {len(results)} claims successfully!")
                
                # Show summary stats
                col1, col2, col3 = st.columns(3)
                col1.metric("Likely True", len(results_df[results_df["verdict"] == "likely true"]))
                col2.metric("Likely False", len(results_df[results_df["verdict"] == "likely false"]))
                col3.metric("Uncertain", len(results_df[results_df["verdict"] == "uncertain"]))
                
                st.markdown("**Results:**")
                st.dataframe(results_df, use_container_width=True)
                
                # Export button
                csv_export = io.StringIO()
                results_df.to_csv(csv_export, index=False)
                
                st.download_button(
                    label="📥 Download Results CSV",
                    data=csv_export.getvalue(),
                    file_name="verification_results.csv",
                    mime="text/csv"
                )
        
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")


def render_live_mode() -> None:
    """Legacy function for compatibility."""
    render_live_verifier()


def render_saved_mode(data: dict[str, Any]) -> None:
    """Legacy function for compatibility."""
    render_saved_claims_browser(data)


def render_similarity_mode(data: dict[str, Any]) -> None:
    """Legacy function removed - replaced with batch processor."""
    pass


def main() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    inject_css()
    
    # Sidebar info
    with st.sidebar:
        st.markdown("### 📋 About")
        st.markdown(
            """
            This app demonstrates a complete misinformation verification pipeline combining:
            - **NLP** claim extraction
            - **Entity linking** via KG
            - **Symbolic reasoning** with rules
            - **Bayesian inference** for credibility
            - **Responsible AI** considerations
            
            Built for the AIaP Group Project.
            """
        )
        st.markdown("---")
        st.markdown("**📊 Data Source:** LIAR Dataset (test set)")
    
    # Load data
    data = load_processed_data()
    if data["df"].empty:
        st.error("❌ No project outputs found. Run the pipeline first.")
        st.stop()
    
    # Header
    render_header(data)
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs([
        "🚀 Live Verifier",
        "📚 Browse Claims",
        "📤 Batch Export"
    ])
    
    with tab1:
        render_live_verifier()
    
    with tab2:
        render_saved_claims_browser(data)
    
    with tab3:
        render_batch_processor(data)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #999; font-size: 0.85rem;'>"
        "⚖️ Misinformation Verifier | AI Assessment Group Project"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
