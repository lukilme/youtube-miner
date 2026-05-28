from api_data_class import Subtitle
from numba.core.types import Any
from typing import List, Dict, Optional, Set
from pathlib import Path
import json
from api_getter import YouTubeClient
import time
from dataclasses import dataclass, field
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger: logging.Logger = logging.getLogger(__name__)


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


class YouTubePipeline:
    """
    Pipeline otimizada para extração de dados do YouTube.
    """

    def __init__(self, client, config: PipelineConfig):
        self.client: YouTubeClient = client
        self.config = config
        self.stats = PipelineStats()

        self.config.checkpoint_dir.mkdir(exist_ok=True)
        self.config.output_dir.mkdir(exist_ok=True)

        self.processed_video_ids: Set[str] = set()
        self.channel_cache: Dict[str, dict] = {}

    def load_checkpoint(self, checkpoint_name: str) -> Optional[dict]:
        """Carrega checkpoint se existir."""
        checkpoint_file = self.config.checkpoint_dir / f"{checkpoint_name}.json"
        if checkpoint_file.exists():
            logger.info(f"Carregando checkpoint: {checkpoint_file}")
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.processed_video_ids = set(data.get("processed_video_ids", []))
                return data
        return None

    def save_checkpoint(self, checkpoint_name: str, data: dict):
        """Salva checkpoint."""
        checkpoint_file = self.config.checkpoint_dir / f"{checkpoint_name}.json"
        data["processed_video_ids"] = list(self.processed_video_ids)
        data["timestamp"] = datetime.now().isoformat()
        data["stats"] = {
            "videos_processed": self.stats.videos_processed,
            "quota_used": self.stats.quota_used_estimate,
        }

        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Checkpoint salvo: {checkpoint_file}")

    def extract_videos_popular(
        self, region: str = "BR", max_results: int = 50
    ) -> List[dict]:
        """
        FASE 1: Descoberta de vídeos mais populares.
        Custo: Grátis (usa trending feed) ou baixo.
        """
        logger.info(f"Buscando vídeos populares ({region})...")
        videos = self.client.fetch_most_popular(
            region_code=region, max_results=max_results
        )
        self.stats.add_quota(1, "most_popular")
        logger.info(f"{len(videos)} vídeos populares encontrados")
        return videos

    def extract_videos_by_category(
        self, category_name: str, region: str = "BR", max_results: int = 50
    ) -> List[dict]:
        """
        FASE 1: Descoberta por categoria.
        Custo: 1 unit (lista) + 1 unit (vídeos).
        """

        videos = self.client.fetch_videos_by_category(
            category=category_name, region_code=region, max_items=max_results
        )
        self.stats.add_quota(2, f"category:{category_name}")
        logger.info(f"{len(videos)} vídeos encontrados")
        return videos

    def search_videos(self, query: str, max_results: int = 50) -> List[dict]:
        """
        FASE 1: Busca por termo (mais caro!).
        Custo: 100 units! Use com moderação.
        """
        logger.warning(f"ATENÇÃO: Search custa 100 units!")
        logger.info(f"Buscando vídeos: '{query}'...")

        self.stats.add_quota(100, f"search:{query}")
        logger.info(f"Busca concluída (CARO!)")
        return []

    def enrich_video_details(self, video_ids: List[str]) -> List[dict]:
        if not video_ids:
            return []
        logger.warning("CUSTO: 1 unit por 50 vídeos")
        logger.info(f"Enriquecendo detalhes de {len(video_ids)} vídeos...")
        all_videos = []

        for i in range(0, len(video_ids), self.config.video_batch_size):
            batch = video_ids[i : i + self.config.video_batch_size]

            new_batch = [vid for vid in batch if vid not in self.processed_video_ids]
            if not new_batch:
                continue

            try:
                videos = [self.client.fetch_video_details(vid) for vid in new_batch]
                videos = [v for v in videos if v]
                all_videos.extend(videos)

                self.stats.add_quota(len(new_batch), f"video_details_batch")
                self.processed_video_ids.update(new_batch)

                logger.info(f"  Batch {i // 50 + 1}: {len(videos)} vídeos")

            except Exception as e:
                logger.error(f"  Erro no batch {i // 50 + 1}: {e}")
                self.stats.errors.append(f"Video batch {i}: {str(e)}")

        return all_videos

    def extract_comments(self, video_id: str) -> List[dict]:
        if not self.config.fetch_comments:
            return []

        try:
            logger.warning("Custo: 1 unidade por página (100 cometários)")
            comments = self.client.fetch_comments(
                video_id=video_id,
                max_items=self.config.max_comments_per_video,
            )
            pages = (len(comments) // 100) + 1
            self.stats.add_quota(pages, f"comments:{video_id}")
            self.stats.comments_collected += len(comments)

            return comments

        except Exception as e:
            logger.error(f"  Erro ao buscar comentários de {video_id}: {e}")
            self.stats.errors.append(f"Comments {video_id}: {str(e)}")
            return []

    def enrich_channel_details(self, channel_ids: List[str]) -> List[dict]:
        """
        FASE 4: Enriquecer detalhes de canais em BATCH.
        Custo: 1 unit para ATÉ 50 canais!
        """
        if not self.config.fetch_channel_details or not channel_ids:
            return []

        unique_ids: list[str] = list(set(channel_ids) - set(self.channel_cache.keys()))
        logger.warning("Custo: 1 unit para 50 canais")
        logger.warning(unique_ids)
        if not unique_ids:
            return list(self.channel_cache.values())
        logger.info(f"Enriquecendo detalhes de {len(unique_ids)} canais...")
        all_channels = []

        for i in range(0, len(unique_ids), self.config.channel_batch_size):
            batch = unique_ids[i : i + self.config.channel_batch_size]

            try:
                channels = self.client.fetch_channels_by_ids(batch)
                all_channels.extend(channels)

                for ch in channels:
                    self.channel_cache[ch["id"]] = ch

                self.stats.add_quota(1, f"channels_batch")
                logger.info(f"  Batch {i // 50 + 1}: {len(channels)} canais")

            except Exception as e:
                logger.error(f"  Erro no batch {i // 50 + 1}: {e}")
                self.stats.errors.append(f"Channel batch {i}: {str(e)}")

        self.stats.channels_collected = len(self.channel_cache)
        return all_channels

    def extract_subtitles(self, video_ids: List[str]) -> List[dict]:
        if not self.config.fetch_subtitles or not video_ids:
            return []

        logger.warning(f"CUSTO: 50 units por vídeo")
        logger.info(f"Extraindo legendas de {len(video_ids)} vídeos...")

        subtitles: list[Subtitle] = self.client.fetch_subtitles_batch(
            video_ids=video_ids, languages=self.config.languages
        )

        self.stats.add_quota(len(video_ids) * 50, "subtitles_batch")
        self.stats.subtitles_collected = len(subtitles)

        return subtitles

    def filter_videos(self, videos: List[dict]) -> List[dict]:
        """
        Aplica filtros de qualidade aos vídeos.
        """
        filtered: list[Any] = []
        for v in videos:
            stats = v.get("statistics", {})
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))

            if views >= self.config.min_views and likes >= self.config.min_likes:
                filtered.append(v)

        logger.info(f"Filtro: {len(videos)} → {len(filtered)} vídeos")
        return filtered

    def run_complete_pipeline(
        self,
        source: str = "popular",
        source_params: Optional[dict] = None,
        checkpoint_name: str = "pipeline",
    ) -> Dict[str, List[dict]]:

        logger.info("Iniciando pipeline otimizada do YouTube")
        logger.info(
            f"Config: max_videos={self.config.max_videos}, "
            f"comments={self.config.fetch_comments}, "
            f"subtitles={self.config.fetch_subtitles}"
        )

        checkpoint = self.load_checkpoint(checkpoint_name)

        results = {"videos": [], "comments": [], "channels": [], "subtitles": []}

        source_params = source_params or {}

        if source == "popular":
            raw_videos = self.extract_videos_popular(**source_params)
        elif source == "category":
            raw_videos = self.extract_videos_by_category(**source_params)
        elif source == "search":
            raw_videos = self.search_videos(**source_params)
        else:
            raise ValueError(f"Fonte inválida: {source}")

        logger.info(f"🔎 {len(raw_videos)} vídeos descobertos")

        # Converter objetos -> ids para enrichment
        raw_video_ids = [v.video_id for v in raw_videos]

        # --------------------------------------------------
        # 2) ENRIQUECIMENTO (retorna dict da API)
        # --------------------------------------------------
        videos = self.enrich_video_details(raw_video_ids)

        # --------------------------------------------------
        # 3) FILTROS
        # --------------------------------------------------
        videos = self.filter_videos(videos)
        results["videos"] = videos

        logger.info(f"📹 {len(videos)} vídeos após enriquecimento e filtros")

        # 🔥 A PARTIR DAQUI USAMOS APENAS VIDEOS ENRIQUECIDOS
        logger.info(videos)
        video_ids = [v["video_id"] for v in videos]

        # --------------------------------------------------
        # 4) EXTRAÇÃO DE COMENTÁRIOS
        # --------------------------------------------------
        all_comments = []

        for idx, video in enumerate(videos, 1):
            video_id = video["video_id"]
            title = video.get("snippet", {}).get("title", "No title")

            logger.info(f"[{idx}/{len(videos)}] Comentários: {title[:50]}")

            if self.config.fetch_comments:
                comments = self.extract_comments(video_id)
                all_comments.extend(comments)

            self.stats.videos_processed += 1

            if idx % self.config.save_checkpoint_every == 0:
                self.save_checkpoint(checkpoint_name, results)

            time.sleep(1 / self.config.rate_limit_rps)

        results["comments"] = all_comments

        # --------------------------------------------------
        # 5) ENRIQUECIMENTO DE CANAIS
        # --------------------------------------------------
        logger.warning(videos)
        channel_ids = list(
            {v["channel_id"] for v in videos if "channel_id" in v and v["channel_id"]}
        )

        logger.info(f"📺 Enriquecendo {len(channel_ids)} canais")

        channels = self.enrich_channel_details(channel_ids)
        results["channels"] = channels

        # --------------------------------------------------
        # 6) LEGENDAS (opcional e caro)
        # --------------------------------------------------
        if self.config.fetch_subtitles:
            logger.info("📝 Extraindo legendas (limitado a 10 vídeos)")
            subtitles = self.extract_subtitles(video_ids[:10])
            results["subtitles"] = subtitles

        # --------------------------------------------------
        # 7) SALVAMENTO FINAL
        # --------------------------------------------------
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.client.save_json(
            results["videos"], self.config.output_dir / f"videos_{timestamp}.json"
        )

        self.client.save_csv(
            results["videos"], self.config.output_dir / f"videos_{timestamp}.csv"
        )

        if results["comments"]:
            self.client.save_json(
                results["comments"],
                self.config.output_dir / f"comments_{timestamp}.json",
            )
        from dataclasses import asdict

        if results["channels"]:
            channels_json: list[dict[str, Any]] = [
                asdict(c) for c in results["channels"]
            ]

            self.client.save_json(
                channels_json, self.config.output_dir / f"channels_{timestamp}.json"
            )

        ##self.save_checkpoint(checkpoint_name, results)

        print(self.stats.report())

        return results


def example_minimal():
    """Exemplo mínimo: só vídeos populares, sem comentários."""
    from api_getter import YouTubeClient, RateLimitConfig

    client = YouTubeClient(rate_limit=RateLimitConfig(requests_per_second=2.0, burst=1))

    config = PipelineConfig(
        max_videos=50,
        fetch_comments=False,
        fetch_subtitles=False,
        fetch_channel_details=True,
        rate_limit_rps=2.0,
    )

    pipeline = YouTubePipeline(client, config)
    results = pipeline.run_complete_pipeline(
        source="popular", source_params={"region": "BR", "max_results": 50}
    )

    print(f"Coletados {len(results['videos'])} vídeos")


def example_category_with_comments():
    """Exemplo médio: categoria específica com comentários."""
    from api_getter import YouTubeClient, RateLimitConfig

    client = YouTubeClient(rate_limit=RateLimitConfig(requests_per_second=2.0, burst=1))

    config = PipelineConfig(
        max_videos=100,
        max_comments_per_video=100,
        fetch_comments=True,
        fetch_subtitles=False,
        min_views=10000,  # Filtrar vídeos com menos de 10k views
        rate_limit_rps=2.0,
    )

    pipeline = YouTubePipeline(client, config)
    results = pipeline.run_complete_pipeline(
        source="category",
        source_params={"category_name": "Música", "region": "BR", "max_results": 100},
        checkpoint_name="musica_pipeline",
    )

    print(f"✅ {len(results['videos'])} vídeos, {len(results['comments'])} comentários")


def example_full_pipeline():
    """Exemplo completo: tudo habilitado (CARO!)."""
    from api_getter import YouTubeClient, RateLimitConfig, LimitsConfig

    client = YouTubeClient(
        rate_limit=RateLimitConfig(requests_per_second=1.0, burst=1),
        limits=LimitsConfig(max_api_calls=1000, max_videos=200, max_comments=5000),
    )

    config = PipelineConfig(
        max_videos=100,
        max_comments_per_video=50,
        fetch_comments=True,
        fetch_subtitles=True,
        fetch_channel_details=True,
        rate_limit_rps=1.0,
        languages=["pt-BR", "pt"],
    )

    pipeline = YouTubePipeline(client, config)
    results = pipeline.run_complete_pipeline(
        source="popular",
        source_params={"region": "BR", "max_results": 50},
        checkpoint_name="full_pipeline",
    )

    print(f"Pipeline completa:")
    print(f"|{len(results['videos'])} vídeos")
    print(f"|{len(results['comments'])} comentários")
    print(f"|{len(results['channels'])} canais")
    print(f"|{len(results['subtitles'])} legendas")


if __name__ == "__main__":
    print(__doc__)
