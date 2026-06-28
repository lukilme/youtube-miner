from dataclasses import field
from pathlib import Path
from typing import List, Dict, Any
import csv
import json
import logging

from src.core.setting.logger import setup_logger

logger: logging.Logger = setup_logger("builder")


class DataExporter:
    checkpoint_dir: Path = field(default_factory=lambda: Path("checkpoints"))

    @staticmethod
    def to_csv(rows: List[Dict[str, Any]], filepath: str) -> None:
        if not rows:
            logger.info("Nenhum dado para salvar em %s.", filepath)
            return
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        logger.info("CSV salvo: %s (%d linhas).", filepath, len(rows))

    @staticmethod
    def to_json(rows: List[Dict[str, Any]], filepath: str) -> None:
        if not rows:
            logger.info("Nenhum dado para salvar em %s.", filepath)
            return
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        logger.info("JSON salvo: %s (%d registros).", filepath, len(rows))
