from __future__ import annotations

from pathlib import Path
from typing import Any
from IPython.display import Markdown, display, HTML
import pandas as pd


def enrich_dataframe(df: pd.DataFrame, csv_file: Path) -> pd.DataFrame:
    """
    Adiciona metadados do arquivo ao DataFrame.
    """
    df = df.copy()

    df["source_file"] = csv_file.name
    df["source_path"] = str(csv_file)

    collection_id = next(
        (part for part in csv_file.parts if part.startswith("id_")),
        None
    )
    df["collection_id"] = collection_id

    stem_parts = csv_file.stem.split("_")
    country = stem_parts[-1] if len(stem_parts) > 2 else None
    df["country"] = country

    return df


def get_dataset_type(csv_file: Path) -> str | None:
    """
    Identifica o tipo do dataset pelo nome do arquivo.
    """
    filename = csv_file.name.lower()

    if "video" in filename:
        return "videos"

    if "comment" in filename:
        return "comments"

    if "channel" in filename:
        return "channels"

    return None


def load_datasets(base_dir: Path) -> dict[str, pd.DataFrame]:
    """
    Carrega todos os CSVs e retorna DataFrames consolidados.
    """
    datasets: dict[str, list[pd.DataFrame]] = {
        "videos": [],
        "comments": [],
        "channels": [],
    }

    for csv_file in base_dir.rglob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
            df = enrich_dataframe(df, csv_file)

            dataset_type = get_dataset_type(csv_file)

            if dataset_type:
                datasets[dataset_type].append(df)

        except Exception as e:
            print(f"Erro ao ler {csv_file}: {e}")

    return {
        name: (
            pd.concat(frames, ignore_index=True)
            if frames
            else pd.DataFrame()
        )
        for name, frames in datasets.items()
    }


def show_summary(datasets: dict[str, pd.DataFrame]) -> None:
    for name, df in datasets.items():
        print(f"{name.capitalize()}: {len(df):,}")




BASE_DIR = Path("../data/raw")

datasets = load_datasets(BASE_DIR)

videos_df = datasets["videos"]
comments_df = datasets["comments"]
channels_df = datasets["channels"]

#show_summary(datasets)