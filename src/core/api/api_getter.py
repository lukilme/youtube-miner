import os
from typing import List, Dict, Any, Optional
from core.models.api_data_classes import (
    Comment,
    Video,
    Subtitle,
    Channel,
    RateLimitConfig,
    LimitsConfig,
    YouTubeAuthError,
)
from src.core.interface.youtube_client import IYouTubeClient
from src.core.service.youtube_service import YouTubeDataService, YouTubeDataParser
from src.core.service.youtube_requester import YouTubeAPIRequester
from src.core.export.data_exporter import DataExporter
from src.core.pipeline import YouTubePipeline
from src.core.setting.logger import setup_logger
import logging

logger: logging.Logger = setup_logger("config")


class YouTubeClient(IYouTubeClient):
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        timeout: int = 20,
        retries: int = 3,
        backoff_base: float = 2.0,
        rate_limit: Optional[RateLimitConfig] = None,
        limits: Optional[LimitsConfig] = None,
    ) -> None:
        resolved_key = api_key or os.getenv("YOUTUBE_API_KEY", "").strip()
        if not resolved_key:
            raise YouTubeAuthError(
                "api_key não fornecida. Passe o argumento api_key ou defina a variável de ambiente YOUTUBE_API_KEY."
            )
        requester = YouTubeAPIRequester(
            api_key=resolved_key,
            timeout=timeout,
            retries=retries,
            backoff_base=backoff_base,
            rate_config=rate_limit or RateLimitConfig(),
        )
        self._service = YouTubeDataService(
            requester=requester,
            parser=YouTubeDataParser(),
            limits=limits or LimitsConfig(),
        )
        self._pipeline = YouTubePipeline(self._service, DataExporter())

    # Delegar métodos públicos
    def fetch_most_popular(self, *args, **kwargs) -> List[Video]:
        return self._service.fetch_most_popular(*args, **kwargs)

    def fetch_comments(self, *args, **kwargs) -> List[Comment]:
        return self._service.fetch_comments(*args, **kwargs)

    def fetch_channels_by_ids(self, *args, **kwargs) -> List[Channel]:
        return self._service.fetch_channels_by_ids(*args, **kwargs)

    def search_channels(self, *args, **kwargs) -> List[Channel]:
        return self._service.search_channels(*args, **kwargs)

    def fetch_channel_by_username(self, *args, **kwargs) -> Optional[Channel]:
        return self._service.fetch_channel_by_username(*args, **kwargs)

    def fetch_subtitles(self, *args, **kwargs) -> Optional[Subtitle]:
        return self._service.fetch_subtitles(*args, **kwargs)

    def fetch_subtitles_batch(self, *args, **kwargs) -> List[Subtitle]:
        return self._service.fetch_subtitles_batch(*args, **kwargs)

    def fetch_videos_by_channel_names(self, *args, **kwargs) -> Dict[str, List[Video]]:
        return self._service.fetch_videos_by_channel_names(*args, **kwargs)

    def fetch_videos_by_category(self, *args, **kwargs) -> List[Video]:
        return self._service.fetch_videos_by_category(*args, **kwargs)

    def fetch_video_details(self, *args, **kwargs) -> Optional[Dict[str, Any]]:
        return self._service.fetch_video_details(*args, **kwargs)

    def run_pipeline(self, *args, **kwargs) -> None:
        self._pipeline.run(*args, **kwargs)

    # Métodos de exportação estáticos mantidos por compatibilidade
    @staticmethod
    def save_csv(rows: List[Dict[str, Any]], filepath: str) -> None:
        DataExporter.to_csv(rows, filepath)

    @staticmethod
    def save_json(rows: List[Dict[str, Any]], filepath: str) -> None:
        DataExporter.to_json(rows, filepath)
