# EDA Preprocessing Notes

The LIAR dataset was loaded from train, validation, and test TSV files using the 14-column schema described in `LIAR_dataset/README`.

## Decisions

- Kept the original six truth labels: pants-fire, false, barely-true, half-true, mostly-true, and true.
- Added a `split` column so train, validation, and test records can be compared without merging them silently.
- Trimmed whitespace from text fields and treated blank strings as missing values.
- Converted speaker credit-history count columns to integers.
- Added lightweight derived features for analysis only: statement word count and subject count.
- Did not remove duplicate statements automatically. Duplicates are reported because removing them could change comparability with the original benchmark.
- Did not use party or speaker metadata as direct truth evidence. These fields are useful for bias analysis, but they can encode historical and political bias.

## Key Dataset Facts

- Total rows loaded: 12791
- Rows by split: {'train': 10240, 'valid': 1284, 'test': 1267}
- Duplicate statement rows: 26 (0.2%)
- Mean statement length: 18.04 words
- Median statement length: 17.0 words

## Connection to the Pipeline

This EDA notebook supports problem framing and dataset understanding. The downstream pipeline starts from `01_Claim_Extraction/extracted_triples_filtered.json`, which currently contains 500 extracted claim records.
