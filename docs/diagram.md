```mermaid
classDiagram

class Channel {
    +str channel_id
    +Optional~str~ title
    +Optional~str~ description
    +Optional~str~ custom_url
    +Optional~str~ published_at
    +Optional~str~ country
    +Optional~str~ thumbnail
    +Optional~int~ view_count
    +Optional~int~ subscriber_count
    +Optional~int~ video_count
    +bool hidden_subscriber_count
}

class Video {
    +str video_id
    +Optional~str~ title
    +Optional~str~ channel_title
    +Optional~str~ channel_id
    +Optional~str~ published_at
    +Optional~str~ category_id
    +Optional~str~ thumbnail
    +Optional~int~ view_count
    +Optional~int~ like_count
    +Optional~int~ comment_count
}

class Comment {
    +str video_id
    +Optional~str~ comment_thread_id
    +Optional~str~ comment_id
    +Optional~str~ author
    +Optional~str~ text
    +int like_count
    +Optional~str~ published_at
    +Optional~str~ updated_at
    +int total_reply_count
    +Optional~str~ video_title
    +Optional~str~ channel_title
    +Optional~int~ video_view_count
    +Optional~int~ video_like_count
    +Optional~int~ video_comment_count
}

class Subtitle {
    +str video_id
    +str language
    +str language_name
    +bool is_generated
    +List~SubtitleSegment~ segments
    +str full_text
}

class SubtitleSegment {
    +str text
    +float start
    +float duration
}

Channel "1" --> "0..*" Video : publica
Video "1" --> "0..*" Comment : possui
Video "1" --> "0..*" Subtitle : possui
Subtitle "1" --> "1..*" SubtitleSegment : contém
```

```
Channel
 └── Video
      ├── Comment
      └── Subtitle
            └── SubtitleSegment
```

```mermaid
flowchart LR
    A[Coleta Inicial] --> B[Seleção de Canais e Vídeos]
    
    B --> C[Enriquecimento de Metadados]
    
    C --> D[Coleta de Comentários]
    
    C --> E[Extração de Métricas]
    
    D --> F[Normalização dos Dados]
    E --> F
    
    F --> G[Controle de Qualidade e Limites]
    
    G --> H[Persistência dos Dados]
    
    H --> I[Arquivos Estruturados para Análise]
```

```
Canal do YouTube
      ↓
Metadados do Vídeo
      ↓
 ┌───────────────┬────────────────┐
 ↓               ↓                ↓
Comentários   Legendas      Métricas
```

```
Coleta Inicial
    └── Seleção de canais e vídeos
            └── Enriquecimento de metadados
                    ├── Comentários
                    ├── Métricas
                    └── Normalização
                            └── Persistência
                                    └── Dados para análise
```

