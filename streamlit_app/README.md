# Streamlit Verification App

This folder contains the tracked Streamlit app used to test the implemented
misinformation verification pipeline.

Recommended entry point:

```bash
streamlit run streamlit_app/app.py
```

The app supports two test paths:

- live claim test: enter a new claim and run extraction, entity linking, KG
  reasoning, and Bayesian inference
- saved claim test: inspect the already processed 500-claim project handoff

The live test uses a lightweight extraction helper that emits the same schema as
module 01, then calls the implemented modules 03, 04, and 05.

The app also uses the project outputs for reliable saved-claim testing:

- `05_Bayesian_Inference/final_verdicts.json`
- `05_Bayesian_Inference/final_verdict_summary.json`
- `06_GenAI_Responsible_AI/responsible_ai_summary.json`
- `report_assets/tables/*.csv`

The app should present `uncertain` verdicts as responsible abstentions, not as
true or false claims.

Current app features:

- live new-claim testing with offline or online Wikidata entity linking
- saved processed-claim testing with full pipeline trace
- similarity search against processed claims
- final probabilities, KG evidence, and raw pipeline records
