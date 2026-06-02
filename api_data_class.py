from numba.core.types import Any
from dataclasses import asdict
from altair import Dict
from dataclasses import dataclass, asdict
from altair.utils import Optional
import re
from typing import List


class YouTubeAPIError(Exception):
    """Erro genérico ao comunicar com a YouTube API."""


class YouTubeAuthError(YouTubeAPIError):
    """Chave de API inválida ou ausente (HTTP 401)."""


class YouTubeQuotaError(YouTubeAPIError):
    """Cota diária da API esgotada (HTTP 403)."""

class CommentsDisabledError(YouTubeAPIError):
     """Não possui comentário, bloqueado pelo autor do vídeo (HTTP 403)."""

@dataclass
class RateLimitConfig:
    requests_per_second: float = 5.0
    burst: int = 1

    def __post_init__(self) -> None:
        if self.requests_per_second < 0:
            raise ValueError("requests_per_second deve ser >= 0.")
        if self.burst < 1:
            raise ValueError("burst deve ser >= 1.")


@dataclass
class LimitsConfig:
    max_videos: int = None
    max_comments_per_video: int = None
    max_channels: int = None
    max_comments: int = None
    max_api_calls: int = None


@dataclass
class Video:
    video_id: str
    title: Optional[str]
    channel_title: Optional[str]
    channel_id: Optional[str]
    published_at: Optional[str]
    category_id: Optional[str]
    thumbnail: Optional[str]
    view_count: Optional[int]
    like_count: Optional[int]
    comment_count: Optional[int]
    tags: Optional[str]
    duration: Optional[str]

    def to_dict(self):
        return asdict(self)

@dataclass
class Comment:
    video_id: str
    comment_thread_id: Optional[str]
    comment_id: Optional[str]
    author: Optional[str]
    text: Optional[str]
    like_count: int = 0
    published_at: Optional[str] = None
    updated_at: Optional[str] = None
    total_reply_count: int = 0
    video_title: Optional[str] = None
    channel_title: Optional[str] = None
    video_view_count: Optional[int] = None
    video_like_count: Optional[int] = None
    video_comment_count: Optional[int] = None

    def to_dict(self):
        return asdict(self)

@dataclass
class Channel:
    channel_id: str
    title: Optional[str]
    description: Optional[str]
    custom_url: Optional[str]
    published_at: Optional[str]
    country: Optional[str]
    thumbnail: Optional[str]
    view_count: Optional[int]
    subscriber_count: Optional[int]
    video_count: Optional[int]
    hidden_subscriber_count: bool = False

    def to_dict(self):
        return asdict(self)

@dataclass
class SubtitleSegment:
    text: str
    start: float
    duration: float

    # def to_dict(self):
    #     return {"text": self.text, "start": self.start, "duration": self.duration}


@dataclass
class Subtitle:
    video_id: str
    language: str
    language_name: str
    is_generated: bool
    segments: List[SubtitleSegment]

    @property
    def full_text(self) -> str:
        return " ".join(
            re.sub(r"\s+", " ", s.text).strip() for s in self.segments if s.text.strip()
        )

    @property
    def to_dict(self):
        return {
            "video_id": self.video_id,
            "language": self.language,
            "language_name": self.language_name,
            "is_generated": self.is_generated,
            "segments": [segment.to_dict() for segment in self.segments],
            "full_text": self.full_text,
        }
