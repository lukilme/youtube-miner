from api_data_class import SubtitleSegment
from api_data_class import LimitsConfig
from api_data_class import RateLimitConfig
from logging import Logger
import csv
import json
import logging
import math
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from api_data_class import (
    Comment,
    Video,
    Subtitle,
    Channel,
    YouTubeAuthError,
    YouTubeQuotaError,
    YouTubeAPIError,
)
import requests

from dotenv import load_dotenv

try:
    # as vezes sai do ar
    from youtube_transcript_api import (
        YouTubeTranscriptApi,
        NoTranscriptFound,
        TranscriptsDisabled,
        TranscriptList,
    )

    _TRANSCRIPT_API_AVAILABLE = True
except ImportError:
    _TRANSCRIPT_API_AVAILABLE = False

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger: Logger = logging.getLogger(__name__)


class YouTubeClient:
    """
    Cliente para a YouTube Data API v3.
    """

    _DEFAULT_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
    _DEFAULT_COMMENTS_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
    _DEFAULT_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
    _DEFAULT_CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"

    _VIDEO_FIELDS = (
        "nextPageToken,"
        "items(id,"
        "snippet(title,channelId,channelTitle,publishedAt,categoryId,"
        "thumbnails(default(url))),"
        "statistics(viewCount,likeCount,commentCount))"
    )

    _CHANNEL_FIELDS = (
        "nextPageToken,"
        "items(id,"
        "snippet(title,description,customUrl,publishedAt,country,"
        "thumbnails(default(url))),"
        "statistics(viewCount,subscriberCount,hiddenSubscriberCount,videoCount))"
    )

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
        resolved_key: str = api_key or os.getenv("YOUTUBE_API_KEY", "").strip()
        if not resolved_key:
            raise YouTubeAuthError(
                "api_key não fornecida. Passe o argumento api_key ou defina a variável de ambiente YOUTUBE_API_KEY."
            )

        self._api_key = resolved_key
        self._videos_url = (
            api_url or os.getenv("YOUTUBE_API_URL", self._DEFAULT_VIDEOS_URL).strip()
        )
        self._comments_url = self._DEFAULT_COMMENTS_URL
        self._search_url = self._DEFAULT_SEARCH_URL
        self._channels_url = self._DEFAULT_CHANNELS_URL

        self.timeout = timeout
        self.retries = retries
        self.backoff_base = backoff_base
        self.rate_limit = rate_limit or RateLimitConfig()
        self.limits = limits or LimitsConfig()

        self._session = requests.Session()
        self._last_request_ts = 0.0
        self._burst_tokens = self.rate_limit.burst

    def fetch_most_popular(
        self,
        region_code: str = "BR",
        max_results: int = 50,
        pages: int = 1,
        video_category_id: Optional[str] = None,
        max_items: Optional[int] = None,
    ) -> List[Video]:
        """
        Retorna vídeos mais populares de uma região.
        """
        if not (1 <= max_results <= 50):
            raise ValueError("max_results deve estar entre 1 e 50.")

        cap: int | None = max_items or self.limits.max_videos
        videos: List[Video] = []
        page_token: Optional[str] = None

        for _ in range(pages):
            if cap and len(videos) >= cap:
                break

            params: Dict[str, Any] = {
                "key": self._api_key,
                "part": "snippet,statistics",
                "chart": "mostPopular",
                "regionCode": region_code,
                "maxResults": max_results,
                "fields": self._VIDEO_FIELDS,
            }
            if page_token:
                params["pageToken"] = page_token
            if video_category_id:
                params["videoCategoryId"] = video_category_id

            data: dict[str, Any] = self._get(self._videos_url, params)
            videos.extend(self._parse_videos(data))
            page_token = data.get("nextPageToken")

            if not page_token:
                break

        if cap:
            videos = videos[:cap]

        logger.info("fetch_most_popular: %d vídeos retornados.", len(videos))
        return videos

    def fetch_comments(
        self,
        video_id: str,
        max_pages: int = 1,
        order: str = "relevance",
        max_items: Optional[int] = None,
    ) -> List[Comment]:
        """
        Retorna comentários top-level de um vídeo.
        """
        if not video_id:
            raise ValueError("video_id não pode ser vazio.")

        cap: int | None = max_items or self.limits.max_comments_per_video
        comments: List[Comment] = []
        page_token: Optional[str] = None

        for _ in range(max_pages):
            if cap and len(comments) >= cap:
                break

            params: Dict[str, Any] = {
                "key": self._api_key,
                "part": "snippet",
                "videoId": video_id,
                "maxResults": 100,
                "order": order,
                "textFormat": "plainText",
            }
            if page_token:
                params["pageToken"] = page_token

            try:
                data: dict[str, Any] = self._get(self._comments_url, params)
            except YouTubeAPIError as exc:
                logger.warning("Comentários indisponíveis para %s: %s", video_id, exc)
                break

            comments.extend(self._parse_comments(video_id, data))
            page_token = data.get("nextPageToken")

            if not page_token:
                break

        if cap:
            comments = comments[:cap]

        return comments

    def fetch_channels_by_ids(
        self,
        channel_ids: List[str],
        max_items: Optional[int] = None,
    ) -> List[Channel]:
        """
        Retorna detalhes de canais a partir de uma lista de IDs.
        """
        if not channel_ids:
            return []

        cap: int | None = max_items or self.limits.max_channels
        ids_to_fetch: list[str] = channel_ids[:cap] if cap else channel_ids
        channels: List[Channel] = []

        for chunk_start in range(0, len(ids_to_fetch), 50):
            chunk: list[str] = ids_to_fetch[chunk_start : chunk_start + 50]
            params: Dict[str, Any] = {
                "key": self._api_key,
                "part": "snippet,statistics",
                "id": ",".join(chunk),
                "fields": self._CHANNEL_FIELDS,
                "maxResults": 50,
            }
            data: dict[str, Any] = self._get(self._channels_url, params)
            channels.extend(self._parse_channels(data))

        logger.info("fetch_channels_by_ids: %d canais retornados.", len(channels))
        return channels

    def search_channels(
        self,
        query: str,
        max_results: int = 25,
        pages: int = 1,
        region_code: Optional[str] = None,
        language: Optional[str] = None,
        max_items: Optional[int] = None,
    ) -> List[Channel]:
        """
        Busca canais por termo de texto e retorna seus detalhes completos.
        """
        if not query:
            raise ValueError("query não pode ser vazia.")
        if not (1 <= max_results <= 50):
            raise ValueError("max_results deve estar entre 1 e 50.")

        cap: int | None = max_items or self.limits.max_channels
        channel_ids: List[str] = []
        page_token: Optional[str] = None

        for _ in range(pages):
            if cap and len(channel_ids) >= cap:
                break

            params: Dict[str, Any] = {
                "key": self._api_key,
                "part": "id",
                "type": "channel",
                "q": query,
                "maxResults": max_results,
                "fields": "nextPageToken,items(id(channelId))",
            }
            if page_token:
                params["pageToken"] = page_token
            if region_code:
                params["regionCode"] = region_code
            if language:
                params["relevanceLanguage"] = language

            data: dict[str, Any] = self._get(self._search_url, params)
            for item in data.get("items", []):
                cid = item.get("id", {}).get("channelId")
                if cid:
                    channel_ids.append(cid)

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        if cap:
            channel_ids = channel_ids[:cap]

        if not channel_ids:
            logger.info("search_channels: nenhum canal encontrado para '%s'.", query)
            return []

        return self.fetch_channels_by_ids(channel_ids, max_items=cap)

    def fetch_channel_by_username(self, username: str) -> Optional[Channel]:
        """
        Busca um canal pelo handle/username (ex.: "@LinusTechTips" ou "LinusTechTips").
        """
        params: Dict[str, Any] = {
            "key": self._api_key,
            "part": "snippet,statistics",
            "forHandle": username.lstrip("@"),
            "fields": self._CHANNEL_FIELDS,
            "maxResults": 1,
        }
        data: dict[str, Any] = self._get(self._channels_url, params)
        channels: list[Channel] = self._parse_channels(data)
        return channels[0] if channels else None

    def fetch_subtitles(
        self,
        video_id: str,
        languages: Optional[List[str]] = None,
        include_generated: bool = True,
    ) -> Optional[Subtitle]:
        """
        Retorna a legenda de um vídeo no idioma preferido disponível.
        """
        if not _TRANSCRIPT_API_AVAILABLE:
            raise RuntimeError(
                "A biblioteca 'youtube-transcript-api' não está instalada. "
                "Execute: pip install youtube-transcript-api"
            )

        if not video_id:
            raise ValueError("video_id não pode ser vazio.")

        preferred: list[str] = languages or ["pt", "pt-BR", "en"]

        try:
            transcript_list: TranscriptList = YouTubeTranscriptApi().list(video_id)
            logger.info(transcript_list)
            transcript = None
            try:
                transcript = transcript_list.find_manually_created_transcript(preferred)
            except NoTranscriptFound:
                pass

            if transcript is None and include_generated:
                try:
                    transcript = transcript_list.find_generated_transcript(preferred)
                except NoTranscriptFound:
                    pass

            if transcript is None:
                transcript = next(iter(transcript_list))
                if preferred:
                    try:
                        transcript = transcript.translate(preferred[0])
                    except Exception:
                        pass
            raw = transcript.fetch()
            segments: list[SubtitleSegment] = [
                SubtitleSegment(
                    text=entry.text,
                    start=entry.start,
                    duration=entry.duration,
                )
                for entry in raw
            ]

            result = Subtitle(
                video_id=video_id,
                language=transcript.language_code,
                language_name=transcript.language,
                is_generated=transcript.is_generated,
                segments=segments,
            )

            logger.info(
                "fetch_subtitles: %s | idioma=%s | gerada=%s | %d segmentos",
                video_id,
                result.language,
                result.is_generated,
                len(segments),
            )
            return result

        except TranscriptsDisabled:
            logger.warning("Legendas desabilitadas para o vídeo %s.", video_id)
            return None
        except Exception as exc:
            print(exec)
            logger.warning("Não foi possível obter legendas de %s", video_id)
            return None

    def fetch_subtitles_batch(
        self,
        video_ids: List[str],
        languages: Optional[List[str]] = None,
        include_generated: bool = True,
    ) -> List[Subtitle]:
        """
        Retorna legendas de múltiplos vídeos, ignorando os sem legenda.
        """
        results: List[Subtitle] = []
        for idx, vid in enumerate(video_ids, start=1):
            logger.info("Legendas %d/%d – %s", idx, len(video_ids), vid)
            sub: Subtitle | None = self.fetch_subtitles(
                vid, languages=languages, include_generated=include_generated
            )
            if sub:
                results.append(sub)
        logger.info(
            "fetch_subtitles_batch: %d/%d vídeos com legenda.",
            len(results),
            len(video_ids),
        )
        return results

    def run_pipeline(
        self,
        total_videos: int = 50,
        region: str = "BR",
        comments_pages: int = 1,
        video_category_id: Optional[str] = "21",
        include_channels: bool = False,
        output_dir: str = "output",
        fmt: str = "csv",
    ) -> None:
        """
        Pipeline completo: vídeos → comentários → (canais) → arquivos.
        """
        logger.info("Pipeline iniciado: %d vídeos / região %s", total_videos, region)

        effective_total = (
            min(total_videos, self.limits.max_videos)
            if self.limits.max_videos
            else total_videos
        )

        pages_needed: int = math.ceil(effective_total / 50)
        videos: list[Video] = self.fetch_most_popular(
            region_code=region,
            max_results=50,
            pages=pages_needed,
            video_category_id=video_category_id,
            max_items=effective_total,
        )
        logger.info("%d vídeos obtidos.", len(videos))

        all_comments: List[Comment] = []
        for idx, video in enumerate(videos, start=1):
            logger.info("Comentários %d/%d – %s", idx, len(videos), video.video_id)
            comments: list[Comment] = self.fetch_comments(
                video_id=video.video_id,
                max_pages=comments_pages,
            )
            for c in comments:
                c.video_title = video.title
                c.channel_title = video.channel_title
                c.video_view_count = video.view_count
                c.video_like_count = video.like_count
                c.video_comment_count = video.comment_count
            all_comments.extend(comments)

        channels: List[Channel] = []
        if include_channels:
            unique_ids: list[str] = list({v.channel_id for v in videos if v.channel_id})
            logger.info("Buscando detalhes de %d canais únicos.", len(unique_ids))
            channels = self.fetch_channels_by_ids(unique_ids)

        region_lower = region.lower()
        save = self.save_csv if fmt == "csv" else self.save_json

        save(
            [v.to_dict() for v in videos],
            os.path.join(output_dir, f"youtube_videos_{region_lower}.{fmt}"),
        )
        save(
            [c.to_dict() for c in all_comments],
            os.path.join(output_dir, f"youtube_comments_{region_lower}.{fmt}"),
        )
        if channels:
            save(
                [ch.to_dict() for ch in channels],
                os.path.join(output_dir, f"youtube_channels_{region_lower}.{fmt}"),
            )

        logger.info("Pipeline finalizado. Arquivos salvos em '%s'.", output_dir)

    def fetch_videos_by_category(
        self,
        category: str,
        region_code: str = "BR",
        max_items: Optional[int] = None,
        pages: int = 1,
    ) -> List[Video]:
        """
        Retorna vídeos populares filtrando por nome de categoria em português.
        """
        _CATEGORY_MAP: Dict[str, str] = {
            "filme": "1",
            "filmes": "1",
            "animacao": "1",
            "automovel": "2",
            "automoveis": "2",
            "veiculo": "2",
            "musica": "10",
            "animal": "15",
            "animais": "15",
            "pet": "15",
            "esporte": "17",
            "esportes": "17",
            "viagem": "19",
            "viagens": "19",
            "gaming": "20",
            "jogos": "20",
            "jogo": "20",
            "game": "20",
            "vlog": "22",
            "pessoas": "22",
            "comedia": "23",
            "humor": "23",
            "entretenimento": "24",
            "noticias": "25",
            "politica": "25",
            "tutorial": "26",
            "estilo": "26",
            "beleza": "26",
            "ciencia": "28",
            "tecnologia": "28",
            "tech": "28",
            "ong": "29",
        }

        _accent_map: dict[int, int] = str.maketrans(
            "áàãâäéèêëíìîïóòõôöúùûüç", "aaaaaeeeeiiiiooooouuuuc"
        )
        print(category)
        try:
            key: str = category.lower().translate(_accent_map).strip()
        except:
            key: str = category[0].lower().translate(_accent_map).strip()
        category_id: str | None = _CATEGORY_MAP.get(key)
        if not category_id:
            available: str = ", ".join(sorted(set(_CATEGORY_MAP.keys())))
            raise ValueError(
                f"Categoria '{category}' não reconhecida. "
                f"Opções disponíveis: {available}"
            )

        logger.info(
            "fetch_videos_by_category: '%s' → category_id=%s / região=%s",
            category,
            category_id,
            region_code,
        )
        return self.fetch_most_popular(
            region_code=region_code,
            max_results=50,
            pages=pages,
            video_category_id=category_id,
            max_items=max_items,
        )

    def fetch_video_details(
        self,
        video_id: str,
        parts: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retorna metadados completos de um vídeo específico.
        """
        if not video_id:
            raise ValueError("video_id não pode ser vazio.")

        requested_parts: list[str] = parts or [
            "snippet",
            "statistics",
            "contentDetails",
            "status",
            "topicDetails",
        ]

        params: Dict[str, Any] = {
            "key": self._api_key,
            "part": ",".join(requested_parts),
            "id": video_id,
        }

        data: dict[str, Any] = self._get(self._videos_url, params)
        items = data.get("items", [])
        if not items:
            logger.warning("fetch_video_details: vídeo '%s' não encontrado.", video_id)
            return None

        item = items[0]
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        content = item.get("contentDetails", {})
        status = item.get("status", {})
        topics = item.get("topicDetails", {})
        localizations = item.get("localizations", {})
        recording = item.get("recordingDetails", {})

        result: Dict[str, Any] = {
            "video_id": item.get("id"),
            "title": snippet.get("title"),
            "description": snippet.get("description"),
            "channel_id": snippet.get("channelId"),
            "channel_title": snippet.get("channelTitle"),
            "published_at": snippet.get("publishedAt"),
            "category_id": snippet.get("categoryId"),
            "default_language": snippet.get("defaultLanguage"),
            "default_audio_language": snippet.get("defaultAudioLanguage"),
            "tags": snippet.get("tags", []),
            "live_broadcast_content": snippet.get("liveBroadcastContent"),
            "thumbnails": snippet.get("thumbnails", {}),
            "view_count": int(stats["viewCount"]) if "viewCount" in stats else None,
            "like_count": int(stats["likeCount"]) if "likeCount" in stats else None,
            "comment_count": (
                int(stats["commentCount"]) if "commentCount" in stats else None
            ),
            "favorite_count": (
                int(stats["favoriteCount"]) if "favoriteCount" in stats else None
            ),
            "duration": content.get("duration"),
            "dimension": content.get("dimension"),
            "definition": content.get("definition"),
            "caption_available": content.get("caption") == "true",
            "licensed_content": content.get("licensedContent"),
            "projection": content.get("projection"),
            "age_restricted": content.get("contentRating", {}).get("ytRating")
            == "ytAgeRestricted",
            "privacy_status": status.get("privacyStatus"),
            "upload_status": status.get("uploadStatus"),
            "embeddable": status.get("embeddable"),
            "license": status.get("license"),
            "made_for_kids": status.get("madeForKids"),
            "self_declared_made_for_kids": status.get("selfDeclaredMadeForKids"),
            "topic_categories": topics.get("topicCategories", []),
            "relevant_topic_ids": topics.get("relevantTopicIds", []),
            "localizations": localizations,
            "recording_date": recording.get("recordingDate"),
            "recording_location": recording.get("location"),
        }

        logger.info(
            "fetch_video_details: '%s' | %s | %s views",
            result["title"],
            result["duration"],
            result["view_count"],
        )
        return result

    @staticmethod
    def save_csv(rows: List[Dict[str, Any]], filepath: str) -> None:
        """Salva lista de dicionários em CSV (UTF-8 com BOM)."""
        if not rows:
            logger.info("Nada para salvar em %s.", filepath)
            return
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        logger.info("CSV salvo: %s (%d linhas).", filepath, len(rows))

    @staticmethod
    def save_json(rows: List[Dict[str, Any]], filepath: str) -> None:
        """Salva lista de dicionários em JSON indentado."""
        if not rows:
            logger.info("Nada para salvar em %s.", filepath)
            return
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        logger.info("JSON salvo: %s (%d registros).", filepath, len(rows))

    def _throttle(self) -> None:
        """Aplica rate-limiting (token bucket simplificado) antes de cada req."""
        if self.rate_limit.requests_per_second <= 0:
            return

        min_interval = 1.0 / self.rate_limit.requests_per_second
        now = time.monotonic()
        elapsed = now - self._last_request_ts

        if self._burst_tokens > 0:
            self._burst_tokens -= 1
        else:
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)

        self._last_request_ts = time.monotonic()

        if elapsed >= min_interval and self._burst_tokens < self.rate_limit.burst:
            self._burst_tokens = min(self._burst_tokens + 1, self.rate_limit.burst)

    def _get(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executa GET com rate-limit e retry com backoff exponencial."""
        last_exc: Exception = RuntimeError("Sem tentativas.")
        for attempt in range(1, self.retries + 1):
            try:
                self._throttle()
                resp = self._session.get(url, params=params, timeout=self.timeout)
                self._raise_for_status(resp)
                return resp.json()
            except (requests.RequestException, YouTubeAPIError) as exc:
                last_exc = exc
                if attempt < self.retries:
                    wait = self.backoff_base ** (attempt - 1)
                    logger.warning(
                        "Tentativa %d/%d falhou (%s). Aguardando %.1fs…",
                        attempt,
                        self.retries,
                        exc,
                        wait,
                    )
                    time.sleep(wait)

        raise YouTubeAPIError(
            f"Falha após {self.retries} tentativas: {last_exc}"
        ) from last_exc

    @staticmethod
    def _raise_for_status(resp: requests.Response) -> None:
        if resp.status_code == 200:
            return
        body = resp.text[:500]
        if resp.status_code == 401:
            raise YouTubeAuthError(f"Não autorizado (401): {body}")
        if resp.status_code == 403:
            raise YouTubeQuotaError(f"Proibido/Cota (403): {body}")
        raise YouTubeAPIError(f"HTTP {resp.status_code}: {body}")

    @staticmethod
    def _parse_videos(data: Dict[str, Any]) -> List[Video]:
        videos: List[Video] = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            videos.append(
                Video(
                    video_id=item.get("id", ""),
                    title=snippet.get("title"),
                    channel_title=snippet.get("channelTitle"),
                    channel_id=snippet.get("channelId"),
                    published_at=snippet.get("publishedAt"),
                    category_id=snippet.get("categoryId"),
                    thumbnail=snippet.get("thumbnails", {})
                    .get("default", {})
                    .get("url"),
                    view_count=(
                        int(stats["viewCount"]) if "viewCount" in stats else None
                    ),
                    like_count=(
                        int(stats["likeCount"]) if "likeCount" in stats else None
                    ),
                    comment_count=(
                        int(stats["commentCount"]) if "commentCount" in stats else None
                    ),
                )
            )
        return videos

    @staticmethod
    def _parse_comments(video_id: str, data: Dict[str, Any]) -> List[Comment]:
        comments: List[Comment] = []
        for item in data.get("items", []):
            top = item.get("snippet", {}).get("topLevelComment", {})
            c = top.get("snippet", {})
            comments.append(
                Comment(
                    video_id=video_id,
                    comment_thread_id=item.get("id"),
                    comment_id=top.get("id"),
                    author=c.get("authorDisplayName"),
                    text=c.get("textDisplay"),
                    like_count=int(c["likeCount"]) if "likeCount" in c else 0,
                    published_at=c.get("publishedAt"),
                    updated_at=c.get("updatedAt"),
                    total_reply_count=item.get("snippet", {}).get("totalReplyCount", 0),
                )
            )
        return comments

    @staticmethod
    def _parse_channels(data: Dict[str, Any]) -> List[Channel]:
        channels: List[Channel] = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            channels.append(
                Channel(
                    channel_id=item.get("id", ""),
                    title=snippet.get("title"),
                    description=snippet.get("description"),
                    custom_url=snippet.get("customUrl"),
                    published_at=snippet.get("publishedAt"),
                    country=snippet.get("country"),
                    thumbnail=snippet.get("thumbnails", {})
                    .get("default", {})
                    .get("url"),
                    view_count=(
                        int(stats["viewCount"]) if "viewCount" in stats else None
                    ),
                    subscriber_count=(
                        int(stats["subscriberCount"])
                        if "subscriberCount" in stats
                        else None
                    ),
                    video_count=(
                        int(stats["videoCount"]) if "videoCount" in stats else None
                    ),
                    hidden_subscriber_count=stats.get("hiddenSubscriberCount", False),
                )
            )
        return channels


if __name__ == "__main__":
    client = YouTubeClient(
        rate_limit=RateLimitConfig(requests_per_second=3.0, burst=2),
        limits=LimitsConfig(max_videos=120, max_comments_per_video=100),
    )
    client.run_pipeline(
        total_videos=120,
        region="BR",
        comments_pages=1,
        include_channels=True,
        output_dir="output",
        fmt="csv",
    )
