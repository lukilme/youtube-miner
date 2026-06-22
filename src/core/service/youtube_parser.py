from typing import List, Dict, Any
from src.core.models.api_data_classes import Comment, Video, Subtitle, Channel


class YouTubeDataParser:
    @staticmethod
    def parse_videos(data: Dict[str, Any]) -> List[Video]:
        videos = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            content = item.get("contentDetails", {})
            videos.append(
                Video(
                    video_id=item.get("id", ""),
                    title=snippet.get("title"),
                    channel_title=snippet.get("channelTitle"),
                    channel_id=snippet.get("channelId"),
                    published_at=snippet.get("publishedAt"),
                    category_id=snippet.get("categoryId"),
                    thumbnail=snippet.get("thumbnails", {}).get("default", {}).get("url"),
                    tags=snippet.get("tags", []),
                    duration=content.get("duration"),
                    view_count=int(stats["viewCount"]) if "viewCount" in stats else None,
                    like_count=int(stats["likeCount"]) if "likeCount" in stats else None,
                    comment_count=int(stats["commentCount"]) if "commentCount" in stats else None,
                )
            )
        return videos

    @staticmethod
    def parse_comments(video_id: str, data: Dict[str, Any]) -> List[Comment]:
        comments = []
        for item in data.get("items", []):
            top = item.get("snippet", {}).get("topLevelComment", {})
            snippet = top.get("snippet", {})
            comments.append(
                Comment(
                    video_id=video_id,
                    comment_thread_id=item.get("id"),
                    comment_id=top.get("id"),
                    author=snippet.get("authorDisplayName"),
                    text=snippet.get("textDisplay"),
                    like_count=int(snippet["likeCount"]) if "likeCount" in snippet else 0,
                    published_at=snippet.get("publishedAt"),
                    updated_at=snippet.get("updatedAt"),
                    total_reply_count=item.get("snippet", {}).get("totalReplyCount", 0),
                )
            )
        return comments

    @staticmethod
    def parse_channels(data: Dict[str, Any]) -> List[Channel]:
        channels = []
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
                    thumbnail=snippet.get("thumbnails", {}).get("default", {}).get("url"),
                    view_count=int(stats["viewCount"]) if "viewCount" in stats else None,
                    subscriber_count=int(stats["subscriberCount"]) if "subscriberCount" in stats else None,
                    video_count=int(stats["videoCount"]) if "videoCount" in stats else None,
                    hidden_subscriber_count=stats.get("hiddenSubscriberCount", False),
                )
            )
        return channels