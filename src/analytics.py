import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.preprocessing import RobustScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
from scipy import stats

TRUSTED_DIR = Path("data/trusted")

VARS_CLUSTER = [
    'RENDA_PER_CAPITA_2010',
    'IDHM_2010',
    'PCT_ESCOLAS_COM_INTERNET',
    'PCT_ESCOLAS_COM_BIBLIOTECA_LEITURA',
    'PCT_ESCOLAS_COM_LAB_INFORMATICA',
    'PCT_ESCOLAS_COM_QUADRA',
    'PCT_ESCOLAS_COM_AGUA_ADEQUADA',
    'PCT_ESCOLAS_COM_ESGOTO_ADEQUADO',
    'MEDIA_ALUNOS_POR_TURMA_FUND',
    'PCT_MAT_15_ANOS_OU_MAIS_PROXY_DISTSERIE',
]

VARS_COMPARACAO = [
    'VL_OBSERVADO_2023',
    'RENDA_PER_CAPITA_2010',
    'IDHM_2010',
    'PCT_ESCOLAS_COM_INTERNET',
    'PCT_ESCOLAS_COM_BIBLIOTECA_LEITURA',
    'PCT_ESCOLAS_COM_LAB_INFORMATICA',
    'PCT_ESCOLAS_COM_QUADRA',
    'PCT_ESCOLAS_COM_AGUA_ADEQUADA',
    'PCT_ESCOLAS_COM_ESGOTO_ADEQUADO',
    'MEDIA_ALUNOS_POR_TURMA_FUND',
    'PCT_MAT_15_ANOS_OU_MAIS_PROXY_DISTSERIE',
]

VARS_RF = VARS_CLUSTER + ['PCT_DOC_COM_SUPERIOR']


# ── FUNÇÕES ───────────────────────────────────────────────────────────────────

def carregar_dados() -> pd.DataFrame:
    df = pd.read_csv(TRUSTED_DIR / "indicadores_municipais_ma.csv", sep=";")
    df['PCT_DOC_COM_SUPERIOR'] = (
        df['QT_DOC_BAS_ESCO_SUP_GRAD'] / df['QT_DOC_BAS'] * 100
    ).round(2)
    df['PCT_DOC_COM_LICENCIATURA'] = (
        df['QT_DOC_BAS_ESCO_SUP_GRAD_LICEN'] / df['QT_DOC_BAS'] * 100
    ).round(2)
    return df


def normalizar(df: pd.DataFrame) -> tuple:
    X = df[VARS_CLUSTER].copy()
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X)
    return X_scaled, scaler


def elbow_silhouette(X_scaled, k_range: range) -> list:
    inertias, silhouettes = [], []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        inertias.append(km.inertia_)
        silhouettes.append(silhouette_score(X_scaled, labels))

    best_k = k_range[silhouettes.index(max(silhouettes))]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].plot(k_range, inertias, marker='o', color='steelblue', linewidth=2)
    axes[0].set_title('Elbow Method')
    axes[0].set_xlabel('Número de clusters (k)')
    axes[0].set_ylabel('Inércia')

    axes[1].plot(k_range, silhouettes, marker='o', color='darkorange', linewidth=2)
    axes[1].set_title('Silhouette Score')
    axes[1].set_xlabel('Número de clusters (k)')
    axes[1].set_ylabel('Score')
    axes[1].axvline(best_k, color='red', linestyle='--',
                    label=f'Melhor k={best_k} ({max(silhouettes):.3f})')
    axes[1].legend()

    plt.tight_layout()
    plt.savefig('reports/figures/elbow_silhouette.png', dpi=150, bbox_inches='tight')

    print(f"\nMelhor k pelo Silhouette: {best_k} (score: {max(silhouettes):.3f})")
    print("\nTodos os scores:")
    for k, s in zip(k_range, silhouettes):
        print(f"  k={k}: {s:.3f}")

    return silhouettes


def visualizar_pca(X_scaled, silhouettes: list, k_range: range) -> None:
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    variancia = pca.explained_variance_ratio_

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for idx, k in enumerate([2, 3, 4]):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        axes[idx].scatter(X_pca[:, 0], X_pca[:, 1], c=labels,
                          cmap='Set1', alpha=0.6, s=40)
        axes[idx].set_title(f'k={k} | silhouette={silhouettes[k-2]:.3f}')
        axes[idx].set_xlabel(f'PC1 ({variancia[0]*100:.1f}% variância)')
        axes[idx].set_ylabel(f'PC2 ({variancia[1]*100:.1f}% variância)')

    plt.suptitle('Visualização PCA dos Clusters', fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig('reports/figures/pca_clusters.png', dpi=150, bbox_inches='tight')


def clusterizar(df: pd.DataFrame, X_scaled, k: int = 3) -> pd.DataFrame:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    df['CLUSTER'] = km.fit_predict(X_scaled)

    print("\nTamanho dos clusters:")
    print(df['CLUSTER'].value_counts().sort_index())

    print("\nCLUSTER 1 — Municípios atípicos (alta renda):")
    print(df[df['CLUSTER'] == 1][['NO_MUNICIPIO', 'RENDA_PER_CAPITA_2010',
                                   'VL_OBSERVADO_2023']].sort_values(
        'RENDA_PER_CAPITA_2010', ascending=False).to_string())

    for cid, nome in [(0, 'vulneráveis'), (2, 'intermediários')]:
        sub = df[df['CLUSTER'] == cid]['VL_OBSERVADO_2023']
        print(f"\nCLUSTER {cid} — Municípios {nome} ({len(sub)} municípios):")
        print(f"  IDEB médio: {sub.mean():.2f}  |  min: {sub.min():.2f}  |  max: {sub.max():.2f}")

    return df


def outliers_positivos(df: pd.DataFrame) -> None:
    for cid in [0, 2]:
        sub = df[df['CLUSTER'] == cid]
        limiar = sub['VL_OBSERVADO_2023'].mean() + sub['VL_OBSERVADO_2023'].std()
        top = sub[sub['VL_OBSERVADO_2023'] >= limiar]
        print(f"\nOutliers positivos Cluster {cid} (IDEB >= {limiar:.2f}):")
        print(top[['NO_MUNICIPIO', 'VL_OBSERVADO_2023',
                   'RENDA_PER_CAPITA_2010', 'IDHM_2010']].sort_values(
            'VL_OBSERVADO_2023', ascending=False).to_string())


def classificar_perfil(cluster_df: pd.DataFrame) -> pd.DataFrame:
    media = cluster_df['VL_OBSERVADO_2023'].mean()
    std = cluster_df['VL_OBSERVADO_2023'].std()
    cluster_df = cluster_df.copy()
    cluster_df['PERFIL'] = 'médio'
    cluster_df.loc[cluster_df['VL_OBSERVADO_2023'] >= media + std, 'PERFIL'] = 'alto'
    cluster_df.loc[cluster_df['VL_OBSERVADO_2023'] <= media - std, 'PERFIL'] = 'baixo'
    return cluster_df


def comparar_perfis(df: pd.DataFrame) -> None:
    for cid, nome in [(0, 'Cluster 0 — Vulneráveis'), (2, 'Cluster 2 — Intermediários')]:
        sub = classificar_perfil(df[df['CLUSTER'] == cid])
        print(f"\nDistribuição por perfil — {nome}:")
        print(sub['PERFIL'].value_counts())
        print(f"\nPerfil médio por grupo ({nome}):")
        print(sub.groupby('PERFIL')[VARS_COMPARACAO].mean().round(2).T.to_string())


def mann_whitney(df: pd.DataFrame) -> None:
    for cid, nome in [(0, 'Cluster 0'), (2, 'Cluster 2')]:
        sub = classificar_perfil(df[df['CLUSTER'] == cid])
        alto = sub[sub['PERFIL'] == 'alto']
        baixo = sub[sub['PERFIL'] == 'baixo']
        print(f"\nTestes Mann-Whitney (alto vs baixo) — {nome}:")
        for var in VARS_COMPARACAO[1:]:
            _, p = stats.mannwhitneyu(alto[var], baixo[var], alternative='two-sided')
            sig = '***' if p < 0.01 else '**' if p < 0.05 else '*' if p < 0.1 else ''
            print(f"  {var:<45} p={p:.3f} {sig}")


def random_forest(df: pd.DataFrame) -> None:
    print("\n" + "=" * 60)
    print("RANDOM FOREST — Importância de variáveis")
    print("=" * 60)

    df_rf = df[df['CLUSTER'].isin([0, 2])].copy()
    X_rf = df_rf[VARS_RF]
    y_rf = df_rf['VL_OBSERVADO_2023']

    rf = RandomForestRegressor(n_estimators=200, random_state=42)
    rf.fit(X_rf, y_rf)
    print(f"\nR² no treino: {rf.score(X_rf, y_rf):.3f}")

    importancias = pd.Series(rf.feature_importances_, index=VARS_RF).sort_values(ascending=False)
    print("\nImportância das variáveis (ordem decrescente):")
    for var, imp in importancias.items():
        bar = '█' * int(imp * 100)
        print(f"  {var:<45} {imp:.3f}  {bar}")

    fig, ax = plt.subplots(figsize=(10, 6))
    importancias.sort_values().plot(kind='barh', ax=ax, color='steelblue')
    ax.set_title('Random Forest — Importância das Variáveis para Predição do IDEB', fontsize=12)
    ax.set_xlabel('Importância')
    ax.axvline(1 / len(VARS_RF), color='red', linestyle='--',
               label=f'Importância uniforme ({1/len(VARS_RF):.3f})')
    ax.legend()
    plt.tight_layout()
    plt.savefig('reports/figures/random_forest_importancia.png', dpi=150, bbox_inches='tight')


# ── PIPELINE PRINCIPAL ────────────────────────────────────────────────────────

def main() -> None:
    df = carregar_dados()
    X_scaled, _ = normalizar(df)

    k_range = range(2, 11)
    silhouettes = elbow_silhouette(X_scaled, k_range)
    visualizar_pca(X_scaled, silhouettes, k_range)

    df = clusterizar(df, X_scaled, k=3)
    outliers_positivos(df)
    comparar_perfis(df)
    mann_whitney(df)
    random_forest(df)


if __name__ == "__main__":
    main()