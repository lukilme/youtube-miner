from __future__ import annotations

import streamlit as st 
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import streamlit as st


# ──────────────────────────────────────────────────────────────────────────────
# Helper — lazy-load do cliente concreto
# ──────────────────────────────────────────────────────────────────────────────
def _get_client():
    """
    Instancia (e faz cache via session_state) o cliente concreto da IYouTubeClient.
    Ajuste o import abaixo para o caminho real da sua implementação.
    """
    if "yt_client" not in st.session_state:
        # ← troque pelo import da sua implementação concreta
        from src.core.api.api_getter import YouTubeClient  # noqa: PLC0415
        st.session_state["yt_client"] = YouTubeClient()
    return st.session_state["yt_client"]


# ──────────────────────────────────────────────────────────────────────────────
# Constantes de UI
# ──────────────────────────────────────────────────────────────────────────────
REGION_OPTIONS = {
    "🇧🇷 Brasil": "BR",
    "🇺🇸 Estados Unidos": "US",
    "🇵🇹 Portugal": "PT",
    "🇦🇷 Argentina": "AR",
    "🇲🇽 México": "MX",
}

CATEGORY_OPTIONS = [
    "Todos",
    "jogos",
    "música",
    "tecnologia",
    "esportes",
    "entretenimento",
    "educação",
    "notícias",
    "ciência",
    "viagens",
    "culinária",
]

ORDER_OPTIONS = {"Relevância": "relevance", "Mais recentes": "time"}

FORMAT_OPTIONS = ["csv", "json"]


# ──────────────────────────────────────────────────────────────────────────────
# Seções do painel
# ──────────────────────────────────────────────────────────────────────────────

def _section_popular_videos(client) -> None:
    st.subheader("🔥 Vídeos Mais Populares")

    col1, col2, col3 = st.columns(3)
    with col1:
        region_label = st.selectbox("Região", list(REGION_OPTIONS.keys()), key="pop_region")
        region_code = REGION_OPTIONS[region_label]
    with col2:
        max_items = st.number_input("Máx. de vídeos", min_value=1, max_value=200, value=10, key="pop_max")
    with col3:
        category = st.selectbox("Categoria", CATEGORY_OPTIONS, key="pop_cat")

    if st.button("🔍 Buscar vídeos populares", use_container_width=True):
        with st.spinner("Buscando vídeos..."):
            try:
                if category == "Todos":
                    videos = client.fetch_most_popular(
                        region_code=region_code,
                        max_items=int(max_items),
                    )
                else:
                    videos = client.fetch_videos_by_category(
                        category=category,
                        region_code=region_code,
                        max_items=int(max_items),
                    )

                if not videos:
                    st.info("Nenhum vídeo encontrado.")
                    return

                rows = [
                    {
                        "ID": v.video_id,
                        "Título": v.title,
                        "Canal": v.channel_title,
                        "Views": f"{v.view_count:,}" if v.view_count else "—",
                        "Likes": f"{v.like_count:,}" if v.like_count else "—",
                        "Duração": v.duration or "—",
                        "Publicado em": str(v.published_at)[:10] if v.published_at else "—",
                    }
                    for v in videos
                ]

                st.success(f"{len(rows)} vídeos encontrados")
                st.dataframe(rows, use_container_width=True)
                st.session_state["last_videos"] = videos

            except Exception as exc:
                st.error(f"Erro ao buscar vídeos: {exc}")


def _section_comments(client) -> None:
    st.subheader("💬 Comentários de Vídeo")

    col1, col2, col3 = st.columns(3)
    with col1:
        video_id = st.text_input("ID do vídeo", placeholder="Ex.: dQw4w9WgXcQ", key="cmt_vid")
    with col2:
        order_label = st.selectbox("Ordenar por", list(ORDER_OPTIONS.keys()), key="cmt_order")
        order = ORDER_OPTIONS[order_label]
    with col3:
        max_comments = st.number_input("Máx. de comentários", min_value=1, max_value=500, value=20, key="cmt_max")

    if st.button("💬 Buscar comentários", use_container_width=True):
        if not video_id.strip():
            st.warning("Informe o ID do vídeo.")
            return
        with st.spinner("Buscando comentários..."):
            try:
                comments = client.fetch_comments(
                    video_id=video_id.strip(),
                    order=order,
                    max_items=int(max_comments),
                )
                if not comments:
                    st.info("Nenhum comentário encontrado.")
                    return

                rows = [
                    {
                        "Autor": c.author_display_name,
                        "Comentário": c.text_display,
                        "Likes": c.like_count or 0,
                        "Publicado em": str(c.published_at)[:10] if c.published_at else "—",
                    }
                    for c in comments
                ]
                st.success(f"{len(rows)} comentários encontrados")
                st.dataframe(rows, use_container_width=True)

            except Exception as exc:
                st.error(f"Erro ao buscar comentários: {exc}")


def _section_channels(client) -> None:
    st.subheader("📺 Busca de Canais")

    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("Termo de busca", placeholder="Ex.: Python Brasil", key="ch_query")
    with col2:
        max_channels = st.number_input("Máx.", min_value=1, max_value=50, value=5, key="ch_max")

    col3, col4 = st.columns(2)
    with col3:
        region_label = st.selectbox("Região (opcional)", ["—"] + list(REGION_OPTIONS.keys()), key="ch_region")
        region_code = None if region_label == "—" else REGION_OPTIONS[region_label]
    with col4:
        username = st.text_input("Ou buscar por @handle", placeholder="@LinusTechTips", key="ch_handle")

    if st.button("📺 Buscar canais", use_container_width=True):
        with st.spinner("Buscando canais..."):
            try:
                if username.strip():
                    result = client.fetch_channel_by_username(username.strip())
                    channels = [result] if result else []
                elif query.strip():
                    channels = client.search_channels(
                        query=query.strip(),
                        max_items=int(max_channels),
                        region_code=region_code,
                    )
                else:
                    st.warning("Informe um termo de busca ou @handle.")
                    return

                if not channels:
                    st.info("Nenhum canal encontrado.")
                    return

                rows = [
                    {
                        "ID": ch.channel_id,
                        "Nome": ch.title,
                        "Inscritos": f"{ch.subscriber_count:,}" if ch.subscriber_count else "—",
                        "Vídeos": ch.video_count or "—",
                        "Views totais": f"{ch.view_count:,}" if ch.view_count else "—",
                        "País": ch.country or "—",
                    }
                    for ch in channels
                ]
                st.success(f"{len(rows)} canal(is) encontrado(s)")
                st.dataframe(rows, use_container_width=True)

            except Exception as exc:
                st.error(f"Erro ao buscar canais: {exc}")


def _section_subtitles(client) -> None:
    st.subheader("📝 Legendas")

    col1, col2, col3 = st.columns(3)
    with col1:
        video_id = st.text_input("ID do vídeo", placeholder="Ex.: dQw4w9WgXcQ", key="sub_vid")
    with col2:
        lang_input = st.text_input(
            "Idiomas preferidos (separados por vírgula)",
            value="pt,pt-BR,en",
            key="sub_lang",
        )
    with col3:
        include_generated = st.checkbox("Incluir legendas automáticas", value=True, key="sub_gen")

    if st.button("📝 Buscar legenda", use_container_width=True):
        if not video_id.strip():
            st.warning("Informe o ID do vídeo.")
            return
        with st.spinner("Buscando legenda..."):
            try:
                languages = [l.strip() for l in lang_input.split(",") if l.strip()]
                subtitle = client.fetch_subtitles(
                    video_id=video_id.strip(),
                    languages=languages or None,
                    include_generated=include_generated,
                )
                if not subtitle:
                    st.info("Legenda não encontrada para este vídeo.")
                    return

                st.success(f"Legenda encontrada — idioma: `{subtitle.language}`")
                with st.expander("📄 Visualizar texto completo", expanded=False):
                    st.text_area("Conteúdo da legenda", subtitle.content or "", height=300, key="sub_content")

            except Exception as exc:
                st.error(f"Erro ao buscar legenda: {exc}")


def _section_video_details(client) -> None:
    st.subheader("🎬 Detalhes de Vídeo")

    col1, col2 = st.columns([2, 2])
    with col1:
        video_id = st.text_input("ID do vídeo", placeholder="Ex.: dQw4w9WgXcQ", key="det_vid")
    with col2:
        parts_input = st.text_input(
            "Parts (separadas por vírgula)",
            value="snippet,statistics,contentDetails",
            key="det_parts",
        )

    if st.button("🎬 Buscar detalhes", use_container_width=True):
        if not video_id.strip():
            st.warning("Informe o ID do vídeo.")
            return
        with st.spinner("Buscando detalhes..."):
            try:
                parts = [p.strip() for p in parts_input.split(",") if p.strip()]
                details = client.fetch_video_details(
                    video_id=video_id.strip(),
                    parts=parts or None,
                )
                if not details:
                    st.info("Vídeo não encontrado.")
                    return
                st.json(details)

            except Exception as exc:
                st.error(f"Erro ao buscar detalhes: {exc}")


def _section_pipeline(client) -> None:
    st.subheader("⚙️ Pipeline Completo")
    st.caption("Executa o fluxo completo: vídeos → comentários → (canais) → arquivos.")

    col1, col2, col3 = st.columns(3)
    with col1:
        total_videos = st.number_input("Total de vídeos", min_value=1, max_value=200, value=10, key="pipe_total")
        region_label = st.selectbox("Região", list(REGION_OPTIONS.keys()), key="pipe_region")
        region_code = REGION_OPTIONS[region_label]
    with col2:
        comments_pages = st.number_input("Páginas de comentários", min_value=1, max_value=10, value=1, key="pipe_cpages")
        category_id = st.text_input("ID de categoria (opcional)", value="21", key="pipe_cat")
    with col3:
        include_channels = st.checkbox("Incluir detalhes de canais", value=False, key="pipe_ch")
        output_dir = st.text_input("Diretório de saída", value="output", key="pipe_dir")
        fmt = st.selectbox("Formato de saída", FORMAT_OPTIONS, key="pipe_fmt")

    if st.button("🚀 Executar pipeline", use_container_width=True, type="primary"):
        with st.spinner("Executando pipeline… isso pode levar alguns minutos."):
            try:
                client.run_pipeline(
                    total_videos=int(total_videos),
                    region=region_code,
                    comments_pages=int(comments_pages),
                    video_category_id=category_id.strip() or None,
                    include_channels=include_channels,
                    output_dir=output_dir.strip(),
                    fmt=fmt,
                )
                st.success(f"Pipeline concluído! Arquivos salvos em `{output_dir}/`.")
            except Exception as exc:
                st.error(f"Erro no pipeline: {exc}")


# ──────────────────────────────────────────────────────────────────────────────
# Entry-point
# ──────────────────────────────────────────────────────────────────────────────

def render(st) -> None:
    st.title("📡 YouTube Explorer")
    st.caption(
        "Consulte a YouTube Data API v3 diretamente: vídeos populares, "
        "comentários, canais, legendas e muito mais."
    )

    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("🔧 Configurações")
        st.info(
            "Certifique-se de que a variável de ambiente `YOUTUBE_API_KEY` "
            "está definida antes de usar este painel.",
            icon="ℹ️",
        )
        st.divider()
        section = st.radio(
            "Seção",
            options=[
                "🔥 Vídeos Populares",
                "💬 Comentários",
                "📺 Canais",
                "📝 Legendas",
                "🎬 Detalhes do Vídeo",
                "⚙️ Pipeline",
            ],
            key="nav_section",
        )
        st.divider()
        st.caption("Interface gerada para `IYouTubeClient`")

    # ── Carrega cliente ───────────────────────────────────────────────────────
    try:
        client = _get_client()
    except Exception as exc:
        st.error(
            f"Não foi possível instanciar o cliente YouTube: {exc}\n\n"
            "Verifique se `YOUTUBE_API_KEY` está definido e se o caminho "
            "de importação em `_get_client()` está correto."
        )
        return

    # ── Roteamento ────────────────────────────────────────────────────────────
    st.divider()

    if section == "🔥 Vídeos Populares":
        _section_popular_videos(client)
    elif section == "💬 Comentários":
        _section_comments(client)
    elif section == "📺 Canais":
        _section_channels(client)
    elif section == "📝 Legendas":
        _section_subtitles(client)
    elif section == "🎬 Detalhes do Vídeo":
        _section_video_details(client)
    elif section == "⚙️ Pipeline":
        _section_pipeline(client)