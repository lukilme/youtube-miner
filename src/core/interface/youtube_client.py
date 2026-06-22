from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.core.models.api_data_classes import (
    Comment,
    Video,
    Subtitle,
    Channel,
)


class IYouTubeClient(ABC):
    """
    Interface descritiva para um cliente da YouTube Data API v3.
    Qualquer implementação concreta deve herdar desta classe e implementar todos os métodos abstratos.
    """

    @abstractmethod
    def fetch_most_popular(
        self,
        region_code: str = "BR",
        max_results: int = 50,
        pages: int = 1,
        video_category_id: Optional[str] = None,
        max_items: Optional[int] = None,
    ) -> List[Video]:
        """
        Retorna os vídeos mais populares de uma região.

        Args:
            region_code: Código ISO 3166-1 alpha-2 da região (padrão: 'BR').
            max_results: Máximo de resultados por página (1 a 50).
            pages: Número de páginas a buscar.
            video_category_id: ID da categoria de vídeos (opcional).
            max_items: Limite máximo de vídeos a retornar (opcional).

        Returns:
            Lista de objetos Video.
        """

    @abstractmethod
    def fetch_comments(
        self,
        video_id: str,
        max_pages: int = 1,
        order: str = "relevance",
        max_items: Optional[int] = None,
    ) -> List[Comment]:
        """
        Retorna os comentários top-level de um vídeo.

        Args:
            video_id: ID do vídeo.
            max_pages: Número máximo de páginas de comentários.
            order: Ordenação ('relevance' ou 'time').
            max_items: Limite máximo de comentários a retornar (opcional).

        Returns:
            Lista de objetos Comment.
        """

    @abstractmethod
    def fetch_channels_by_ids(
        self,
        channel_ids: List[str],
        max_items: Optional[int] = None,
    ) -> List[Channel]:
        """
        Retorna detalhes de canais a partir de uma lista de IDs.

        Args:
            channel_ids: Lista de IDs de canais.
            max_items: Limite máximo de canais a retornar (opcional).

        Returns:
            Lista de objetos Channel.
        """

    @abstractmethod
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

        Args:
            query: Termo de busca.
            max_results: Máximo de resultados por página (1 a 50).
            pages: Número de páginas a buscar.
            region_code: Código da região (opcional).
            language: Idioma para relevância (opcional).
            max_items: Limite máximo de canais a retornar (opcional).

        Returns:
            Lista de objetos Channel.
        """

    @abstractmethod
    def fetch_channel_by_username(self, username: str) -> Optional[Channel]:
        """
        Busca um canal pelo handle/username (ex.: '@LinusTechTips' ou 'LinusTechTips').

        Args:
            username: Nome de usuário ou handle do canal.

        Returns:
            Objeto Channel ou None se não encontrado.
        """

    @abstractmethod
    def fetch_subtitles(
        self,
        video_id: str,
        languages: Optional[List[str]] = None,
        include_generated: bool = True,
    ) -> Optional[Subtitle]:
        """
        Retorna a legenda de um vídeo no idioma preferido disponível.

        Args:
            video_id: ID do vídeo.
            languages: Lista de idiomas preferidos (ex.: ['pt', 'pt-BR', 'en']).
            include_generated: Se True, inclui legendas geradas automaticamente.

        Returns:
            Objeto Subtitle ou None se não houver legenda.
        """

    @abstractmethod
    def fetch_subtitles_batch(
        self,
        video_ids: List[str],
        languages: Optional[List[str]] = None,
        include_generated: bool = True,
    ) -> List[Subtitle]:
        """
        Retorna legendas de múltiplos vídeos, ignorando os que não possuem.

        Args:
            video_ids: Lista de IDs de vídeos.
            languages: Lista de idiomas preferidos.
            include_generated: Se True, inclui legendas geradas automaticamente.

        Returns:
            Lista de objetos Subtitle.
        """

    @abstractmethod
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

        Args:
            total_videos: Total de vídeos a processar.
            region: Código da região.
            comments_pages: Páginas de comentários por vídeo.
            video_category_id: ID da categoria de vídeos.
            include_channels: Se True, busca detalhes dos canais.
            output_dir: Diretório de saída.
            fmt: Formato do arquivo ('csv' ou 'json').
        """

    @abstractmethod
    def fetch_videos_by_category(
        self,
        category: str,
        region_code: str = "BR",
        max_items: Optional[int] = None,
        pages: int = 1,
    ) -> List[Video]:
        """
        Retorna vídeos populares filtrando por categoria (nome em português).

        Args:
            category: Nome da categoria (ex.: 'jogos', 'música', 'tecnologia').
            region_code: Código da região.
            max_items: Limite máximo de vídeos.
            pages: Número de páginas a buscar.

        Returns:
            Lista de objetos Video.
        """

    @abstractmethod
    def fetch_video_details(
        self,
        video_id: str,
        parts: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retorna metadados completos de um vídeo específico.

        Args:
            video_id: ID do vídeo.
            parts: Partes da resposta desejadas (ex.: ['snippet', 'statistics']).

        Returns:
            Dicionário com os metadados ou None se não encontrado.
        """

    @staticmethod
    @abstractmethod
    def save_csv(rows: List[Dict[str, Any]], filepath: str) -> None:
        """
        Salva uma lista de dicionários em CSV (UTF-8 com BOM).

        Args:
            rows: Lista de dicionários.
            filepath: Caminho do arquivo de destino.
        """

    @staticmethod
    @abstractmethod
    def save_json(rows: List[Dict[str, Any]], filepath: str) -> None:
        """
        Salva uma lista de dicionários em JSON indentado.

        Args:
            rows: Lista de dicionários.
            filepath: Caminho do arquivo de destino.
        """
