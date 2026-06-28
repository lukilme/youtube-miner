import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR  # SVM para regressão
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    mean_absolute_percentage_error
)
import warnings
warnings.filterwarnings('ignore')

# ==================== CONFIGURAÇÃO ====================
np.random.seed(42)
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# ==================== GERAÇÃO DE DADOS DE EXEMPLO ====================
def gerar_dados_exemplo(n_samples=500):
    """
    Gera dataset simulado com as features do YouTube
    """
    data = {
        'title': [f'Video {i} Amazing Content Trending' for i in range(n_samples)],
        'description': [f'Description for video {i} with tags and keywords' for i in range(n_samples)],
        'view_count': np.random.exponential(10000, n_samples).astype(int),
        'like_count': np.random.exponential(500, n_samples).astype(int),
        'comment_count': np.random.exponential(100, n_samples).astype(int),
        'duration_segundos': np.random.randint(60, 3600, n_samples),
        'subscriber_count': np.random.exponential(100000, n_samples).astype(int),
        'engagement_rate': np.random.uniform(0.01, 0.15, n_samples),
        'title_length': np.random.randint(10, 100, n_samples),
        'title_word_count': np.random.randint(2, 15, n_samples),
        'channel_age_days': np.random.randint(30, 3650, n_samples),
    }
    
    df = pd.DataFrame(data)
    return df

# ==================== PREPARAÇÃO DOS DADOS ====================
def preparar_dados(df, target='view_count', test_size=0.2):
    """
    Prepara dados para treinamento com TF-IDF
    """
    print("=" * 60)
    print("PREPARAÇÃO DOS DADOS")
    print("=" * 60)
    
    # Verificar dados faltantes
    print(f"\nDados faltantes:\n{df.isnull().sum()}")
    df = df.fillna(0)
    
    # Separar features de texto e numéricas
    texto_features = df[['title', 'description']]
    numeric_features = df[[col for col in df.columns 
                          if col not in ['title', 'description', target]]]
    
    # Combinar texto
    df['texto_combinado'] = df['title'] + ' ' + df['description']
    
    # TF-IDF
    print(f"\n📊 Aplicando TF-IDF...")
    tfidf = TfidfVectorizer(
        max_features=50,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.8,
        stop_words='english'
    )
    tfidf_features = tfidf.fit_transform(df['texto_combinado']).toarray()
    tfidf_df = pd.DataFrame(tfidf_features, columns=[f'tfidf_{i}' for i in range(tfidf_features.shape[1])])
    
    # Combinação final de features
    X = pd.concat([numeric_features, tfidf_df], axis=1)
    y = df[target].values
    
    # Log transform do target para melhor distribuição
    y_log = np.log1p(y)
    
    print(f"✅ Features criadas: {X.shape[1]}")
    print(f"   - Features numéricos: {numeric_features.shape[1]}")
    print(f"   - Features TF-IDF: {tfidf_df.shape[1]}")
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_log, test_size=test_size, random_state=42
    )
    
    # Normalização
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"\n📈 Conjuntos de dados:")
    print(f"   - Treino: {X_train_scaled.shape[0]} amostras")
    print(f"   - Teste: {X_test_scaled.shape[0]} amostras")
    
    return {
        'X_train': X_train_scaled,
        'X_test': X_test_scaled,
        'y_train': y_train,
        'y_test': y_test,
        'feature_names': X.columns.tolist()
    }

# ==================== MODELOS ====================
class ModeloRegressao:
    def __init__(self, nome, modelo):
        self.nome = nome
        self.modelo = modelo
        self.historico = {}
    
    def treinar(self, X_train, y_train):
        print(f"\n🚀 Treinando {self.nome}...")
        self.modelo.fit(X_train, y_train)
        print(f"   ✅ Modelo treinado com sucesso")
    
    def avaliar(self, X_test, y_test):
        y_pred = self.modelo.predict(X_test)
        
        # Converter de volta da log scale
        y_test_original = np.expm1(y_test)
        y_pred_original = np.expm1(y_pred)
        
        self.historico['y_pred'] = y_pred
        self.historico['y_pred_original'] = y_pred_original
        self.historico['y_test'] = y_test
        
        # Métricas em escala log
        rmse_log = np.sqrt(mean_squared_error(y_test, y_pred))
        mae_log = mean_absolute_error(y_test, y_pred)
        r2_log = r2_score(y_test, y_pred)
        
        # Métricas na escala original
        rmse_original = np.sqrt(mean_squared_error(y_test_original, y_pred_original))
        mae_original = mean_absolute_error(y_test_original, y_pred_original)
        r2_original = r2_score(y_test_original, y_pred_original)
        mape = mean_absolute_percentage_error(y_test_original, y_pred_original)
        
        self.historico['metricas'] = {
            'RMSE (log)': rmse_log,
            'MAE (log)': mae_log,
            'R² (log)': r2_log,
            'RMSE (original)': rmse_original,
            'MAE (original)': mae_original,
            'R² (original)': r2_original,
            'MAPE': mape
        }
        
        return self.historico['metricas']
    
    def cross_validate(self, X_train, y_train, cv=5):
        scores = cross_val_score(self.modelo, X_train, y_train, 
                                cv=cv, scoring='r2')
        self.historico['cv_scores'] = scores
        return scores

# ==================== COMPARAÇÃO DE MODELOS ====================
def treinar_e_comparar_modelos(X_train, X_test, y_train, y_test):
    """
    Treina os três modelos especificados
    """
    print("\n" + "=" * 60)
    print("TREINAMENTO E AVALIAÇÃO DOS MODELOS")
    print("=" * 60)
    
    modelos = {
        'TF-IDF + SVM (Linear)': ModeloRegressao(
            'TF-IDF + SVM (Linear)',
            SVR(kernel='linear', C=100, epsilon=0.1)
        ),
        'TF-IDF + Logistic Regression': ModeloRegressao(
            'TF-IDF + Logistic Regression',
            LinearRegression()  # Note: LogisticRegression é para classificação
        ),
        'TF-IDF + Random Forest': ModeloRegressao(
            'TF-IDF + Random Forest',
            RandomForestRegressor(n_estimators=100, max_depth=15, 
                                random_state=42, n_jobs=-1)
        )
    }
    
    resultados = {}
    
    for nome, modelo in modelos.items():
        print(f"\n{'─' * 60}")
        modelo.treinar(X_train, y_train)
        metricas = modelo.avaliar(X_test, y_test)
        cv_scores = modelo.cross_validate(X_train, y_train)
        
        resultados[nome] = {
            'modelo': modelo,
            'metricas': metricas,
            'cv_scores': cv_scores
        }
        
        print(f"\n📊 Métricas - {nome}:")
        print(f"   R² (Escala Original): {metricas['R² (original)']:.4f}")
        print(f"   RMSE (Escala Original): {metricas['RMSE (original)']:.2f}")
        print(f"   MAE (Escala Original): {metricas['MAE (original)']:.2f}")
        print(f"   MAPE: {metricas['MAPE']:.4f}")
        print(f"   Cross-Validation R² Médio: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
    
    return resultados

# ==================== VISUALIZAÇÕES ====================
def visualizar_resultados(resultados, y_test):
    """
    Cria gráficos de comparação dos modelos
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Comparação de Modelos de Regressão', fontsize=16, fontweight='bold')
    
    # 1. Comparação de R²
    ax = axes[0, 0]
    r2_scores = [resultados[nome]['metricas']['R² (original)'] for nome in resultados.keys()]
    cores = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    bars = ax.bar(range(len(resultados)), r2_scores, color=cores, alpha=0.7)
    ax.set_ylabel('R² Score', fontweight='bold')
    ax.set_title('Coeficiente de Determinação (R²)')
    ax.set_xticks(range(len(resultados)))
    ax.set_xticklabels([nome.split('+')[1].strip() for nome in resultados.keys()], rotation=15)
    ax.set_ylim([0, 1])
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}', ha='center', va='bottom', fontweight='bold')
    
    # 2. Comparação de RMSE
    ax = axes[0, 1]
    rmse_scores = [resultados[nome]['metricas']['RMSE (original)'] for nome in resultados.keys()]
    bars = ax.bar(range(len(resultados)), rmse_scores, color=cores, alpha=0.7)
    ax.set_ylabel('RMSE', fontweight='bold')
    ax.set_title('Root Mean Squared Error')
    ax.set_xticks(range(len(resultados)))
    ax.set_xticklabels([nome.split('+')[1].strip() for nome in resultados.keys()], rotation=15)
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.0f}', ha='center', va='bottom', fontweight='bold')
    
    # 3. Scatter - Predição vs Real (SVM)
    ax = axes[1, 0]
    svm_pred = resultados['TF-IDF + SVM (Linear)']['modelo'].historico['y_pred_original']
    y_test_original = np.expm1(y_test)
    ax.scatter(y_test_original, svm_pred, alpha=0.6, s=30, color='#FF6B6B')
    ax.plot([y_test_original.min(), y_test_original.max()], 
            [y_test_original.min(), y_test_original.max()], 
            'k--', lw=2, label='Perfeito')
    ax.set_xlabel('Valores Reais', fontweight='bold')
    ax.set_ylabel('Valores Preditos', fontweight='bold')
    ax.set_title('SVM - Predição vs Real')
    ax.legend()
    
    # 4. Scatter - Predição vs Real (Random Forest)
    ax = axes[1, 1]
    rf_pred = resultados['TF-IDF + Random Forest']['modelo'].historico['y_pred_original']
    ax.scatter(y_test_original, rf_pred, alpha=0.6, s=30, color='#45B7D1')
    ax.plot([y_test_original.min(), y_test_original.max()], 
            [y_test_original.min(), y_test_original.max()], 
            'k--', lw=2, label='Perfeito')
    ax.set_xlabel('Valores Reais', fontweight='bold')
    ax.set_ylabel('Valores Preditos', fontweight='bold')
    ax.set_title('Random Forest - Predição vs Real')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('/home/claude/comparacao_modelos.png', dpi=300, bbox_inches='tight')
    print("\n✅ Gráfico salvo: comparacao_modelos.png")
    plt.close()

# ==================== FEATURE IMPORTANCE ====================
def mostrar_feature_importance(resultados, feature_names):
    """
    Mostra importância das features (Random Forest)
    """
    rf_model = resultados['TF-IDF + Random Forest']['modelo'].modelo
    importances = rf_model.feature_importances_
    indices = np.argsort(importances)[-15:]  # Top 15
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(range(len(indices)), importances[indices], color='#45B7D1', alpha=0.8)
    ax.set_yticks(range(len(indices)))
    ax.set_yticklabels([feature_names[i] for i in indices])
    ax.set_xlabel('Importância', fontweight='bold')
    ax.set_title('Top 15 Features - Random Forest', fontweight='bold')
    plt.tight_layout()
    plt.savefig('/home/claude/feature_importance.png', dpi=300, bbox_inches='tight')
    print("✅ Gráfico salvo: feature_importance.png")
    plt.close()

# ==================== RESUMO EXECUTIVO ====================
def gerar_relatorio(resultados):
    """
    Gera relatório comparativo dos modelos
    """
    print("\n" + "=" * 60)
    print("RELATÓRIO EXECUTIVO - COMPARAÇÃO DE MODELOS")
    print("=" * 60)
    
    df_resultados = pd.DataFrame({
        nome: resultado['metricas'] 
        for nome, resultado in resultados.items()
    }).T
    
    print("\n📋 Resumo de Métricas:")
    print(df_resultados.to_string())
    
    print("\n🏆 Melhores Modelos:")
    best_r2 = df_resultados['R² (original)'].idxmax()
    best_rmse = df_resultados['RMSE (original)'].idxmin()
    best_mape = df_resultados['MAPE'].idxmin()
    
    print(f"   • Melhor R²: {best_r2}")
    print(f"   • Melhor RMSE: {best_rmse}")
    print(f"   • Melhor MAPE: {best_mape}")
    
    # Salvar relatório
    with open('/home/claude/relatorio_modelos.txt', 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("RELATÓRIO DE REGRESSÃO - PREVISÃO DE PERFORMANCE DE VÍDEOS\n")
        f.write("=" * 60 + "\n\n")
        f.write(df_resultados.to_string())
        f.write(f"\n\nMelhor modelo geral: {best_r2}\n")
    
    print("\n✅ Relatório salvo: relatorio_modelos.txt")

def main():
    print("\n" + "🎬 " * 10)
    print("SISTEMA DE PREVISÃO DE PERFORMANCE DE VÍDEOS YOUTUBE")
    print("🎬 " * 10 + "\n")
    
    # Gerar dados
    print("📥 Gerando dados de exemplo...")
    df = gerar_dados_exemplo(n_samples=500)
    print(f"✅ Dataset criado com {len(df)} vídeos")
    
    # Preparar dados
    dados = preparar_dados(df, target='view_count')
    
    # Treinar modelos
    resultados = treinar_e_comparar_modelos(
        dados['X_train'],
        dados['X_test'],
        dados['y_train'],
        dados['y_test']
    )
    
    # Visualizar
    print("\n📊 Gerando visualizações...")
    visualizar_resultados(resultados, dados['y_test'])
    mostrar_feature_importance(resultados, dados['feature_names'])
    
    # Relatório
    gerar_relatorio(resultados)
    
    print("\n" + "=" * 60)
    print("✨ PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
    print("=" * 60)
    print("\n📁 Arquivos gerados:")
    print("   • comparacao_modelos.png")
    print("   • feature_importance.png")
    print("   • relatorio_modelos.txt")

if __name__ == "__main__":
    main()