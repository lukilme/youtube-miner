# 📋 Fase 1 - Baseline: Roteiro Detalhado
## Projeto: Análise de Padrões Latentes no YouTube

**Duração estimada:** 2-3 semanas  
**Objetivo:** Estabelecer pipeline básico de coleta, limpeza, análise exploratória e modelos baseline para validar viabilidade do projeto.

---

## 🎯 Objetivos da Fase 1

1. **Coletar dados estruturados** da API do YouTube de forma eficiente e sustentável
2. **Limpar e preparar** os dados para análise
3. **Realizar EDA** (Exploratory Data Analysis) para entender distribuições e correlações
4. **Criar modelos baseline** simples usando apenas features numéricas
5. **Documentar** achados e decisões técnicas
6. **Estabelecer métricas** de avaliação para fases futuras

---

## 📦 Pré-requisitos

### Ambiente Técnico
- [X] Python 3.9+ instalado
- [X] Ambiente virtual configurado (venv ou conda)
- [X] Git configurado para versionamento
- [X] Jupyter Lab/Notebook para análise interativa

### Credenciais e Acesso
- [ ] API Key do YouTube Data API v3 obtida (Google Cloud Console)
- [ ] Quota diária verificada (10.000 créditos confirmados)
- [ ] Documentação da API estudada ([YouTube Data API](https://developers.google.com/youtube/v3/docs))

### Bibliotecas Essenciais
```bash
pip install google-api-python-client pandas numpy scikit-learn 
pip install matplotlib seaborn plotly jupyterlab
pip install python-dotenv tqdm joblib
```

---

## 🗂️ Estrutura do Projeto

```
youtube-analysis/
│
├── data/
│   ├── raw/              # Dados brutos da API
│   ├── processed/        # Dados limpos
│   └── interim/          # Dados intermediários
│
├── notebooks/
│   ├── 01_coleta.ipynb
│   ├── 02_limpeza.ipynb
│   ├── 03_eda.ipynb
│   └── 04_baseline_models.ipynb
│
├── src/
│   ├── __init__.py
│   ├── data_collection.py
│   ├── data_cleaning.py
│   ├── feature_engineering.py
│   └── utils.py
│
├── config/
│   └── config.yaml
│
├── .env                  # API keys (NÃO versionar!)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 📅 Cronograma Detalhado

### **Semana 1: Coleta e Limpeza**

#### Dia 1-2: Setup e Primeira Coleta
**Tempo estimado:** 6-8 horas

- [ ] **1.1 Configurar ambiente**
  - [ ] Criar repositório Git
  - [ ] Configurar `.gitignore` (incluir `.env`, `data/raw/`, notebooks checkpoints)
  - [ ] Criar estrutura de pastas
  - [ ] Configurar `.env` com API_KEY

- [ ] **1.2 Implementar coleta básica**
  ```python
  # src/data_collection.py - Estrutura conceitual
  
  class YouTubeCollector:
      def __init__(self, api_key):
          """Inicializar cliente da API"""
          
      def search_videos(self, query, max_results=50):
          """Buscar vídeos por query"""
          
      def get_video_details(self, video_ids):
          """Obter metadados detalhados (views, likes, etc.)"""
          
      def get_video_comments(self, video_id, max_comments=100):
          """Obter comentários do vídeo"""
          
      def get_channel_info(self, channel_id):
          """Obter info do canal"""
          
      def calculate_quota_cost(self, operation):
          """Rastrear uso de quota"""
  ```

- [ ] **1.3 Definir estratégia de amostragem inicial**
  - [ ] Decidir categorias/tópicos para coletar (ex: 5-10 categorias diferentes)
  - [ ] Definir período temporal (ex: últimos 30 dias)
  - [ ] Definir critérios de inclusão (idioma, duração mínima, etc.)
  - [ ] **Meta:** ~1.000-5.000 vídeos para baseline

- [ ] **1.4 Executar primeira coleta**
  - [ ] Coletar metadados de vídeos
  - [ ] Coletar informações de canais
  - [ ] Salvar dados brutos em JSON/CSV
  - [ ] Registrar quota consumida

**Entrega Dia 1-2:**
- ✅ Script de coleta funcional
- ✅ Dataset inicial em `data/raw/`
- ✅ Log de quota usage

---

#### Dia 3-4: Limpeza e Preparação de Dados
**Tempo estimado:** 6-8 horas

- [ ] **2.1 Análise de qualidade dos dados**
  - [ ] Verificar valores ausentes por coluna
  - [ ] Identificar duplicatas (mesmo video_id)
  - [ ] Analisar tipos de dados
  - [ ] Documentar anomalias encontradas

- [ ] **2.2 Implementar pipeline de limpeza**
  ```python
  # src/data_cleaning.py - Estrutura conceitual
  
  def remove_duplicates(df):
      """Remover vídeos duplicados"""
      
  def handle_missing_values(df):
      """Estratégia para NaN:
      - view_count, like_count: preencher com 0 ou mediana?
      - published_at: remover se ausente
      - description: preencher com string vazia
      """
      
  def normalize_dates(df):
      """Converter strings de data para datetime"""
      
  def validate_numeric_ranges(df):
      """Verificar valores negativos, outliers extremos"""
      
  def create_derived_features(df):
      """Criar features básicas:
      - engagement_rate = (likes + comments) / views
      - like_ratio = likes / views
      - comment_ratio = comments / views
      - days_since_publish
      """
  ```

- [ ] **2.3 Executar limpeza**
  - [ ] Aplicar funções de limpeza
  - [ ] Salvar dados limpos em `data/processed/`
  - [ ] Criar relatório de limpeza (quantos removidos, imputados, etc.)

- [ ] **2.4 Criar dataset consolidado**
  - [ ] Unir dados de vídeos + canais
  - [ ] Salvar em formato Parquet (mais eficiente)
  - [ ] Criar dicionário de dados (data dictionary)

**Entrega Dia 3-4:**
- ✅ Dataset limpo em `data/processed/videos_clean.parquet`
- ✅ Relatório de limpeza (markdown ou notebook)
- ✅ Dicionário de dados documentado

---

### **Semana 2: Análise Exploratória de Dados (EDA)**

#### Dia 5-7: EDA Aprofundada
**Tempo estimado:** 10-12 horas

- [ ] **3.1 Estatísticas descritivas**
  - [ ] Calcular média, mediana, desvio padrão para todas features numéricas
  - [ ] Criar tabela de percentis (25%, 50%, 75%, 90%, 95%, 99%)
  - [ ] Identificar outliers usando IQR ou Z-score

- [ ] **3.2 Análise univariada**
  - [ ] **Views:**
    - [ ] Histograma de distribuição
    - [ ] Log-transform para melhor visualização
    - [ ] Identificar vídeos com 0 views
  - [ ] **Likes e Comments:**
    - [ ] Distribuição
    - [ ] Relação com views
  - [ ] **Subscriber count:**
    - [ ] Distribuição de tamanho de canais
    - [ ] Categorizar (micro, médio, grande, mega)
  - [ ] **Duração do vídeo:**
    - [ ] Distribuição
    - [ ] Categorizar (curto <5min, médio 5-15min, longo >15min)

- [ ] **3.3 Análise bivariada**
  - [ ] **Matriz de correlação** (Pearson e Spearman)
  - [ ] Scatter plots chave:
    - [ ] Views vs Likes
    - [ ] Views vs Comments
    - [ ] Subscriber count vs Views
    - [ ] Duration vs Engagement
  - [ ] **Categorias vs Engagement:**
    - [ ] Boxplots de views por categoria
    - [ ] Engagement rate por categoria

- [ ] **3.4 Análise temporal**
  - [ ] Views ao longo do tempo (série temporal)
  - [ ] Dia da semana de publicação vs Engagement
  - [ ] Hora do dia de publicação vs Engagement

- [ ] **3.5 Visualizações avançadas**
  - [ ] Pair plot das principais features
  - [ ] Heatmap de correlação
  - [ ] Distribuições com violinplot/ridgeline
  - [ ] **Dashboard interativo** (Plotly Dash - opcional)

**Entrega Dia 5-7:**
- ✅ Notebook `03_eda.ipynb` completo e documentado
- ✅ Conjunto de visualizações salvas em `reports/figures/`
- ✅ Documento de insights principais (markdown)

---

### **Semana 3: Modelagem Baseline**

#### Dia 8-10: Clustering Básico
**Tempo estimado:** 8-10 horas

- [ ] **4.1 Preparação para clustering**
  - [ ] Selecionar features para clustering:
    ```python
    # Exemplo de features
    features = [
        'view_count',
        'like_count', 
        'comment_count',
        'subscriber_count',
        'video_count',  # do canal
        'engagement_rate',
        'like_ratio',
        'duration_seconds'
    ]
    ```
  - [ ] Normalizar/padronizar features (StandardScaler ou MinMaxScaler)
  - [ ] Tratar outliers (clip, remove, ou transformar)

- [ ] **4.2 Determinar número ideal de clusters**
  - [ ] **Método Elbow:**
    - [ ] Executar K-means para