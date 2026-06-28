import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from sklearn.pipeline import Pipeline
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import dendrogram, linkage
from sklearn.manifold import TSNE
import warnings
warnings.filterwarnings('ignore')
import nltk
import re
import pandas as pd
import numpy as np
import unicodedata
import matplotlib.pyplot as plt
from pathlib import Path
import sys

ROOT: Path = Path.cwd().parent
sys.path.append(str(ROOT))

import src.plots.statistic as static
import nltk
import spacy

nltk.download("stopwords")
from nltk.corpus import stopwords
def get_stopwords():
    nltk_words = set(stopwords.words("portuguese"))
    nlp = spacy.load("pt_core_news_sm")
    spacy_words = nlp.Defaults.stop_words
    return nltk_words.union(spacy_words)


def remove_accents(word):
    return "".join(
        c for c in unicodedata.normalize("NFD", word) if unicodedata.category(c) != "Mn"
    )
STOPWORDS_PT = {remove_accents(w).lower() for w in get_stopwords()}

stopwords_adicionais = {
    # Verbos muito frequentes em títulos (formas conjugadas)
    "vai", "vão", "chegou", "compra", "comprar", "mudar", "criando",
    "precisa", "saber", "fez", "usa", "ficou", "perder", "bater",
    "papo", "fazer", "tá", "tem", "ter", "ser", "está", "estão",
    "era", "foi", "fica", "veio", "trouxe", "vem", "faz", "falamos",
    
    # Pronomes/artigos que podem faltar na lista padrão
    "isso", "esse", "essa", "esses", "essas", "aquilo", "aquela",
    "aquele", "tudo", "todo", "toda", "todos", "todas",
    
    # Advérbios e conectivos genéricos
    "aí", "lá", "cá", "já", "só", "mais", "muito", "pouco",
    "bem", "mal", "agora", "hoje", "ontem", "amanhã", "sempre",
    "nunca", "talvez", "ainda", "também", "assim", "depois",
    
    # Palavras de títulos clickbait muito comuns (opcional – remova se quiser preservar o estilo)
    "você", "seu", "sua", "seus", "suas",  # já podem estar na lista, mas garanta
}

stopwords_adicionais.update({
    "leonardo", "muller", "locução", "narração"
})

STOPWORDS_PT.update(stopwords_adicionais)
class YoutubeVideoClusterAnalyzer:
    """
    Análise de clustering para detectar categorias ocultas em vídeos YouTube
    """
    
    def __init__(self, filepath):
        self.df = pd.read_csv(filepath)
        self.df_processed = None
        self.scaler = StandardScaler()
        self.pca = None
        self.clusters = None
        self.features_for_clustering = None
        
    def load_and_explore(self):
        """Carrega e explora o dataset"""
        print("📊 Dataset Shape:", self.df.shape)
        print("\n📝 Primeiras linhas:")
        print(self.df.head())
        print("\n❌ Missing Values:")
        print(self.df.isnull().sum())
        return self
    
    def prepare_data(self):
        """Preparação e limpeza dos dados"""
        print("\n🔧 Preparando dados...")
        self.df_processed = self.df.copy()
        self.df_processed['description_processed'] = self.df_processed['description_processed'].fillna('')
        # Preencher valores faltantes
        numeric_cols = self.df_processed.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            print(col)
            self.df_processed[col].fillna(self.df_processed[col].median(), inplace=True)
        
        # Preencher strings faltantes
        string_cols = ['title_processed', 'description_processed',  'description_canal']
        for col in string_cols:
            if col in self.df_processed.columns:
                print(col)
                self.df_processed[col].fillna('', inplace=True)
        
        # Remover duplicatas
        initial_rows = len(self.df_processed)
        self.df_processed = self.df_processed.drop_duplicates(subset=['video_id'])
        print(f"✅ Removidas {initial_rows - len(self.df_processed)} duplicatas")
        
        return self
    
    def create_advanced_features(self):
        """Cria features avançadas para melhor clustering"""
        print("\n🎯 Criando features avançadas...")
        
        # 1. Features de Engajamento Avançadas
        self.df_processed['engagement_score'] = (
            self.df_processed['engagement_rate'] * 
            self.df_processed['views_per_day']
        )
        
        # Virality Index (crescimento de engajamento)
        self.df_processed['virality_index'] = (
            (self.df_processed['like_rate'] + self.df_processed['comment_rate']) / 
            (self.df_processed['dias_publicacao'] + 1)
        )
        
        # Qualidade de conteúdo estimada
        self.df_processed['content_quality'] = (
            self.df_processed['like_comment_ratio'] * 
            self.df_processed['view_subscriber_ratio']
        )
        
        # 2. Features Temporais
        self.df_processed['tempo_na_plataforma_ratio'] = (
            self.df_processed['age_days'] / 
            (self.df_processed['channel_age_days'] + 1)
        )
        
        # Frescor do conteúdo (quanto mais recente, maior)
        self.df_processed['freshness_score'] = np.exp(
            -self.df_processed['dias_publicacao'] / 30
        )
        
        # 3. Features de Consistência do Canal
        self.df_processed['channel_consistency'] = (
            self.df_processed['video_count'] / 
            (self.df_processed['channel_age_days'] + 1)
        )
        
        self.df_processed['channel_growth_potential'] = (
            self.df_processed['avg_views_per_video'] / 
            (self.df_processed['subscriber_count'] + 1)
        )
        texts = self.df_processed['title_processed'].fillna('').astype(str)
        stopwords_pt = list(STOPWORDS_PT)
        tfidf = TfidfVectorizer(
            max_features=30,
            stop_words=stopwords_pt,
            min_df=2,
            max_df=0.8
        )
        title_features = tfidf.fit_transform(texts).toarray()

        # 4. Features de Descritivo
        if 'title_processed' in self.df_processed.columns:
            self.df_processed['title_diversity'] = (
                self.df_processed['title_word_count'] / 
                (self.df_processed['title_length'] + 1)
            )
        
        self.df_processed['description_richness'] = (
            self.df_processed['description_word_count'] / 
            (self.df_processed['duration_segundos'] + 1)
        )
        
        # 5. Features de Estratégia de Monetização
        self.df_processed['monetization_potential'] = (
            self.df_processed['view_count'] * 
            self.df_processed['engagement_rate']
        )
        
        print("✅ 10 novas features criadas")
        return self
    
    def extract_text_features(self, n_features=200):
        print("\nExtraindo features de texto...")

        # Garantir que as colunas existem
        if 'title_processed' not in self.df_processed.columns:
            print("Coluna 'title_processed' não encontrada.")
            return
        if 'description_processed' not in self.df_processed.columns:
            print("Coluna 'description_processed' não encontrada. Usando apenas título.")
            self.df_processed['description_processed'] = ''

        # Preencher NaN e garantir strings
        titles = self.df_processed['title_processed'].fillna('').astype(str).str.strip()
        descriptions = self.df_processed['description_processed'].fillna('').astype(str).str.strip()

        # Concatenar (pode usar um separador como ' ')
        texts = titles + ' ' + descriptions

        # Remover linhas com texto completamente vazio
        valid_mask = texts != ''

        print(f"Total de documentos: {len(texts)}")
        print(f"Documentos válidos: {valid_mask.sum()}")
        print(f"Documentos vazios: {(~valid_mask).sum()}")

        if valid_mask.sum() < 2:
            print("Poucos documentos válidos para aplicar TF-IDF.")
            return

        # Aqui pode incluir as stopwords adicionais que já discutimos
        from nltk.corpus import stopwords
        stopwords_pt = set(stopwords.words('portuguese'))
        import spacy
        nlp = spacy.load("pt_core_news_sm")
        # ACRESCENTE AS SUAS STOPWORDS PERSONALIZADAS AQUI
        # custom_stopwords = {
        #     "leonardo", "muller", "locução", "narração", "dias",
        #     "vai", "chegou", "você", "esse", "seu", "tudo", "novo"
        # }
        # texto = " ".join(custom_stopwords)
        # doc = nlp(texto)
        # stopwords_pt.update(doc)

        tfidf = TfidfVectorizer(
            max_features=n_features,
            stop_words=list(stopwords_pt),
            min_df=2,
            max_df=0.9
        )

        try:
            title_features = tfidf.fit_transform(texts[valid_mask]).toarray()

            # Criar colunas zeradas e preencher apenas as linhas válidas
            for i in range(title_features.shape[1]):
                self.df_processed[f'text_tfidf_{i}'] = 0.0

            valid_indices = self.df_processed.index[valid_mask]
            for i in range(title_features.shape[1]):
                self.df_processed.loc[valid_indices, f'text_tfidf_{i}'] = title_features[:, i]

            print(f"TF-IDF gerado com {title_features.shape[1]} features (título + descrição).")

        except ValueError as e:
            print(f"Erro ao gerar TF-IDF: {e}")
            print("Prosseguindo sem features de texto.")
    
    def prepare_clustering_features(self):
        """Seleciona e normaliza features para clustering"""
        self.feature_columns = [
            'view_count',
            'like_count',
            'engagement_rate',
            'title_length',
            'description_word_count',
            'duration_segundos',
            'subscriber_count',
        ]
        base_features = self.feature_columns.copy()
    # pega TF-IDF se existir
        tfidf_features = [
            col for col in self.df_processed.columns
            if col.startswith('text_tfidf_') 
        ]

        self.feature_columns = [
            col for col in base_features + tfidf_features
            if col in self.df_processed.columns
        ]

        print("Features selecionadas:")
        print(self.feature_columns)

        X_df = self.df_processed[self.feature_columns].copy()

        # 1) converter tudo para numérico
        for col in X_df.columns:
            X_df[col] = pd.to_numeric(X_df[col], errors='coerce')

        # 2) trocar infinitos por NaN
        X_df = X_df.replace([np.inf, -np.inf], np.nan)

        print("\nNaN antes da imputação:")
        nan_counts = X_df.isna().sum()
        print(nan_counts[nan_counts > 0])

        # 3) preencher NaN com mediana da coluna
        for col in X_df.columns:
            if X_df[col].isna().any():
                med = X_df[col].median()
                if pd.isna(med):
                    med = 0
                X_df[col] = X_df[col].fillna(med)

        # 4) fallback final
        X_df = X_df.fillna(0)

        # segurança extra
        if X_df.isna().sum().sum() > 0:
            raise ValueError("Ainda existem NaNs em X_df após imputação.")

        if np.isinf(X_df.to_numpy()).sum() > 0:
            raise ValueError("Ainda existem infinitos em X_df após limpeza.")

        self.X = X_df.to_numpy(dtype=float)

        from sklearn.preprocessing import StandardScaler
        self.scaler = StandardScaler()
        self.X_scaled = self.scaler.fit_transform(self.X)

        print("\nResumo final:")
        print("Shape X:", self.X.shape)
        print("NaNs em X:", np.isnan(self.X).sum())
        print("NaNs em X_scaled:", np.isnan(self.X_scaled).sum())
    
    def find_optimal_clusters(self, max_k=20):
        """Encontra o número ótimo de clusters"""
        print(f"\n🔍 Procurando número ótimo de clusters (k=2 até {max_k})...")
        
        inertias = []
        silhouette_scores = []
        davies_bouldin_scores = []
        K_range = range(2, max_k + 1)
        
        for k in K_range:
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = km.fit_predict(self.X_scaled)
            
            inertias.append(km.inertia_)
            silhouette_scores.append(silhouette_score(self.X_scaled, labels))
            davies_bouldin_scores.append(davies_bouldin_score(self.X_scaled, labels))
            
            print(f"  k={k}: Silhueta={silhouette_scores[-1]:.3f}, Davies-Bouldin={davies_bouldin_scores[-1]:.3f}")
        
        # Plotar resultados
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))
        
        axes[0].plot(K_range, inertias, 'bo-')
        axes[0].set_xlabel('Número de Clusters (k)')
        axes[0].set_ylabel('Inércia')
        axes[0].set_title('Elbow Method')
        axes[0].grid(True, alpha=0.3)
        
        axes[1].plot(K_range, silhouette_scores, 'go-')
        axes[1].set_xlabel('Número de Clusters (k)')
        axes[1].set_ylabel('Silhueta Score')
        axes[1].set_title('Silhueta Score (maior é melhor)')
        axes[1].grid(True, alpha=0.3)
        
        axes[2].plot(K_range, davies_bouldin_scores, 'ro-')
        axes[2].set_xlabel('Número de Clusters (k)')
        axes[2].set_ylabel('Davies-Bouldin Score')
        axes[2].set_title('Davies-Bouldin Score (menor é melhor)')
        axes[2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('optimal_clusters.png', dpi=300, bbox_inches='tight')
        print("✅ Gráfico salvo: optimal_clusters.png")
        plt.close()
        
        # Escolher k com melhor silhueta
        optimal_k = K_range[np.argmax(silhouette_scores)]
        return optimal_k
    
    def apply_clustering(self, n_clusters=10):
        """Aplica múltiplos algoritmos de clustering"""
        print(f"\n🎪 Aplicando clustering com {n_clusters} clusters...")
        
        # K-Means
        print("  → KMeans...")
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=20)
        self.df_processed['cluster_kmeans'] = kmeans.fit_predict(self.X_scaled)
        kmeans_silhouette = silhouette_score(self.X_scaled, self.df_processed['cluster_kmeans'])
        print(f"    Silhueta KMeans: {kmeans_silhouette:.3f}")
        
        # Hierarchical Clustering
        print("  → Agglomerative Clustering...")
        agg = AgglomerativeClustering(n_clusters=n_clusters, linkage='ward')
        self.df_processed['cluster_hierarchical'] = agg.fit_predict(self.X_scaled)
        hier_silhouette = silhouette_score(self.X_scaled, self.df_processed['cluster_hierarchical'])
        print(f"    Silhueta Hierarchical: {hier_silhouette:.3f}")
        
        # DBSCAN (sem n_clusters especificado)
        print("  → DBSCAN...")
        dbscan = DBSCAN(eps=3, min_samples=5)
        self.df_processed['cluster_dbscan'] = dbscan.fit_predict(self.X_scaled)
        n_dbscan = len(set(self.df_processed['cluster_dbscan'])) - (1 if -1 in self.df_processed['cluster_dbscan'] else 0)
        print(f"    Clusters encontrados: {n_dbscan}")
        
        # Usar KMeans como principal (melhores resultados geralmente)
        self.df_processed['cluster'] = self.df_processed['cluster_kmeans']
        self.kmeans_model = kmeans
        
        return self
    
    def visualize_clusters_pca(self):
        """Visualiza clusters usando PCA"""
        print("\n🎨 Visualizando clusters com PCA...")
        
        self.pca = PCA(n_components=2)
        X_pca = self.pca.fit_transform(self.X_scaled)
        
        explained_var = self.pca.explained_variance_ratio_
        print(f"✅ Variância explicada: {explained_var[0]:.2%} + {explained_var[1]:.2%}")
        
        plt.figure(figsize=(12, 8))
        scatter = plt.scatter(
            X_pca[:, 0], X_pca[:, 1],
            c=self.df_processed['cluster'],
            cmap='tab20', s=50, alpha=0.6, edgecolors='black', linewidth=0.5
        )
        plt.colorbar(scatter, label='Cluster')
        plt.xlabel(f'PC1 ({explained_var[0]:.1%})')
        plt.ylabel(f'PC2 ({explained_var[1]:.1%})')
        plt.title('Clustering de Vídeos YouTube - PCA')
        plt.grid(True, alpha=0.3)
        plt.savefig('clusters_pca.png', dpi=300, bbox_inches='tight')
        print("✅ Gráfico salvo: clusters_pca.png")
        plt.close()
        
        return self
    
    def visualize_clusters_tsne(self, sample_size=1000):
        """Visualiza clusters usando t-SNE (para datasets grandes)"""
        print("\n🎨 Visualizando clusters com t-SNE...")
        
        # Usar amostra para t-SNE por questão de performance
        if len(self.X_scaled) > sample_size:
            indices = np.random.choice(len(self.X_scaled), sample_size, replace=False)
            X_sample = self.X_scaled[indices]
            clusters_sample = self.df_processed['cluster'].iloc[indices].values
        else:
            X_sample = self.X_scaled
            clusters_sample = self.df_processed['cluster'].values
        
        tsne = TSNE(n_components=2, random_state=42, perplexity=30, max_iter=1000)
        X_tsne = tsne.fit_transform(X_sample)
        
        plt.figure(figsize=(12, 8))
        scatter = plt.scatter(
            X_tsne[:, 0], X_tsne[:, 1],
            c=clusters_sample,
            cmap='tab20', s=50, alpha=0.6, edgecolors='black', linewidth=0.5
        )
        plt.colorbar(scatter, label='Cluster')
        plt.xlabel('t-SNE 1')
        plt.ylabel('t-SNE 2')
        plt.title('Clustering de Vídeos YouTube - t-SNE')
        plt.grid(True, alpha=0.3)
        plt.savefig('clusters_tsne.png', dpi=300, bbox_inches='tight')
        print("✅ Gráfico salvo: clusters_tsne.png")
        plt.close()
        
        return self
    
    def analyze_clusters(self):
        """Analisa características de cada cluster"""
        print("\n📊 Análise de Características dos Clusters")
        print("=" * 80)
        
        analysis_features = [
            'view_count', 'engagement_rate', 'virality_index',
            'duration_segundos', 'subscriber_count', 'freshness_score',
            'title_sentiment', 'title_word_count', 'content_quality'
        ]
        
        analysis_features = [f for f in analysis_features if f in self.df_processed.columns]
        
        cluster_analysis = self.df_processed.groupby('cluster')[analysis_features].agg(['mean', 'median', 'std'])
        
        print("\n📈 Estatísticas por Cluster:")
        for cluster_id in sorted(self.df_processed['cluster'].unique()):
            cluster_data = self.df_processed[self.df_processed['cluster'] == cluster_id]
            
            print(f"\n🎯 CLUSTER {cluster_id}")
            print(f"   Vídeos: {len(cluster_data)}")
            print(f"   Views médias: {cluster_data['view_count'].mean():,.0f}")
            print(f"   Taxa engajamento: {cluster_data['engagement_rate'].mean():.2%}")
            print(f"   Índice virality: {cluster_data['virality_index'].mean():.4f}")
            print(f"   Duração média: {cluster_data['duration_segundos'].mean():.0f}s")
            print(f"   Sentimento título: {cluster_data['title_sentiment'].mean():.2f}")
            print(f"   Seguidores canal: {cluster_data['subscriber_count'].mean():,.0f}")
            
            # Encontrar exemplos
            top_videos = cluster_data.nlargest(3, 'view_count')[['title_processed', 'view_count', 'engagement_rate']]
            print(f"\n   Top vídeos:")
            for idx, (_, row) in enumerate(top_videos.iterrows(), 1):
                print(f"     {idx}. {row['title_processed'][:60]}...")
                print(f"        Views: {row['view_count']:,.0f} | Engajamento: {row['engagement_rate']:.2%}")
        
        return self
    
    def create_cluster_summary(self):
        """Cria resumo visual dos clusters"""
        print("\n📋 Criando resumo visual dos clusters...")
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Distribuição de clusters
        cluster_counts = self.df_processed['cluster'].value_counts().sort_index()
        axes[0, 0].bar(cluster_counts.index, cluster_counts.values, color='skyblue', edgecolor='black')
        axes[0, 0].set_xlabel('Cluster')
        axes[0, 0].set_ylabel('Número de Vídeos')
        axes[0, 0].set_title('Distribuição de Vídeos por Cluster')
        axes[0, 0].grid(True, alpha=0.3, axis='y')
        
        # Views por cluster
        self.df_processed.boxplot(column='view_count', by='cluster', ax=axes[0, 1])
        axes[0, 1].set_xlabel('Cluster')
        axes[0, 1].set_ylabel('View Count')
        axes[0, 1].set_title('Distribuição de Views por Cluster')
        plt.sca(axes[0, 1])
        plt.xticks(rotation=0)
        
        # Engajamento por cluster
        cluster_engagement = self.df_processed.groupby('cluster')['engagement_rate'].mean()
        axes[1, 0].bar(cluster_engagement.index, cluster_engagement.values, color='lightgreen', edgecolor='black')
        axes[1, 0].set_xlabel('Cluster')
        axes[1, 0].set_ylabel('Taxa de Engajamento')
        axes[1, 0].set_title('Engajamento Médio por Cluster')
        axes[1, 0].grid(True, alpha=0.3, axis='y')
        
        # Duração por cluster
        cluster_duration = self.df_processed.groupby('cluster')['duration_segundos'].mean()
        axes[1, 1].bar(cluster_duration.index, cluster_duration.values, color='lightsalmon', edgecolor='black')
        axes[1, 1].set_xlabel('Cluster')
        axes[1, 1].set_ylabel('Duração (segundos)')
        axes[1, 1].set_title('Duração Média por Cluster')
        axes[1, 1].grid(True, alpha=0.3, axis='y')
        
        plt.suptitle('Resumo de Clusters', fontsize=16, y=1.00)
        plt.tight_layout()
        plt.savefig('cluster_summary.png', dpi=300, bbox_inches='tight')
        print("✅ Gráfico salvo: cluster_summary.png")
        plt.close()
        
        return self
    
    def save_results(self, output_file='youtube_clusters_results.csv'):
        """Salva os resultados do clustering"""
        print(f"\n💾 Salvando resultados em {output_file}...")
        
        output_df = self.df_processed[[
            'video_id', 'title_processed', 'view_count', 'engagement_rate',
             'cluster', 'cluster_kmeans', 'cluster_hierarchical',
            'virality_index', 'content_quality', 'freshness_score'
        ]].copy()
        
        output_df.to_csv(output_file, index=False)
        print(f"✅ Arquivo salvo: {output_file}")
        
        return self
    
    def run_full_analysis(self, n_clusters=None, find_optimal=True, n_features=200):
        """Executa a análise completa"""
        print("🚀 INICIANDO ANÁLISE DE CLUSTERING")
        print("=" * 80)
        
        self.load_and_explore()
        self.prepare_data()
        self.create_advanced_features()
        self.extract_text_features(n_features=n_features)
        self.prepare_clustering_features()
        
        if find_optimal:
            n_clusters = self.find_optimal_clusters(max_k=20)
            print(f"\n✨ Número ótimo de clusters: {n_clusters}")
        elif n_clusters is None:
            n_clusters = 5
        
        self.apply_clustering(n_clusters=n_clusters)
        self.visualize_clusters_pca()
        self.visualize_clusters_tsne()
        self.analyze_clusters()
        self.create_cluster_summary()
        self.save_results()
        
        print("\n" + "=" * 80)
        print("✅ ANÁLISE CONCLUÍDA COM SUCESSO!")
        print("=" * 80)
        
        return self


if __name__ == "__main__":
    # Carregar dados
    analyzer = YoutubeVideoClusterAnalyzer('seu_dataset.csv')
    
    # Executar análise completa
    analyzer.run_full_analysis(find_optimal=True)
    
    # Opcionalmente, acessar resultados
    print("\n📊 Dataset com clusters:")
    print(analyzer.df_processed[['title_processed', 'view_count', 'cluster']].head(10))