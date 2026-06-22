from typing import List
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from src.core.setting import setup_logger
import logging

logger: logging.Logger = setup_logger("pipeline_stats", logging.DEBUG)


@dataclass
class PipelineConfig:
    max_videos: int = 100
    max_comments_per_video: int = 50
    max_replies_per_comment: int = 10

    rate_limit_rps: float = 2.0
    burst: int = 1

    video_batch_size: int = 50
    channel_batch_size: int = 50

    checkpoint_dir: Path = field(default_factory=lambda: Path("checkpoints"))
    save_checkpoint_every: int = 10

    min_views: int = 0
    min_likes: int = 0
    languages: List[str] = field(default_factory=lambda: ["pt", "en"])

    fetch_comments: bool = True
    fetch_subtitles: bool = False
    fetch_channel_details: bool = True

    output_dir: Path = field(default_factory=lambda: Path("output"))


@dataclass
class PipelineStats:
    """Estatísticas da execução."""

    start_time: datetime = field(default_factory=datetime.now)
    videos_processed: int = 0
    comments_collected: int = 0
    channels_collected: int = 0
    subtitles_collected: int = 0
    api_calls: int = 0
    quota_used_estimate: int = 0
    errors: List[str] = field(default_factory=list)

    def add_quota(self, units: int, operation: str):
        """Registra uso de quota."""
        self.quota_used_estimate += units
        self.api_calls += 1
        logger.debug(
            f"Quota: +{units} units ({operation}), total: {self.quota_used_estimate}"
        )

    def report(self) -> str:
        """Retorna relatório de execução."""
        duration = (datetime.now() - self.start_time).total_seconds()
        return f"""
            Duração: {duration:.1f}s
            API Calls: {self.api_calls}
            Quota Estimada: {self.quota_used_estimate} units

            Vídeos processados: {self.videos_processed}
            Comentários coletados: {self.comments_collected}
            Canais únicos: {self.channels_collected}
            Legendas baixadas: {self.subtitles_collected}
            Erros: {len(self.errors)}
        """
