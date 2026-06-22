from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class IYouTubePipeline(ABC):
    """
    Interface para pipelines de extração de dados do YouTube.

    Define o contrato para descoberta de vídeos, enriquecimento com detalhes,
    coleta de comentários, legendas e dados de canais, com controle de quota,
    checkpoints e filtros.
    """

    @abstractmethod
    def extract_videos_popular(
        self, region: str = "BR", max_results: int = 50
    ) -> List[dict]:
        """
        Obtém os vídeos em alta (trending) em uma região específica.
        Custo estimado de quota: gratuito (feed público) ou 1 unidade.

        Args:
            region: Código da região (ex: 'BR', 'US').
            max_results: Número máximo de vídeos a retornar.

        Returns:
            Lista de dicionários com informações básicas dos vídeos populares.
        """

    @abstractmethod
    def extract_videos_by_category(
        self, category_name: str, region: str = "BR", max_results: int = 50
    ) -> List[dict]:
        """
        Busca vídeos associados a uma categoria (ex: 'Music', 'Gaming').
        Custo estimado: 2 unidades (1 para categoria + 1 para listagem).

        Args:
            category_name: Nome da categoria (sensível à grafia da API).
            region: Código da região.
            max_results: Número máximo de vídeos.

        Returns:
            Lista de dicionários com os vídeos encontrados na categoria.
        """

    @abstractmethod
    def search_videos(self, query: str, max_results: int = 50) -> List[dict]:
        """
        Realiza uma pesquisa por palavra-chave. Operação cara!
        Custo: 100 unidades por chamada.

        Args:
            query: Termo de busca.
            max_results: Número máximo de resultados.

        Returns:
            Lista de vídeos correspondentes à consulta.
        """

    @abstractmethod
    def enrich_video_details(self, video_ids: List[str]) -> List[dict]:
        """
        Enriquece vídeos com estatísticas completas (visualizações, curtidas, etc.).
        Custo: 1 unidade para cada lote de 50 vídeos.

        Args:
            video_ids: Lista de IDs dos vídeos a enriquecer.

        Returns:
            Lista de dicionários com os detalhes completos dos vídeos.
        """

    @abstractmethod
    def extract_comments(self, video_id: str) -> List[dict]:
        """
        Coleta os comentários principais de um vídeo.
        Custo: 1 unidade por página de até 100 comentários.

        Args:
            video_id: ID do vídeo.

        Returns:
            Lista de comentários do vídeo.
        """

    @abstractmethod
    def enrich_channel_details(self, channel_ids: List[str]) -> List[dict]:
        """
        Obtém informações detalhadas dos canais (título, inscritos, avatar, etc.).
        Custo: 1 unidade para cada lote de até 50 canais.

        Args:
            channel_ids: Lista de IDs dos canais.

        Returns:
            Lista de dicionários com os dados completos dos canais solicitados.
        """

    @abstractmethod
    def extract_subtitles(self, video_ids: List[str]) -> List[dict]:
        """
        Extrai legendas (CC) dos vídeos nos idiomas configurados.
        Custo: 50 unidades por vídeo (use com moderação).

        Args:
            video_ids: Lista de IDs dos vídeos.

        Returns:
            Legendas baixadas.
        """

    @abstractmethod
    def filter_videos(self, videos: List[dict]) -> List[dict]:
        """
        Aplica filtros de qualidade (visualizações e curtidas mínimas) sobre a lista.

        Args:
            videos: Lista de vídeos a filtrar.

        Returns:
            Vídeos que atendem aos critérios definidos na configuração.
        """

    @abstractmethod
    def run_complete_pipeline(
        self,
        source: str = "popular",
        source_params: Optional[dict] = None,
        checkpoint_name: str = "pipeline",
    ) -> Dict[str, List[dict]]:
        """
        Executa todas as fases do pipeline: descoberta, enriquecimento, comentários,
        canais e legendas, salvando resultados parciais e finais.

        Args:
            source: Fonte de descoberta ('popular', 'category' ou 'search').
            source_params: Parâmetros adicionais para a função de descoberta escolhida.
            checkpoint_name: Nome base para arquivos de checkpoint.

        Returns:
            Dicionário com as chaves 'videos', 'comments', 'channels' e 'subtitles'.
        """
