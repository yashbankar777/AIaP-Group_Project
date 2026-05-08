# Project Validation Report

Date: 2026-05-09

This report records the consistency checks completed before moving into the
Streamlit demo and presentation phase.

## Validation Summary

Status: ready for Streamlit demo development.

The numbered project structure is consistent with the root README:

```text
01_Claim_Extraction/
02_Problem_Dataset_EDA/
03_Entity_Linking_KR/
04_KG_Reasoning/
05_Bayesian_Inference/
06_GenAI_Responsible_AI/
shared/
report_assets/
docs/
LIAR_dataset/
streamlit_app/
```

The main pipeline handoff is valid:

```text
01 extracted triples: 500 records
03 linked entities:   500 records
04 KG results:        500 records
05 final verdicts:    500 records
```

Claim IDs match from `03_Entity_Linking_KR` through
`05_Bayesian_Inference`, and the required schema fields are present in each
handoff file.

## Fixes Applied

- Replaced the hard-coded local LIAR dataset path in the claim extraction
  notebook with project-root-relative path detection.
- Updated generated summaries to use repository-relative paths instead of
  machine-specific `/Users/...` paths.
- Added `streamlit>=1.36` to `requirements.txt` for the upcoming demo app.
- Updated `.gitignore` so only legacy root-level Streamlit files are ignored.
  A tracked app can now be added under a folder such as `streamlit_app/app.py`.
- Normalized the new `05` and `06` notebooks so Jupyter no longer warns about
  missing cell IDs.

## Verification Commands Run

```bash
/opt/anaconda3/bin/python 02_Problem_Dataset_EDA/run_eda.py
/opt/anaconda3/bin/python 04_KG_Reasoning/run_kg_reasoning.py
python3 05_Bayesian_Inference/run_bayesian_inference.py
python3 06_GenAI_Responsible_AI/run_responsible_ai_analysis.py
python3 -m compileall 05_Bayesian_Inference/run_bayesian_inference.py 06_GenAI_Responsible_AI/run_responsible_ai_analysis.py
/opt/anaconda3/bin/python -m py_compile 02_Problem_Dataset_EDA/run_eda.py 03_Entity_Linking_KR/run_entity_linking.py 04_KG_Reasoning/run_kg_reasoning.py
jupyter nbconvert --to notebook --execute 05_Bayesian_Inference/bayesian_inference.ipynb --output /private/tmp/05_bayesian_inference_executed.ipynb --ExecutePreprocessor.timeout=120
jupyter nbconvert --to notebook --execute 06_GenAI_Responsible_AI/genai_responsible_ai.ipynb --output /private/tmp/06_genai_responsible_ai_executed.ipynb --ExecutePreprocessor.timeout=120
```

Additional validation confirmed:

- all JSON files are parseable
- all notebooks are valid notebook JSON
- no hard-coded `/Users/...` paths remain in project files
- `01 -> 03 -> 04 -> 05` handoff counts match
- `03 -> 04 -> 05` claim IDs match
- required schema fields are present

## Known Notes for the Streamlit App

- Use `05_Bayesian_Inference/final_verdicts.json` as the main demo output
  because it already contains final probabilities, KG evidence, and reasoning.
- Use `06_GenAI_Responsible_AI/responsible_ai_summary.json` for presentation
  metrics such as KG unknown rate, Bayesian uncertainty rate, and risk-register
  content.
- The current pipeline is intentionally conservative: `499/500` final verdicts
  are `uncertain` because KG reasoning found only one supported claim and no
  contradicted claims. This should be presented as a responsible uncertainty
  design decision, not as a broken demo.
- The app should avoid implying that `uncertain` means true or false.
- A good app structure would be `streamlit_app/app.py` plus small helper modules
  inside the same folder.

## Remaining Technical Cautions

- The full claim extraction and online entity linking notebooks can be slow
  because they depend on transformer models and Wikidata API calls.
- The local `python3` interpreter does not currently have all project
  dependencies installed. The Anaconda Python at `/opt/anaconda3/bin/python`
  does have the data-science dependencies used by modules `02`, `03`, and `04`.
  For a fresh environment, run:

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```
