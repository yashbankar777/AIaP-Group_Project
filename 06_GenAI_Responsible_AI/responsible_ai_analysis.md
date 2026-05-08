# Responsible AI Analysis

This module compares the project pipeline with GenAI and LLM-based alternatives, then evaluates the system through responsible AI risks, limitations, scalability, and future work.

## Executive Position

The current system is best understood as an interpretable decision-support pipeline, not a fully automated fact-checker. Its main strength is traceability: the project preserves extracted triples, entity links, KG reasoning status, Bayesian assumptions, and final uncertainty. Its main weakness is evidence coverage: KG reasoning returns unknown for 99.8% of the 500 processed claims, which leads Bayesian inference to keep 99.8% of claims uncertain.

For a high-stakes misinformation setting, this conservative behaviour is ethically preferable to a GenAI-only system that answers every claim with fluent but potentially unsupported explanations. The strongest future direction is a hybrid RAG and KG workflow where an LLM helps decompose claims and summarise retrieved evidence, while citations, entity IDs, calibrated probabilities, and human review remain mandatory.

## Evidence From Project Modules

| module | method | project_evidence | responsible_ai_interpretation |
| --- | --- | --- | --- |
| 01 Claim Extraction | RoBERTa NER plus spaCy dependency parsing | 500 triples; mean extraction confidence 0.7735; 211 UNKNOWN subjects | The system creates auditable subject-relation-object evidence, but extraction confidence is not a truth score and parser errors can flow downstream. |
| 02 Dataset EDA | LIAR dataset profiling and preprocessing review | 12791 rows across 6 truth labels; 26 duplicate statements; 3566 missing speaker jobs | The political dataset is useful for benchmarking but carries selection, speaker, topic, and label bias risks. |
| 03 Entity Linking and KR | Wikidata-compatible entity and property representation | 273 of 500 records have any entity link; property mapping coverage is 0.2%; average linking confidence is 0.373 | Knowledge representation improves traceability, but low linking and property coverage create a major verification bottleneck. |
| 04 KG Reasoning | Conservative symbolic reasoning over KG evidence | 499 unknown, 1 supported, 0 contradicted; average KG confidence 0.319 | The KG layer avoids unsupported factual claims by abstaining when evidence is insufficient. |
| 05 Bayesian Inference | Conservative posterior probability and final verdict model | 499 uncertain and 1 likely true; average decision confidence 0.039 | The final model communicates uncertainty instead of converting weak evidence into definitive misinformation labels. |

## GenAI and LLM Comparison

| dimension | current_pipeline | llm_only | rag_hybrid |
| --- | --- | --- | --- |
| Evidence traceability | High: triples, entity IDs, KG status, evidence text, and Bayesian reasoning are stored. | Often weak unless explicitly forced to cite sources; generated rationales may sound plausible without evidence. | Potentially high if retrieved passages, KG IDs, prompts, and model outputs are logged together. |
| Coverage | Low-to-moderate: strict entity linking and KG rules leave most claims unknown. | High surface coverage because an LLM can answer almost every claim. | Moderate-to-high if retrieval expands evidence while abstention remains allowed. |
| Factuality risk | Lower overclaiming risk because the system abstains when KG evidence is missing. | Higher hallucination and overconfidence risk, especially on political or time-sensitive claims. | Lower than LLM-only when answers must be grounded in retrieved, checked sources. |
| Bias sensitivity | Dataset and speaker-history bias remain, but the Bayesian prior is deliberately weak. | May reproduce training-data, prompt, political, and source-selection biases with less visibility. | Can be audited through source diversity checks and topic/speaker fairness reporting. |
| Interpretability | Strong: each stage has a specific representation and failure mode. | Weak-to-moderate: natural-language explanations are readable but not necessarily faithful. | Strong if the LLM is used to summarise retrieved evidence rather than invent evidence. |
| Scalability | Efficient once built, but KG lookup and relation coverage limit throughput and recall. | Simple to prototype but expensive and harder to reproduce at scale. | Most realistic deployment path: batch retrieval, cached evidence, and selective LLM calls. |
| Best use | Auditable verification, conservative decision support, and reportable uncertainty. | Exploratory assistance, claim rewriting, and identifying possible evidence sources. | Human-in-the-loop fact checking with citations, calibrated uncertainty, and escalation. |

## Responsible AI Risk Register

| risk_area | project_evidence | potential_harm | current_control | recommended_improvement | severity |
| --- | --- | --- | --- | --- | --- |
| Hallucinated or unsupported evidence | KG reasoning returned 99.8% unknown results. | A system that still gives definitive answers could falsely accuse or falsely clear claims. | The KG and Bayesian modules abstain when evidence is weak. | Use RAG with citation verification and require source-level evidence before final labels. | High |
| False positives | Bayesian output kept 99.8% of claims uncertain. | True or nuanced claims could be labelled misinformation, harming public trust. | Conservative 0.65 threshold and explicit uncertainty class. | Route low-evidence or high-impact claims to human review. | High |
| False negatives | The current KG layer found no contradicted claims in the 500-record handoff. | False claims may pass through as uncertain rather than being challenged. | The output does not call uncertain claims true. | Improve relation extraction, claim decomposition, and live KG/source querying. | High |
| Dataset and speaker bias | LIAR has 12791 political claims and concentrated top speakers/topics. | The model may encode political, media-selection, or speaker-history bias. | Speaker history is weakly weighted and labels are not used as probability evidence. | Report performance by speaker, party, topic, state, and label bucket. | Medium |
| Entity-linking error propagation | Only 54.6% of records have any entity link and property mapping coverage is 0.2%. | Wrong or missing entity IDs can make correct KG reasoning impossible. | Low-confidence links remain visible and usually lead to unknown KG status. | Add candidate ranking, alias expansion, entity disambiguation, and confidence calibration. | Medium |
| Automation misuse | The project produces decision-support probabilities, not verified legal or journalistic rulings. | Users may treat probabilistic outputs as authoritative fact-checks. | Outputs include reasoning, uncertainty, and reference-label separation. | Add UI warnings, audit logs, appeal paths, and reviewer sign-off for public deployment. | Medium |

## Scalability and Deployment Reflection

- Claim extraction can be batched, but higher-quality relation extraction and coreference resolution are needed before scaling beyond the current 500-record handoff.
- Entity linking is the main coverage bottleneck: only 54.6% of records have any entity link, and property mapping coverage is 0.2%.
- KG reasoning is computationally cheap once entities and properties are available, but external API calls, incomplete KG coverage, and political claim complexity limit recall.
- Bayesian inference is scalable and transparent, but its probabilities should be calibrated with validation data before deployment.
- LLM-only verification scales poorly in governance terms because cost, prompt sensitivity, hallucination risk, and reproducibility problems increase with volume.
- A hybrid system should cache retrieved evidence, log prompts and sources, enforce abstention, and escalate high-impact cases to human reviewers.

## Recommended Future Work

| priority | improvement | why_it_matters | expected_effect |
| --- | --- | --- | --- |
| 1 | Replace single-triple extraction with multi-claim decomposition and coreference resolution. | Political claims often contain multiple factual units and pronouns that break simple triples. | Higher recall and cleaner downstream KG queries. |
| 2 | Expand entity linking with candidate ranking, aliases, and confidence calibration. | Entity-link coverage is the main bottleneck before KG reasoning. | More claims reach evidence-based support or contradiction decisions. |
| 3 | Add live Wikidata/DBpedia/SPARQL property checks plus trusted web retrieval. | The current KG layer mostly reasons over local descriptions and simple class rules. | Better factual coverage while keeping evidence traceable. |
| 4 | Use an LLM only inside a retrieval-grounded workflow. | LLMs can improve paraphrase handling and evidence synthesis but must not invent sources. | Improved usability without losing auditability. |
| 5 | Calibrate Bayesian probabilities against a labelled validation set. | Current probabilities are transparent assumptions rather than empirically calibrated truth rates. | More reliable decision thresholds and confidence estimates. |
| 6 | Create a human-in-the-loop review workflow for high-impact or low-evidence claims. | Responsible deployment needs accountability for decisions that affect people or public discourse. | Lower harm from false positives, false negatives, and automation bias. |

## Report-Ready Conclusion

The project demonstrates a responsible design trade-off: it sacrifices broad automated coverage in order to preserve interpretability, evidence traceability, and uncertainty. A GenAI-only approach would likely produce more complete-looking answers, but those answers would be harder to audit and more vulnerable to hallucination and overconfidence. The most defensible improvement is not to replace the pipeline with an LLM, but to integrate LLMs in a constrained RAG workflow that improves claim decomposition, source retrieval, and explanation quality while preserving KG evidence, calibrated Bayesian uncertainty, and human oversight.
