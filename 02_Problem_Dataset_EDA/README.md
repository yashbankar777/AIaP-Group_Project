# 02 Problem, Dataset EDA, and Preprocessing

Owner: Member 2

## Purpose

This module explains the real-world problem and analyses the LIAR dataset before downstream AI reasoning.

## Tasks

- Define misinformation verification as a real-world AI problem.
- Analyse the LIAR dataset structure.
- Report train/validation/test sizes.
- Show truth-label distribution.
- Check missing values and duplicated rows.
- Analyse speakers, subjects, parties, and contexts where useful.
- Summarise preprocessing decisions.
- Create tables/figures for the report.

## Input

- `../LIAR_dataset/train.tsv`
- `../LIAR_dataset/valid.tsv`
- `../LIAR_dataset/test.tsv`

## Expected Outputs

- dataset summary table
- label distribution figure
- preprocessing notes
- `dataset_summary.json`
- `preprocessing_notes.md`
- report-ready tables in `../report_assets/tables/`
- report-ready figures in `figures/` and `../report_assets/figures/`

## How to Run

From the repository root:

```bash
python3 02_Problem_Dataset_EDA/run_eda.py
```

The notebook `dataset_eda.ipynb` uses the same runner and can be opened to review the analysis step by step.

## Report Sections Supported

- Executive Summary
- Introduction
- Workflow and Methodology: data collection and preprocessing
- Empirical Analysis: dataset description

## Suggested Metrics

- number of rows per split
- number of labels
- label distribution
- missing values per column
- duplicated rows
- top speakers and topics
