from __future__ import annotations
from typing import Optional, Self
from pathlib import Path
from src.core.pipeline.pipeline import YouTubePipeline
from src.core.models.pipeline_data_classes import PipelineConfig
import logging

from src.core.setting.logger import setup_logger

logger: logging.Logger = setup_logger("builder")


class PipelineBuilder:
    """
    Builder fluente para configurar e executar YouTubePipeline.

    Exemplo de uso:
        results = (
            PipelineBuilder(client)
            .from_popular(region="BR", max_results=50)
            .with_filters(min_views=10_000, min_likes=500)
            .limit(max_videos=30)
            .with_comments(max_per_video=100)
            .with_channels()
            .with_subtitles(languages=["pt", "en"])
            .checkpoint("minha_pipeline")
            .output_dir("data/output")
            .run()
        )
    """

    def __init__(self, client):
        self._client = client
        self._config = PipelineConfig()
        self._source: str = "popular"
        self._source_params: dict = {}
        self._checkpoint_name: str = "pipeline"

    def from_popular(self, region: str = "BR", max_results: int = 50) -> Self:
        self._source = "popular"
        self._source_params = {"region": region, "max_results": max_results}
        return self

    def from_category(
        self, category: str, region: str = "BR", max_results: int = 50
    ) -> Self:
        self._source = "category"
        self._source_params = {
            "category_name": category,
            "region": region,
            "max_results": max_results,
        }
        return self

    def from_search(self, query: str, max_results: int = 50) -> Self:
        self._source = "search"
        self._source_params = {"query": query, "max_results": max_results}
        return self

    def limit(self, max_videos: int) -> Self:
        self._config.max_videos = max_videos
        return self

    def with_filters(
        self,
        min_views: int = 0,
        min_likes: int = 0,
        languages: Optional[list[str]] = None,
    ) -> Self:
        self._config.min_views = min_views
        self._config.min_likes = min_likes
        if languages:
            self._config.languages = languages
        return self

    def with_comments(
        self,
        max_per_video: int = 50,
        max_replies: int = 10,
    ) -> Self:
        self._config.fetch_comments = True
        self._config.max_comments_per_video = max_per_video
        self._config.max_replies_per_comment = max_replies
        return self

    def without_comments(self) -> Self:
        self._config.fetch_comments = False
        return self

    def with_channels(self) -> Self:
        self._config.fetch_channel_details = True
        return self

    def without_channels(self) -> Self:
        self._config.fetch_channel_details = False
        return self

    def with_subtitles(self, languages: Optional[list[str]] = None) -> Self:
        self._config.fetch_subtitles = True
        if languages:
            self._config.languages = languages
        return self

    def checkpoint(self, name: str, save_every: int = 10) -> Self:
        self._checkpoint_name = name
        self._config.save_checkpoint_every = save_every
        return self

    def output_dir(self, path: str | Path) -> Self:
        self._config.output_dir = Path(path)
        return self

    def rate_limit(self, rps: float = 2.0, burst: int = 1) -> Self:
        self._config.rate_limit_rps = rps
        self._config.burst = burst
        return self

    def build(self) -> YouTubePipeline:
        """Retorna a pipeline configurada sem executá-la."""
        return YouTubePipeline(self._client, self._config)

    def run(self) -> dict:
        """Constrói e executa a pipeline imediatamente."""
        pipeline = self.build()
        return pipeline.run_complete_pipeline(
            source=self._source,
            source_params=self._source_params,
            checkpoint_name=self._checkpoint_name,
        )
