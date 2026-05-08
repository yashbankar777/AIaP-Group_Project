# Bayesian Model Notes

This module defines how uncertain upstream evidence is combined into the final
credibility estimate.

## Inputs

- extraction confidence from Member 1
- KG status from Member 4
- KG confidence from Member 4
- entity-linking confidence from Member 3 when available
- optional LIAR speaker-history counts

The ground-truth LIAR label is kept only as `reference_label` for evaluation.
It is not used when calculating `P(true)`.

## Bayesian Assumptions

The model starts from a neutral prior:

```text
P(true) = 0.50
```

When LIAR speaker-history counts are available, the prior is adjusted slightly:

```text
positive_history = mostly_true_count + 0.5 * half_true_count
negative_history = false_count + pants_fire_count
                   + 0.75 * barely_true_count
                   + 0.5 * half_true_count
```

The adjusted speaker prior is blended back toward 0.50 so that historical
speaker metadata cannot dominate the claim evidence.

The KG result is then treated as a likelihood-ratio signal:

```text
posterior_log_odds = prior_log_odds
                     + kg_status_log_bayes_factor * evidence_weight
```

Current log Bayes factors:

```text
supported    = +2.4
contradicted = -2.4
unknown      =  0.0
```

The evidence weight is the KG confidence scaled by extraction and entity-linking
confidence. In other words, strong KG support or contradiction matters most when
the claim extraction and entity linking are also reliable.

## Output Labels

- `likely true`
- `likely false`
- `uncertain`

The threshold is conservative: a claim must reach at least `0.65` posterior
probability for `likely true`, or at most `0.35` for `likely false`. Otherwise
the model returns `uncertain`.

The report should explain why uncertainty is retained rather than forcing every
claim into a binary answer. This is especially important because the KG module
is intentionally conservative and many extracted political claims cannot be
verified safely with the available local KG evidence.
