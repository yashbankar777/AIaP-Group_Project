# 06 GenAI, LLM Comparison, and Responsible AI

Owner: Member 6

## Purpose

This module covers GenAI/LLM comparison, responsible AI design, limitations, trade-offs, scalability, and future work.

This is an official assessed contribution, not just report editing.

## Tasks

- Compare the proposed pipeline with a GenAI/LLM-only approach.
- Discuss how LLMs or RAG could improve the system.
- Analyse risks such as hallucination, bias, overconfidence, and misinformation amplification.
- Discuss false positives and false negatives.
- Analyse scalability and computational constraints.
- Propose realistic future improvements.

## Expected Outputs

- `responsible_ai_analysis.md`
- `responsible_ai_summary.json`
- `genai_responsible_ai.ipynb`
- `../report_assets/tables/responsible_ai_module_evidence.csv`
- `../report_assets/tables/genai_pipeline_comparison.csv`
- `../report_assets/tables/responsible_ai_risk_register.csv`
- `../report_assets/tables/responsible_ai_future_work.csv`
- limitations/trade-off notes for the final report

## How to Run

From the repository root:

```bash
python3 06_GenAI_Responsible_AI/run_responsible_ai_analysis.py
```

The notebook `genai_responsible_ai.ipynb` uses the same runner and explains the
comparison, responsible AI risks, limitations, scalability, and future work.

## Method Notes

- The notebook does not make live LLM calls. This keeps the comparison
  reproducible and avoids unsupported generated claims.
- The GenAI comparison is grounded in evidence from Notebooks 1 to 5.
- The recommended future direction is a retrieval-augmented, human-in-the-loop
  hybrid system, not an unconstrained LLM-only verifier.

## Report Sections Supported

- Introduction: real-world impact and ethical implications
- Theoretical Justification: GenAI/LLM comparison
- Critical Reflection
- Conclusion and Future Work
