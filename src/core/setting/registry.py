from src.core.models.page import Page
from typing import Dict
from src.views import intro_render, scrapper_render, sql_render,request_render

PAGES: list[Page] = [
    Page(name="Introdução", icon="house-fill", render=intro_render),
    Page(name="Scrapper", icon="search", render=scrapper_render),
    Page(name="SQL View", icon="table", render=sql_render),
    Page(name="Request API", icon="cloud-arrow-up", render=request_render)
]

VIDEO_FIELDS = (
    "nextPageToken,"
    "items("
    "id,snippet(title,description,channelId,channelTitle,publishedAt,categoryId,"
    "tags,thumbnails(default(url))),"
    "contentDetails(duration,definition,caption),"
    "statistics(viewCount,likeCount,commentCount,favoriteCount),"
    "topicDetails(topicCategories)"
    ")"
)

CHANNEL_FIELDS = (
    "nextPageToken,"
    "items(id,snippet(title,description,customUrl,publishedAt,country,"
    "thumbnails(default(url))),"
    "statistics(viewCount,subscriberCount,hiddenSubscriberCount,videoCount))"
)

CATEGORY_MAP: Dict[str, str] = {
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
    "educacao": "27",
    "Educação": "27",
    "ciencia": "28",
    "tecnologia": "28",
    "tech": "28",
    "ong": "29",
}

PAGE_SIZE = 50
