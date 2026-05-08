from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/matplotlib-cache")
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


LIAR_COLUMNS = [
    "statement_id",
    "label",
    "statement",
    "subjects",
    "speaker",
    "speaker_job",
    "state",
    "party",
    "barely_true_count",
    "false_count",
    "half_true_count",
    "mostly_true_count",
    "pants_fire_count",
    "context",
]

LABEL_ORDER = [
    "pants-fire",
    "false",
    "barely-true",
    "half-true",
    "mostly-true",
    "true",
]

SPLIT_ORDER = ["train", "valid", "test"]

CREDIT_COLUMNS = [
    "barely_true_count",
    "false_count",
    "half_true_count",
    "mostly_true_count",
    "pants_fire_count",
]


def find_project_root(start: Path | None = None) -> Path:
    """Return the repository root whether this is run from root or the module folder."""
    current = (start or Path.cwd()).resolve()
    candidates = [current, *current.parents]
    for candidate in candidates:
        if (candidate / "LIAR_dataset").exists() and (candidate / "01_Claim_Extraction").exists():
            return candidate
    raise FileNotFoundError("Could not find project root containing LIAR_dataset.")


def load_liar_dataset(project_root: Path) -> pd.DataFrame:
    frames = []
    for split, filename in {
        "train": "train.tsv",
        "valid": "valid.tsv",
        "test": "test.tsv",
    }.items():
        path = project_root / "LIAR_dataset" / filename
        split_df = pd.read_csv(
            path,
            sep="\t",
            header=None,
            names=LIAR_COLUMNS,
            dtype=str,
            keep_default_na=False,
        )
        split_df.insert(0, "split", split)
        frames.append(split_df)

    df = pd.concat(frames, ignore_index=True)
    for column in df.columns:
        df[column] = df[column].astype(str).str.strip()
    for column in CREDIT_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0).astype(int)

    df["statement_word_count"] = df["statement"].str.split().str.len()
    df["subject_count"] = df["subjects"].apply(
        lambda value: 0 if not value else len([item for item in value.split(",") if item.strip()])
    )
    return df


def missing_value_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column in LIAR_COLUMNS:
        missing = df[column].isna() | df[column].astype(str).str.strip().eq("")
        rows.append(
            {
                "column": column,
                "missing_count": int(missing.sum()),
                "missing_percent": round(float(missing.mean() * 100), 2),
            }
        )
    return pd.DataFrame(rows)


def split_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby("split")
        .agg(
            row_count=("statement_id", "count"),
            unique_labels=("label", "nunique"),
            unique_speakers=("speaker", "nunique"),
            duplicate_statements=("statement", lambda values: int(values.duplicated().sum())),
            mean_statement_words=("statement_word_count", "mean"),
            median_statement_words=("statement_word_count", "median"),
        )
        .reset_index()
        .assign(
            mean_statement_words=lambda data: data["mean_statement_words"].round(2),
            median_statement_words=lambda data: data["median_statement_words"].round(2),
        )
    )
    summary["split"] = pd.Categorical(summary["split"], categories=SPLIT_ORDER, ordered=True)
    return summary.sort_values("split").reset_index(drop=True)


def label_distribution_table(df: pd.DataFrame) -> pd.DataFrame:
    counts = (
        df.groupby(["split", "label"])
        .size()
        .rename("count")
        .reset_index()
    )
    totals = counts.groupby("split")["count"].transform("sum")
    counts["percent"] = (counts["count"] / totals * 100).round(2)
    counts["split"] = pd.Categorical(counts["split"], categories=SPLIT_ORDER, ordered=True)
    counts["label"] = pd.Categorical(counts["label"], categories=LABEL_ORDER, ordered=True)
    return counts.sort_values(["split", "label"]).reset_index(drop=True)


def top_subjects_table(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    subject_rows = []
    for _, row in df.iterrows():
        for subject in row["subjects"].split(","):
            subject = subject.strip()
            if subject:
                subject_rows.append({"subject": subject, "split": row["split"]})
    if not subject_rows:
        return pd.DataFrame(columns=["subject", "count"])
    return (
        pd.DataFrame(subject_rows)
        .value_counts("subject")
        .head(n)
        .rename_axis("subject")
        .reset_index(name="count")
    )


def top_value_table(df: pd.DataFrame, column: str, n: int = 15) -> pd.DataFrame:
    values = df[column].replace("", "missing")
    return values.value_counts().head(n).rename_axis(column).reset_index(name="count")


def claim_extraction_summary(project_root: Path) -> dict:
    path = project_root / "01_Claim_Extraction" / "extracted_triples_filtered.json"
    if not path.exists():
        return {"available": False, "path": str(path)}

    records = json.loads(path.read_text())
    triples = pd.DataFrame(records)
    if triples.empty:
        return {"available": True, "record_count": 0}

    confidence_column = "confidence" if "confidence" in triples.columns else "extraction_confidence"
    summary = {
        "available": True,
        "record_count": int(len(triples)),
        "columns": list(triples.columns),
        "label_distribution": triples.get("label", pd.Series(dtype=str)).value_counts().to_dict(),
        "top_relations": triples.get("relation", pd.Series(dtype=str)).value_counts().head(10).to_dict(),
        "subject_type_distribution": triples.get("subject_type", pd.Series(dtype=str)).value_counts().to_dict(),
    }
    if confidence_column in triples.columns:
        summary["mean_extraction_confidence"] = round(float(pd.to_numeric(triples[confidence_column]).mean()), 4)
    return summary


def save_bar_chart(data: pd.DataFrame, x: str, y: str, title: str, output_path: Path, hue: str | None = None) -> None:
    plt.figure(figsize=(10, 5))
    sns.set_theme(style="whitegrid")
    ax = sns.barplot(data=data, x=x, y=y, hue=hue, errorbar=None)
    ax.set_title(title)
    ax.set_xlabel(x.replace("_", " ").title())
    ax.set_ylabel(y.replace("_", " ").title())
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    plt.close()


def run_eda(project_root: Path | None = None) -> dict:
    project_root = find_project_root(project_root)
    output_dir = project_root / "02_Problem_Dataset_EDA"
    report_tables_dir = project_root / "report_assets" / "tables"
    report_figures_dir = project_root / "report_assets" / "figures"
    module_figures_dir = output_dir / "figures"

    for path in [report_tables_dir, report_figures_dir, module_figures_dir]:
        path.mkdir(parents=True, exist_ok=True)

    df = load_liar_dataset(project_root)
    split_summary = split_summary_table(df)
    labels = label_distribution_table(df)
    missing = missing_value_table(df)
    speakers = top_value_table(df, "speaker")
    parties = top_value_table(df, "party")
    states = top_value_table(df, "state")
    contexts = top_value_table(df, "context")
    subjects = top_subjects_table(df)

    tables = {
        "dataset_split_summary.csv": split_summary,
        "label_distribution.csv": labels,
        "missing_values.csv": missing,
        "top_speakers.csv": speakers,
        "top_parties.csv": parties,
        "top_states.csv": states,
        "top_contexts.csv": contexts,
        "top_subjects.csv": subjects,
    }
    for filename, table in tables.items():
        table.to_csv(report_tables_dir / filename, index=False)

    save_bar_chart(
        split_summary,
        x="split",
        y="row_count",
        title="LIAR Dataset Rows by Split",
        output_path=report_figures_dir / "liar_split_sizes.png",
    )
    save_bar_chart(
        labels,
        x="label",
        y="count",
        hue="split",
        title="LIAR Truth Label Distribution by Split",
        output_path=report_figures_dir / "liar_label_distribution.png",
    )
    save_bar_chart(
        parties,
        x="party",
        y="count",
        title="Top Party Affiliations in LIAR",
        output_path=report_figures_dir / "liar_party_distribution.png",
    )

    for figure_name in [
        "liar_split_sizes.png",
        "liar_label_distribution.png",
        "liar_party_distribution.png",
    ]:
        source = report_figures_dir / figure_name
        target = module_figures_dir / figure_name
        target.write_bytes(source.read_bytes())

    duplicate_statement_count = int(df.duplicated(subset=["statement"]).sum())
    duplicate_id_count = int(df.duplicated(subset=["statement_id"]).sum())
    summary = {
        "dataset": "LIAR",
        "source_files": ["train.tsv", "valid.tsv", "test.tsv"],
        "total_rows": int(len(df)),
        "rows_by_split": split_summary.set_index("split")["row_count"].astype(int).to_dict(),
        "label_order": LABEL_ORDER,
        "overall_label_distribution": df["label"].value_counts().reindex(LABEL_ORDER).fillna(0).astype(int).to_dict(),
        "duplicate_statement_count": duplicate_statement_count,
        "duplicate_statement_percent": round(float(duplicate_statement_count / len(df) * 100), 2),
        "duplicate_id_count": duplicate_id_count,
        "missing_values": missing.set_index("column")["missing_count"].astype(int).to_dict(),
        "mean_statement_words": round(float(df["statement_word_count"].mean()), 2),
        "median_statement_words": round(float(df["statement_word_count"].median()), 2),
        "top_speakers": speakers.head(10).to_dict(orient="records"),
        "top_subjects": subjects.head(10).to_dict(orient="records"),
        "claim_extraction_handoff": claim_extraction_summary(project_root),
        "generated_tables": [str((report_tables_dir / name).relative_to(project_root)) for name in tables],
        "generated_figures": [
            "report_assets/figures/liar_split_sizes.png",
            "report_assets/figures/liar_label_distribution.png",
            "report_assets/figures/liar_party_distribution.png",
        ],
    }

    summary_path = output_dir / "dataset_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    notes = f"""# EDA Preprocessing Notes

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

- Total rows loaded: {summary["total_rows"]}
- Rows by split: {summary["rows_by_split"]}
- Duplicate statement rows: {summary["duplicate_statement_count"]} ({summary["duplicate_statement_percent"]}%)
- Mean statement length: {summary["mean_statement_words"]} words
- Median statement length: {summary["median_statement_words"]} words

## Connection to the Pipeline

This EDA notebook supports problem framing and dataset understanding. The downstream pipeline starts from `01_Claim_Extraction/extracted_triples_filtered.json`, which currently contains {summary["claim_extraction_handoff"].get("record_count", 0)} extracted claim records.
"""
    (output_dir / "preprocessing_notes.md").write_text(notes)

    return {
        "data": df,
        "split_summary": split_summary,
        "label_distribution": labels,
        "missing_values": missing,
        "top_speakers": speakers,
        "top_parties": parties,
        "top_states": states,
        "top_contexts": contexts,
        "top_subjects": subjects,
        "summary": summary,
    }


if __name__ == "__main__":
    results = run_eda()
    print(json.dumps(results["summary"], indent=2))
