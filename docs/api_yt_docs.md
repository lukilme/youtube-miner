# API do YouTube — Visão geral (consultas, métricas e limites gratuitos)

## O que é a API

A YouTube Data API v3 permite consultar dados públicos da plataforma YouTube como vídeos, canais, categorias e comentários, além de coletar métricas básicas.

---

## Autenticação

| Tipo          | Finalidade                                    |
| ------------- | --------------------------------------------- |
| API Key       | Para dados públicos                           |
| OAuth 2.0     | Necessário para ações de usuário              |
| YouTube Analytics API | Analytics avançado (API separada)     |

---

## Free Tier (Quota)

A API usa quota points por requisição.

- Limite padrão diário: 10.000 units/dia
- Reset automático a cada 24h (horário do Pacífico)

### Custos comuns por endpoint

| Operação                | Custo (units) |
| ----------------------- | ------------- |
| search.list             | 100           |
| videos.list             | 1             |
| channels.list           | 1             |
| commentThreads.list     | 1             |
| videoCategories.list    | 1             |

O endpoint de busca (search) é o mais caro.

---

## Recursos principais da API

---

### 1. Vídeos (Videos)

**Endpoint:** `videos.list`

**Permite consultar:** Informações completas de vídeos por ID

**Campos importantes (part):**

| Part            | Descrição                         |
| --------------- | --------------------------------- |
| snippet         | título, descrição, thumbnails     |
| statistics      | métricas do vídeo                 |
| contentDetails  | duração, qualidade                |
| topicDetails    | categorias/temas                  |

**Métricas disponíveis:**

| Métrica       | Campo         |
| ------------- | ------------- |
| Visualizações | viewCount     |
| Likes         | likeCount     |
| Comentários   | commentCount  |
| Favoritos     | favoriteCount |

**Exemplo de uso:** Consultar estatísticas de vídeos específicos.

---

### 2. Busca de vídeos (Search)

> [!WARNING]
> Alto custo
> 
> Não recomendado, apenas se soubser o que está fazendo
>

**Endpoint:** `search.list`

**Permite:** Buscar vídeos por palavra-chave. Filtrar por data, canal, tipo (video, channel, playlist), duração, relevância.

**Parâmetros importantes:**

| Parâmetro        | Exemplo                 |
| ---------------- | ----------------------- |
| q                | "machine learning"      |
| type             | video                   |
| order            | date, rating, viewCount |
| publishedAfter   | 2025-01-01              |

Custo alto: 100 quota units

Geralmente usado apenas para obter IDs e depois consultar via `videos.list`.

---

### 3. Canais (Channels)

**Endpoint:** `channels.list`

**Permite consultar:** Dados de um canal por ID ou username

**Campos importantes:**

| Part               | Descrição                     |
| ------------------ | ----------------------------- |
| snippet            | nome, descrição, thumbnails   |
| statistics         | métricas do canal             |
| brandingSettings   | customizações                 |

**Métricas disponíveis:**

| Métrica         | Campo           |
| --------------- | --------------- |
| Inscritos       | subscriberCount |
| Total de views  | viewCount       |
| Total de vídeos | videoCount      |

---

### 4. Categorias de vídeos

**Endpoint:** `videoCategories.list`

**Permite:** Listar categorias **oficiais do YouTube**.

Exemplos: Music, Gaming, Education, Science & Technology

Uso comum: Classificação de conteúdo, filtros de busca por categoria.

---

### 5. Comentários

**Endpoint principal:** `commentThreads.list`

**Permite consultar:** Comentários de vídeos, respostas de comentários

**Campos úteis:**

| Campo                                        | Descrição           |
| -------------------------------------------- | ------------------- |
| snippet.topLevelComment.snippet.textDisplay | texto               |
| authorDisplayName                            | autor               |
| likeCount                                    | likes do comentário |
| publishedAt                                  | data                |

**Endpoint adicional:** `comments.list` (busca respostas específicas)

---

## Estratégia recomendada de uso

Fluxo típico para economizar quota:

| Etapa | Endpoint            | Finalidade                     | Custo (units) |
| ----- | ------------------- | ------------------------------ | ------------- |
| 1     | search.list         | obter IDs de vídeos            | 100           |
| 2     | videos.list         | coletar métricas               | 1             |
| 3     | channels.list       | dados do canal                 | 1             |
| 4     | commentThreads.list | comentários                    | 1             |

---

## Resumo

A API gratuita permite:

- Buscar vídeos e canais
- Coletar métricas públicas
- Obter comentários
- Classificar conteúdo por categoria
- Operar com 10.000 requisições/dia (quota baseada em pontos)