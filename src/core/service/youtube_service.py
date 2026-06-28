import logging
from src.core.setting.logger import setup_logger
from typing import List, Dict, Any, Optional
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

from src.core.models.api_data_classes import Comment, Video, Subtitle, Channel, LimitsConfig, SubtitleSegment
from src.core.service.youtube_requester import YouTubeAPIRequester, YouTubeAPIError
from src.core.pipeline import YouTubePipeline
from src.core.setting.registry import CATEGORY_MAP, VIDEO_FIELDS, CHANNEL_FIELDS, PAGE_SIZE
from src.core.service.youtube_parser import YouTubeDataParser

try:
    from youtube_transcript_api import (
        YouTubeTranscriptApi,
        NoTranscriptFound,
        TranscriptsDisabled,
        TranscriptList,
    )
    _TRANSCRIPT_API_AVAILABLE = True
except ImportError:
    _TRANSCRIPT_API_AVAILABLE = False

logger: logging.Logger = setup_logger("youtube_service")

class YouTubeDataService:
    _VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
    _COMMENTS_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
    _SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
    _CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"
    _PLAYLIST_ITEMS_URL = "https://www.googleapis.com/youtube/v3/playlistItems"

    def __init__(
        self,
        requester: YouTubeAPIRequester,
        parser: YouTubeDataParser,
        limits: Optional[LimitsConfig] = None,
    ) -> None:
        self._req = requester
        self._parser = parser
        self.limits = limits or LimitsConfig()

    def fetch_most_popular(
        self,
        region_code: str = "BR",
        max_results: int = 50,
        pages: int = 1,
        video_category_id: Optional[str] = None,
        max_items: Optional[int] = None,
    ) -> List[Video]:
        if not (1 <= max_results <= PAGE_SIZE):
            raise ValueError(f"max_results deve estar entre 1 e {PAGE_SIZE}.")

        cap = max_items or self.limits.max_videos
        videos: List[Video] = []
        page_token: Optional[str] = None

        for _ in range(pages):
            if cap and len(videos) >= cap:
                break
            params = {
                "part": "snippet,statistics,contentDetails,topicDetails",
                "chart": "mostPopular",
                "regionCode": region_code,
                "maxResults": max_results,
                "fields": VIDEO_FIELDS,
            }
            if page_token:
                params["pageToken"] = page_token
            if video_category_id:
                params["videoCategoryId"] = video_category_id

            data = self._req.get(self._VIDEOS_URL, params)
            videos.extend(self._parser.parse_videos(data))
            page_token = data.get("nextPageToken")
            if not page_token:
                break

        if cap:
            videos = videos[:cap]
        logger.info("fetch_most_popular: %d vídeos retornados.", len(videos))
        return videos

    def fetch_video_details(
        self,
        video_id: str,
        parts: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        if not video_id:
            raise ValueError("video_id não pode ser vazio.")

        requested_parts = parts or [
            "snippet", "statistics", "contentDetails", "status", "topicDetails"
        ]
        params = {"part": ",".join(requested_parts), "id": video_id}
        data = self._req.get(self._VIDEOS_URL, params)
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

        result = {
            "video_id": item.get("id"),
            "title": snippet.get("title"),
            "description": snippet.get("description"),
            "channel_id": snippet.get("channelId"),
            "channel_title": snippet.get("channelTitle"),
            "published_at": snippet.get("publishedAt"),
            "category_id": snippet.get("categoryId"),
            "tags": snippet.get("tags", []),
            "thumbnails": snippet.get("thumbnails", {}),
            "view_count": int(stats.get("viewCount", 0)) or None,
            "like_count": int(stats.get("likeCount", 0)) or None,
            "comment_count": int(stats.get("commentCount", 0)) or None,
            "duration": content.get("duration"),
            "definition": content.get("definition"),
            "caption_available": content.get("caption") == "true",
            "privacy_status": status.get("privacyStatus"),
            "topic_categories": topics.get("topicCategories", []),
        }
        logger.info(
            "fetch_video_details: '%s' | %s | %s views",
            result["title"], result["duration"], result["view_count"]
        )
        return result

    def fetch_videos_by_category(
        self,
        category: str,
        region_code: str = "BR",
        max_items: Optional[int] = None,
        pages: int = 1,
    ) -> List[Video]:
        _accent_map = str.maketrans("áàãâäéèêëíìîïóòõôöúùûüç", "aaaaaeeeeiiiiooooouuuuc")
        try:
            key = category.lower().translate(_accent_map).strip()
        except Exception:
            key = category[0].lower().translate(_accent_map).strip()
        category_id = CATEGORY_MAP.get(key)
        if not category_id:
            available = ", ".join(sorted(set(CATEGORY_MAP.keys())))
            raise ValueError(f"Categoria '{category}' não reconhecida. Opções: {available}")
        logger.info("fetch_videos_by_category: '%s' → id=%s", category, category_id)
        return self.fetch_most_popular(
            region_code=region_code,
            max_results=PAGE_SIZE,
            pages=pages,
            video_category_id=category_id,
            max_items=max_items,
        )
    def fetch_videos_by_channel_id(
        self,
        channel_id: str,
        videos_per_channel: int = 15,
    ) -> List[Video]:
        """
        Busca vídeos de um canal usando diretamente seu channel_id.
        Utiliza a playlist de uploads (UU + ID sem os dois primeiros caracteres).
        """
        if not channel_id:
            logger.warning("fetch_videos_by_channel_id: channel_id vazio.")
            return []

        # Playlist de uploads: "UU" + channel_id[2:] (padrão do YouTube)
        uploads_playlist_id = "UU" + channel_id[2:]

        # 1. Obter IDs dos vídeos da playlist de uploads
        playlist_params: Dict[str, Any] = {
            "key": self._api_key,
            "part": "contentDetails",
            "playlistId": uploads_playlist_id,
            "maxResults": videos_per_channel,
        }
        playlist_data = self._get(
            "https://www.googleapis.com/youtube/v3/playlistItems",
            playlist_params
        )
        video_ids: List[str] = [
            item["contentDetails"]["videoId"]
            for item in playlist_data.get("items", [])
            if item.get("contentDetails", {}).get("videoId")
        ]

        if not video_ids:
            logger.info("Nenhum vídeo encontrado para o canal: %s", channel_id)
            return []

        videos: List[Video] = []
        for chunk_start in range(0, len(video_ids), 50):
            chunk = video_ids[chunk_start : chunk_start + 50]
            video_params: Dict[str, Any] = {
                "key": self._api_key,
                "part": "snippet,statistics,contentDetails,topicDetails",
                "id": ",".join(chunk),
                "fields": self._VIDEO_FIELDS,
            }
            video_data = self._get(self._videos_url, video_params)
            videos.extend(self._parse_videos(video_data))

        logger.info("fetch_videos_by_channel_id: %s → %d vídeos.", channel_id, len(videos))
        return videos
    def fetch_videos_by_channel_names(
        self,
        channel_names: List[str],
        videos_per_channel: int = 15,
    ) -> Dict[str, List[Video]]:
        """Obtém vídeos recentes de canais usando a playlist de uploads (mais confiável)."""
        result: Dict[str, List[Video]] = {}
        for name in channel_names:
            logger.info("Resolvendo canal: %s", name)
            channel = self.fetch_channel_by_username(name)
            if channel is None:
                logger.warning("Canal não encontrado: %s", name)
                result[name] = []
                continue

            # Playlist de uploads: substitui 'UC' por 'UU' no ID
            uploads_playlist_id = "UU" + channel.channel_id[2:]
            playlist_params = {
                "part": "contentDetails",
                "playlistId": uploads_playlist_id,
                "maxResults": videos_per_channel,
            }
            playlist_data = self._req.get(self._PLAYLIST_ITEMS_URL, playlist_params)
            video_ids = [
                item["contentDetails"]["videoId"]
                for item in playlist_data.get("items", [])
                if item.get("contentDetails", {}).get("videoId")
            ]
            if not video_ids:
                logger.info("Nenhum vídeo encontrado para o canal: %s", name)
                result[name] = []
                continue

            videos = self._get_videos_by_ids(video_ids)
            logger.info("fetch_videos_by_channel_names: %s → %d vídeos.", name, len(videos))
            result[name] = videos
        return result

    def fetch_videos_by_channel_names_(
        self,
        channel_names: List[str],
        videos_per_channel: int = 15,
    ) -> Dict[str, List[Video]]:

        result: Dict[str, List[Video]] = {}

        for name in channel_names:
            logger.info("Resolvendo canal: %s", name)

            channel: Optional[Channel] = self.fetch_channel_by_username(name)
            if channel is None:
                logger.warning("Canal não encontrado: %s", name)
                result[name] = []
                continue

            uploads_playlist_id = "UU" + channel.channel_id[2:]

            playlist_params: Dict[str, Any] = {
                "key": self._api_key,
                "part": "contentDetails",
                "playlistId": uploads_playlist_id,
                "maxResults": videos_per_channel,
            }
            
            playlist_data: dict[str, Any] = self._get(
                "https://www.googleapis.com/youtube/v3/playlistItems", 
                playlist_params
            )
            
            video_ids: List[str] = [
                item["contentDetails"]["videoId"]
                for item in playlist_data.get("items", [])
                if item.get("contentDetails", {}).get("videoId")
            ]

            if not video_ids:
                logger.info("Nenhum vídeo encontrado para o canal: %s", name)
                result[name] = []
                continue

            videos: List[Video] = []
            for chunk_start in range(0, len(video_ids), 50):
                chunk = video_ids[chunk_start : chunk_start + 50]
                video_params: Dict[str, Any] = {
                    "key": self._api_key,
                    "part": "snippet,statistics,contentDetails,topicDetails",
                    "id": ",".join(chunk),
                    "fields": self._VIDEO_FIELDS,
                }
                video_data: dict[str, Any] = self._get(self._videos_url, video_params)
                videos.extend(self._parse_videos(video_data))

            logger.info(
                "fetch_videos_by_channel_names: %s → %d vídeos.", name, len(videos)
            )
            result[name] = videos

        return result
    def _get_videos_by_ids(self, video_ids: List[str]) -> List[Video]:
        """Busca detalhes de uma lista de IDs, dividindo em páginas de 50."""
        videos: List[Video] = []
        for i in range(0, len(video_ids), PAGE_SIZE):
            chunk = video_ids[i:i + PAGE_SIZE]
            params = {
                "part": "snippet,statistics,contentDetails,topicDetails",
                "id": ",".join(chunk),
                "fields": VIDEO_FIELDS,
            }
            data = self._req.get(self._VIDEOS_URL, params)
            videos.extend(self._parser.parse_videos(data))
        return videos

    def fetch_comments(
        self,
        video_id: str,
        max_pages: int = 1,
        order: str = "relevance",
        max_items: Optional[int] = None,
    ) -> List[Comment]:
        if not video_id:
            raise ValueError("video_id não pode ser vazio.")

        cap = max_items or self.limits.max_comments_per_video
        comments: List[Comment] = []
        page_token: Optional[str] = None

        for _ in range(max_pages):
            if cap and len(comments) >= cap:
                break
            params = {
                "part": "snippet",
                "videoId": video_id,
                "maxResults": 100,
                "order": order,
                "textFormat": "plainText",
            }
            if page_token:
                params["pageToken"] = page_token

            try:
                data = self._req.get(self._COMMENTS_URL, params)
            except YouTubeAPIError as exc:
                logger.warning("Comentários indisponíveis para %s: %s", video_id, exc)
                break

            comments.extend(self._parser.parse_comments(video_id, data))
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
        if not channel_ids:
            return []

        cap = max_items or self.limits.max_channels
        ids_to_fetch = channel_ids[:cap] if cap else channel_ids
        channels: List[Channel] = []

        for i in range(0, len(ids_to_fetch), PAGE_SIZE):
            chunk = ids_to_fetch[i:i + PAGE_SIZE]
            params = {
                "part": "snippet,statistics",
                "id": ",".join(chunk),
                "fields": CHANNEL_FIELDS,
                "maxResults": PAGE_SIZE,
            }
            data = self._req.get(self._CHANNELS_URL, params)
            channels.extend(self._parser.parse_channels(data))

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
        if not query:
            raise ValueError("query não pode ser vazia.")
        if not (1 <= max_results <= PAGE_SIZE):
            raise ValueError(f"max_results deve estar entre 1 e {PAGE_SIZE}.")

        cap = max_items or self.limits.max_channels
        channel_ids: List[str] = []
        page_token: Optional[str] = None

        for _ in range(pages):
            if cap and len(channel_ids) >= cap:
                break
            params = {
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

            data = self._req.get(self._SEARCH_URL, params)
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
        params = {
            "part": "snippet,statistics",
            "forHandle": username.lstrip("@"),
            "fields": CHANNEL_FIELDS,
            "maxResults": 1,
        }
        data = self._req.get(self._CHANNELS_URL, params)
        channels = self._parser.parse_channels(data)
        return channels[0] if channels else None

    def fetch_subtitles(
        self,
        video_id: str,
        languages: Optional[List[str]] = None,
        include_generated: bool = True,
    ) -> Optional[Subtitle]:
        if not _TRANSCRIPT_API_AVAILABLE:
            raise RuntimeError("youtube-transcript-api não está instalada.")
        if not video_id:
            raise ValueError("video_id não pode ser vazio.")

        preferred = languages or ["pt", "pt-BR", "en"]
        try:
            transcript_list = YouTubeTranscriptApi().list(video_id)
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
            segments = [
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
                video_id, result.language, result.is_generated, len(segments),
            )
            return result

        except TranscriptsDisabled:
            logger.warning("Legendas desabilitadas para o vídeo %s.", video_id)
            return None
        except Exception as exc:
            logger.exception("Erro ao obter legendas de %s: %s", video_id, exc)
            return None

    def fetch_subtitles_batch(
        self,
        video_ids: List[str],
        languages: Optional[List[str]] = None,
        include_generated: bool = True,
    ) -> List[Subtitle]:
        results: List[Subtitle] = []
        for idx, vid in enumerate(video_ids, start=1):
            logger.info("Legendas %d/%d – %s", idx, len(video_ids), vid)
            sub = self.fetch_subtitles(vid, languages=languages, include_generated=include_generated)
            if sub:
                results.append(sub)
        logger.info("fetch_subtitles_batch: %d/%d vídeos com legenda.", len(results), len(video_ids))
        return results
