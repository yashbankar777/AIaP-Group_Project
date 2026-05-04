# Project Structure and Task Allocation

This file is the working plan for dividing the project so each member can contribute independently.

## Official Project Direction

The project is a misinformation verification system. The report should focus on the AI pipeline, not on the Streamlit app.

The system combines:

- NLP claim extraction
- structural knowledge representation
- symbolic knowledge graph reasoning
- Bayesian probabilistic inference
- GenAI/LLM comparison and responsible AI reflection

## Member Tasks

| Member | Folder | Task | Expected output |
|---|---|---|---|
| 1 | `01_Claim_Extraction/` | Completed claim extraction using RoBERTa/spaCy | `extracted_triples_filtered.json` |
| 2 | `02_Problem_Dataset_EDA/` | Problem framing, dataset analysis, preprocessing | dataset summary, label charts, EDA notes |
| 3 | `03_Entity_Linking_KR/` | Entity linking and knowledge representation | `linked_entities.json`, schema notes |
| 4 | `04_KG_Reasoning/` | Knowledge graph reasoning and decision-making | `kg_results.json`, reasoning rules |
| 5 | `05_Bayesian_Inference/` | Bayesian final credibility inference | `final_verdicts.json`, Bayesian assumptions |
| 6 | `06_GenAI_Responsible_AI/` | GenAI/LLM comparison, ethics, limitations, scalability | responsible AI analysis and future work |

## Working Rules

- Work in your own numbered folder.
- Do not edit another member's module unless the group agrees.
- Use JSON or CSV outputs as handoff files.
- Use `shared/sample_*.json` files when an upstream member's final output is not ready.
- Add tables or figures for the report into `report_assets/`.
- Keep your README updated with what you did and how it supports the report.

## Immediate Next Steps

1. Member 2 starts dataset EDA and creates report figures.
2. Member 3 starts entity linking using `01_Claim_Extraction/extracted_triples_filtered.json` or `shared/sample_triples.json`.
3. Member 4 starts KG reasoning with `shared/sample_linked_entities.json`.
4. Member 5 starts Bayesian inference with `shared/sample_kg_results.json`.
5. Member 6 starts GenAI/LLM comparison and responsible AI reflection.
6. Each member writes their assigned report subsection in `REPORT_OUTLINE.md`.
