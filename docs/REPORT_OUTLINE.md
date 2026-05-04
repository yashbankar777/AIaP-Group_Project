# Report Outline and Writing Allocation

The final report should follow the official Assessment 3 template.

Target length: up to 3500 words including references.

## 1. Executive Summary

Primary writer: Member 2, final group review.

Expected content:

- one-paragraph project overview
- problem being solved
- AI methods used
- key findings and limitations

Write this section last.

## 2. Introduction

Primary writer: Member 2.

Expected content:

- background and context of misinformation verification
- real-world significance and impact
- problem statement
- challenges and constraints
- project objectives and scope

Member 6 can contribute ethical and real-world impact points.

## 3. Theoretical Justification

Primary writers: Members 1, 3, 4, 5, 6.

Suggested split:

- Member 1: RoBERTa/spaCy, NER, dependency parsing, claim extraction
- Member 3: structural knowledge representation and entity linking
- Member 4: symbolic reasoning and decision-making over KG evidence
- Member 5: Bayesian probabilistic reasoning
- Member 6: GenAI/LLM comparison and responsible AI considerations

## 4. Workflow and Methodology

Primary writers: Members 1, 2, 3, 4, 5.

Suggested split:

- Member 2: dataset collection, dataset structure, preprocessing
- Member 1: claim extraction workflow
- Member 3: entity linking workflow
- Member 4: KG reasoning workflow
- Member 5: Bayesian inference workflow

Clearly distinguish design decisions from implementation details.

## 5. Empirical Analysis and Results

Primary writers: Members 2, 3, 4, 5.

Expected content:

- dataset description and label distribution
- extraction quality metrics
- entity-linking success rate
- KG support/contradiction/unknown counts
- final credibility results
- tables and figures

Member 1 can provide extraction output context if needed.

## 6. Critical Reflection

Primary writer: Member 6, with short input from everyone.

Expected content:

- limitations of the approach
- failure cases from each module
- trade-offs such as accuracy vs interpretability and coverage vs reliability
- scalability and computational constraints
- alternative methods and future improvements
- responsible AI risks such as bias, false positives, false negatives, and hallucination risk

## 7. GitHub Repository

Primary writer: shared/final editor.

Expected content:

- repository link
- setup instructions
- how to run notebooks/modules
- explanation of folder structure

## 8. Conclusion

Primary writers: Members 5 and 6, final group review.

Expected content:

- summary of findings
- key insights from the AI pipeline
- realistic future work

## 9. Individual Contributions

Primary writer: each member writes their own.

Each contribution should be specific and verifiable. Example:

```text
Member 3 implemented the entity-linking module, mapping extracted subjects and objects to knowledge graph identifiers, documenting the claim schema, and preparing linked entity outputs for downstream KG reasoning.
```

## 10. References

Primary writer: each member contributes references for their section.

Use academic references where possible. Keep citation style consistent.
