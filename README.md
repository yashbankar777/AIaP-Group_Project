# AIaP Group Project: Misinformation Verification System

This repository is structured for Assessment 3: Real World Applications of Artificial Intelligence.

The project is a misinformation verification pipeline. It combines NLP-based claim extraction, structural knowledge representation, symbolic knowledge graph reasoning, Bayesian probabilistic inference, and responsible AI/GenAI reflection.

The Streamlit app is treated as a separate group demo and is ignored by Git. The official assignment contribution is based on the AI modules, results, report sections, and individual contribution evidence.

## Official Folder Structure

```text
01_Claim_Extraction/          Member 1 - already completed
02_Problem_Dataset_EDA/       Member 2
03_Entity_Linking_KR/         Member 3
04_KG_Reasoning/              Member 4
05_Bayesian_Inference/        Member 5
06_GenAI_Responsible_AI/      Member 6
shared/                       Shared schemas and sample handoff files
report_assets/                Tables and figures for the final report
LIAR_dataset/                 Source dataset
```

The older root-level notebooks `02_Knowledge_graph_reasoning.ipynb` and `03_Bayesian_reasoning.ipynb` are legacy placeholders. New work should go into the numbered folders above.

## Contribution Split

| Member | Contribution | Main report link |
|---|---|---|
| 1 | Claim extraction using RoBERTa/spaCy | NLP method, feature engineering, model design |
| 2 | Problem formulation, dataset EDA, preprocessing | Introduction, dataset, workflow |
| 3 | Entity linking and structural knowledge representation | Knowledge representation |
| 4 | Knowledge graph reasoning and decision-making | Logic and symbolic reasoning |
| 5 | Bayesian credibility inference | Probabilistic reasoning and final verdict |
| 6 | GenAI/LLM comparison and responsible AI reflection | Critical reflection, ethics, scalability |

## Independence Rules

- Each member is responsible for one clearly assigned folder/module.
- Members should only edit their own module unless the group agrees otherwise.
- Each module must have a clear input file and output file.
- Modules should pass data through JSON or CSV files, not through one shared notebook.
- If another member's output is not ready, use a small sample file with the same format.
- Each module should include a short README explaining what it does, how to run it, what it produces, and how it connects to the report.
- The Streamlit app is only a group demo tool; it is not one person's main assessed contribution.
- The official assessment contribution should be based on AI methods, experiments, results, and critical reflection.

## Pipeline Flow

```text
LIAR_dataset
  -> 01_Claim_Extraction
       output: extracted_triples_filtered.json
  -> 03_Entity_Linking_KR
       output: linked_entities.json
  -> 04_KG_Reasoning
       output: kg_results.json
  -> 05_Bayesian_Inference
       output: final_verdicts.json
```

Member 2 and Member 6 are non-blocking modules. They can work independently while the pipeline modules are being developed.

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

For the spaCy model used in Member 1's notebook:

```bash
python -m spacy download en_core_web_sm
```

## Shared Contracts

See [shared/schemas.md](shared/schemas.md) for the agreed JSON fields and sample handoff files.

## Report Planning

See [PROJECT_STRUCTURE_AND_TASKS.md](PROJECT_STRUCTURE_AND_TASKS.md) and [REPORT_OUTLINE.md](REPORT_OUTLINE.md).
