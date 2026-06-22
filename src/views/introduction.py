from pathlib import Path

ASSETS_DIR = Path("static")


def render(st):
    st.markdown(
        """
        <h1 style='text-align: center; color: #3b82f6;'>
            Introducao
        </h1>
        <p style='text-align: center; font-size: 1.2rem; color: #9ca3af;'>
            Projeto de Mineracao de Dados e PNL - YouTube Miner
        </p>
        <hr>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("""
        O YouTube é um dos maiores ecossistemas de conteúdo audiovisual e interação social do mundo.
        A cada dia, milhões de vídeos, comentários e reações são produzidos de forma orgânica,
        formando uma base rica para investigar comportamento coletivo, engajamento e circulação de temas.
        """)

    st.divider()

    st.subheader("Escala do Ecossistema")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Vídeos", "5B - 14,8B")
    with c2:
        st.metric("Canais ativos", "115M")
    with c3:
        st.metric("Conteúdos mensais", "60M")

    st.caption(
        "Estimativas usadas como contexto para dimensionar a relevância da plataforma."
    )

    st.divider()

    st.subheader("Base acadêmica e lacuna")

    left, right = st.columns(2)

    with left:
        st.info("""
            **Chatzopoulou et al. (2010)**  
            Cerca de 37 milhões de registros mostraram correlação forte entre visualizações,
            comentários, curtidas e favoritos, sugerindo padrões estruturais de engajamento.
            """)

        st.info("""
            **Hoiles et al. (2016)**  
            Visualizações no primeiro dia, inscritos e sinais de otimização pós-publicação
            apareceram como fatores relevantes para popularidade.
            """)

    with right:
        st.info("""
            **Yang et al. (2022)**  
            Vídeos mais curtos e sinais sociais, como curtidas, se associaram positivamente
            ao engajamento em um canal de divulgação científica.
            """)

        st.info("""
            **Giankos et al. (2025)**  
            Palavras-chave nos títulos influenciaram a visibilidade, enquanto a duração
            não teve efeito relevante em canais de pesca.
            """)

    st.warning("""
        Apesar desses avanços, a maior parte dos estudos ainda privilegia métricas estruturais
        e metadados. As camadas semânticas presentes em títulos, descrições e comentários
        seguem pouco exploradas.
        """)

    st.divider()

    st.subheader("Visuais centrais da proposta")

    img_col1, img_col2 = st.columns(2)

    with img_col1:
        st.markdown("**Diagrama da dinâmica entre canais, vídeos e comentários**")
        diagrama_path = ASSETS_DIR / "diagrama.png"
        if diagrama_path.exists():
            st.image(str(diagrama_path), use_container_width=True)
        else:
            st.error("Imagem não encontrada: assets/diagrama.png")

        st.caption("Mostra a relação circular entre canal, vídeo e comentários.")

    with img_col2:
        st.markdown("**Thumbs e nuvens de palavras baseadas nos comentários**")
        cloud_path = ASSETS_DIR / "cloud_words.png"
        if cloud_path.exists():
            st.image(str(cloud_path), use_container_width=True)
        else:
            st.error("Imagem não encontrada: assets/cloud_words.png")

        st.caption(
            "Evidencia como temas distintos aparecem na reação textual da audiência."
        )

    st.divider()

    st.subheader("Por que realizar esta pesquisa?")

    st.success("""
        A proposta integra três camadas pouco usuais em conjunto: **texto**, **rede** e
        **sentimento**. Essa combinação permite identificar padrões que a categorização
        manual do YouTube não enxerga, especialmente no contexto brasileiro.
        """)

    st.markdown("""
        Ao unir a **Tríade** com o **Ciclo**, a pesquisa propõe o conceito de **Categorias Emergentes**:
        uma categoria oculta não é definida pelo título do vídeo, mas sim pelo comportamento coletivo da audiência.
        """)

    st.markdown("""
        > "Uma categoria oculta não é definida pelo título do vídeo, mas sim pelo comportamento coletivo da audiência."
        """)

    with st.expander("Exemplo para defesa"):
        st.markdown("""
            Um vídeo está classificado oficialmente como **Educação**.

            A análise integrada revela que:
            - o texto dos comentários concentra 80% de palavras ligadas a **emoção** e **polêmica**;
            - a rede mostra respostas concentradas em dois usuários que trocam farpas;
            - o sentimento é majoritariamente **negativo**, com traços de raiva e ansiedade.

            A conclusão é que o vídeo não opera apenas como um conteúdo educacional.
            Ele se comporta como uma categoria oculta, por exemplo, **Disputa Ideológica**.

            Isso só é possível porque a leitura conjunta de canal, vídeo e comentários expõe
            a dependência entre origem do conteúdo, gatilho temático e reação da audiência.
            """)

    st.divider()

    st.subheader("Lógica circular do sistema")

    step1, step2, step3 = st.columns(3)

    with step1:
        st.markdown("### 1. Canal → Vídeo → Público")
        st.markdown("""
            Um canal de ciência tende a produzir vídeos com linguagem mais formal.
            Um canal de games tende a usar gírias, humor e intensidade emocional.

            Isso altera diretamente o perfil dos comentários.
            """)

    with step2:
        st.markdown("### 2. Vídeo → Comentário")
        st.markdown("""
            O assunto do vídeo atua como gatilho para a reação textual.

            Quando comentários se afastam do tema central, isso pode indicar
            que o vídeo passou a funcionar como espaço para outro tipo de disputa.
            """)

    with step3:
        st.markdown("### 3. Comentário → Canal → Vídeo")
        st.markdown("""
            A audiência retroalimenta o criador.

            Comentários frequentes, polarizados ou muito centralizados em certos usuários
            podem influenciar o próximo vídeo e também o alcance algorítmico.
            """)

    with st.expander("Leitura analítica da circularidade"):
        st.markdown("""
            - **Canal determina o vídeo e o público**: o canal carrega estilo, identidade e viés.
            - **Vídeo pauta o comentário**: o conteúdo ativa respostas que raramente são neutras.
            - **Comentário realimenta o canal**: a reação da audiência afeta decisões futuras e o engajamento.

            Essa estrutura transforma o YouTube em um **sistema vivo**, e não em uma coleção estática
            de textos isolados.
            """)

    st.divider()

    st.subheader("Vantagens da abordagem")

    v1, v2 = st.columns(2)

    with v1:
        st.markdown("""
            #### Descoberta de categorias ocultas
            O clustering não supervisionado revela agrupamentos temáticos e sociais
            que não aparecem nas categorias oficiais da plataforma.
            """)

        st.markdown("""
            #### Representação textual rica
            A abordagem combina:
            - Sentence-BERT multilíngue
            - TF-IDF com n-gramas
            - metadados estruturados
            """)

    with v2:
        st.markdown("""
            #### Prevenção de data leakage
            Variáveis que vazariam o alvo são removidas explicitamente,
            como views, likes e comentários.
            """)

        st.markdown("""
            #### Modularidade e reuso
            As transformações são separadas em etapas de fit e transform,
            permitindo reaplicação consistente em novos dados.
            """)

    st.divider()

    st.subheader("Principais riscos e limitações")

    with st.expander("Desafios metodológicos"):
        st.markdown("""
            - Limitação de cota da API do YouTube
            - Ruído em transcrições automáticas (ASR)
            - Linguagem informal e gírias brasileiras
            - Possível desalinhamento entre categoria oficial e comportamento real
            - Necessidade de validação humana dos clusters
            """)

        st.markdown("""
            **Estratégias adotadas**
            - Foco em nichos específicos de canais
            - Pré-processamento intenso
            - Dicionários de gírias brasileiras
            - Avaliação quantitativa e qualitativa
            """)

    st.divider()

    st.subheader("Resumo da proposta")

    st.info("""
        Nossa inovação é tratar o YouTube como um ecossistema. O canal é o DNA,
        o vídeo é o comportamento e o comentário é a reação do ambiente.
        Nenhum desses elementos faz sentido isoladamente.

        Ao sobrepor **Texto**, **Rede** e **Sentimento**, a pesquisa não apenas descreve dados:
        ela interpreta a dinâmica coletiva da comunidade e identifica nichos que o algoritmo,
        até hoje, tende a não enxergar.
        """)
