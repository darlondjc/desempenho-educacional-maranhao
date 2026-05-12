import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import unicodedata
from pathlib import Path
from sklearn.preprocessing import RobustScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, adjusted_rand_score
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from scipy import stats

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRUSTED_DIR = PROJECT_ROOT / "data" / "trusted"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"

VARS_CLUSTER = [
    'RENDA_PER_CAPITA_2010',
    'IDHM_2010',
]

CLUSTER_K = 2

VARS_EXPLICATIVAS_IDEB = [
    'RENDA_PER_CAPITA_2010',
    'IDHM_2010',
    'PCT_ESCOLAS_COM_INTERNET',
    'PCT_ESCOLAS_COM_BIBLIOTECA_LEITURA',
    'PCT_ESCOLAS_COM_LAB_INFORMATICA',
    'PCT_ESCOLAS_COM_QUADRA',
    'PCT_ESCOLAS_COM_AGUA_ADEQUADA',
    'PCT_ESCOLAS_COM_ESGOTO_ADEQUADO',
    'PCT_DOC_SUPERIOR_COMPLETO',
    'PCT_DOC_LICENCIATURA_TOTAL',
    'MEDIA_ALUNOS_POR_TURMA_BAS',
    'MEDIA_ALUNOS_POR_TURMA_FUND',
    'MEDIA_ALUNOS_POR_TURMA_MED',
    'PCT_MAT_15_ANOS_OU_MAIS_PROXY_DISTSERIE',
    'PCT_TURMAS_CORRFLUXO_FUND_AF',
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


def _renderizar_ou_salvar(nome_arquivo: str, salvar_arquivo: bool = True) -> None:
    if salvar_arquivo:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        plt.savefig(FIGURES_DIR / nome_arquivo, dpi=150, bbox_inches='tight')
    else:
        plt.show()
    plt.close()


def elbow_silhouette(X_scaled, k_range: range, salvar_arquivo: bool = True) -> list:
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
    _renderizar_ou_salvar("elbow_silhouette.png", salvar_arquivo=salvar_arquivo)

    print(f"\nMelhor k pelo Silhouette: {best_k} (score: {max(silhouettes):.3f})")
    print("\nTodos os scores:")
    for k, s in zip(k_range, silhouettes):
        print(f"  k={k}: {s:.3f}")

    return silhouettes


def visualizar_pca(X_scaled, silhouettes: list, k_range: range, salvar_arquivo: bool = True) -> None:
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
    _renderizar_ou_salvar("pca_clusters.png", salvar_arquivo=salvar_arquivo)


def clusterizar(df: pd.DataFrame, X_scaled, k: int = 3) -> pd.DataFrame:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    df['CLUSTER'] = km.fit_predict(X_scaled)
    df = nomear_clusters(df)

    print("\nTamanho dos clusters:")
    print(df.groupby('CLUSTER_NOME').size().sort_values(ascending=False))

    for cid in _clusters_ordenados_por_renda(df):
        nome = _nome_cluster(df, cid)
        sub = df[df['CLUSTER'] == cid]
        print(f"\nCluster {nome} — municípios ({len(sub)}):")
        print(sub[['NO_MUNICIPIO', 'RENDA_PER_CAPITA_2010', 'VL_OBSERVADO_2023']]
              .sort_values('RENDA_PER_CAPITA_2010', ascending=False)
              .to_string(index=False))

    for nome in [n for n in df['CLUSTER_NOME'].dropna().unique() if n != 'alta renda']:
        sub = df[df['CLUSTER_NOME'] == nome]['VL_OBSERVADO_2023']
        print(f"\nCluster {nome} ({len(sub)} municípios):")
        print(f"  IDEB médio: {sub.mean():.2f}  |  min: {sub.min():.2f}  |  max: {sub.max():.2f}")

    return df


def nomear_clusters(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    medias_renda = df.groupby('CLUSTER')['RENDA_PER_CAPITA_2010'].mean().sort_values()
    ordem = list(medias_renda.index)

    if len(ordem) == 3:
        nomes = ['vulneráveis', 'intermediários', 'alta renda']
        mapa = {cid: nomes[i] for i, cid in enumerate(ordem)}
    elif len(ordem) == 2:
        nomes = ['vulneráveis', 'maior renda']
        mapa = {cid: nomes[i] for i, cid in enumerate(ordem)}
    else:
        mapa = {cid: f'grupo {i + 1}' for i, cid in enumerate(ordem)}

    df['CLUSTER_NOME'] = df['CLUSTER'].map(mapa)
    return df


def _clusters_ordenados_por_renda(df: pd.DataFrame) -> list:
    ordem = (
        df.groupby(['CLUSTER', 'CLUSTER_NOME'])['RENDA_PER_CAPITA_2010']
        .mean()
        .sort_values()
        .index
    )
    return [cid for cid, _ in ordem]


def _nome_cluster(df: pd.DataFrame, cid: int) -> str:
    sub = df[df['CLUSTER'] == cid]
    if sub.empty or 'CLUSTER_NOME' not in sub.columns:
        return f'cluster {cid}'
    return str(sub['CLUSTER_NOME'].iloc[0])


def _clusters_analise_intragrupo(df: pd.DataFrame) -> list:
    return _clusters_ordenados_por_renda(df)


def _slug_cluster_nome(nome: str) -> str:
    texto = unicodedata.normalize('NFKD', nome).encode('ascii', 'ignore').decode('ascii')
    return texto.replace(' ', '_').lower()


def _estabilidade_clusters(X, labels_referencia, k: int, n_bootstrap: int = 25, frac_amostra: float = 0.8) -> float:
    n = len(X)
    tamanho_amostra = max(20, int(n * frac_amostra))
    aris = []

    for seed in range(n_bootstrap):
        rng = np.random.default_rng(42 + seed)
        idx = rng.choice(n, size=tamanho_amostra, replace=True)
        X_boot = X[idx]

        km = KMeans(n_clusters=k, random_state=42 + seed, n_init=10)
        labels_boot = km.fit_predict(X_boot)
        ari = adjusted_rand_score(labels_referencia[idx], labels_boot)
        aris.append(ari)

    return float(np.mean(aris))


def relevancia_variaveis_cluster(X_scaled, k: int = 3, n_bootstrap: int = 25) -> pd.DataFrame:
    km_base = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels_base = km_base.fit_predict(X_scaled)
    silhouette_base = silhouette_score(X_scaled, labels_base)
    estabilidade_base = _estabilidade_clusters(X_scaled, labels_base, k=k, n_bootstrap=n_bootstrap)

    resultados = []
    for i, var in enumerate(VARS_CLUSTER):
        cols_sem_var = [j for j in range(X_scaled.shape[1]) if j != i]
        X_sem_var = X_scaled[:, cols_sem_var]

        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels_sem_var = km.fit_predict(X_sem_var)

        silhouette_sem_var = silhouette_score(X_sem_var, labels_sem_var)
        estabilidade_sem_var = _estabilidade_clusters(
            X_sem_var, labels_base, k=k, n_bootstrap=n_bootstrap
        )

        resultados.append({
            'variavel': var,
            'delta_silhouette': silhouette_base - silhouette_sem_var,
            'delta_estabilidade': estabilidade_base - estabilidade_sem_var,
            'ari_vs_base': adjusted_rand_score(labels_base, labels_sem_var),
        })

    df_rel = pd.DataFrame(resultados)
    df_rel['score_relevancia'] = (
        df_rel['delta_silhouette'].clip(lower=0) +
        df_rel['delta_estabilidade'].clip(lower=0) +
        (1 - df_rel['ari_vs_base'])
    )
    df_rel = df_rel.sort_values('score_relevancia', ascending=False).reset_index(drop=True)

    print("\n" + "=" * 60)
    print("RELEVÂNCIA DE VARIÁVEIS PARA CLUSTERIZAÇÃO (ABLAÇÃO)")
    print("=" * 60)
    print(f"Silhouette base (k={k}): {silhouette_base:.3f}")
    print(f"Estabilidade base (ARI bootstrap): {estabilidade_base:.3f}")
    print("\nQuanto maior o score_relevancia, mais a variável contribui para os clusters.")
    print(df_rel[['variavel', 'delta_silhouette', 'delta_estabilidade', 'ari_vs_base', 'score_relevancia']]
          .round(4)
          .to_string(index=False))

    return df_rel


def outliers_positivos(df: pd.DataFrame) -> None:
    for cid in _clusters_analise_intragrupo(df):
        sub = df[df['CLUSTER'] == cid]
        limiar = sub['VL_OBSERVADO_2023'].mean() + sub['VL_OBSERVADO_2023'].std()
        top = sub[sub['VL_OBSERVADO_2023'] >= limiar]
        print(f"\nOutliers positivos Cluster {_nome_cluster(df, cid)} (IDEB >= {limiar:.2f}):")
        print(top[['NO_MUNICIPIO', 'VL_OBSERVADO_2023',
                   'RENDA_PER_CAPITA_2010', 'IDHM_2010']].sort_values(
            'VL_OBSERVADO_2023', ascending=False).to_string())


def destacar_municipios_por_cluster(df: pd.DataFrame, top_n: int = 5) -> None:
    print("\n" + "=" * 60)
    print("DESTAQUES DE IDEB DENTRO DE CADA CLUSTER")
    print("=" * 60)

    for cid in _clusters_ordenados_por_renda(df):
        sub = df[df['CLUSTER'] == cid].copy()
        sub = sub.sort_values('VL_OBSERVADO_2023', ascending=False)

        melhores = sub[['NO_MUNICIPIO', 'VL_OBSERVADO_2023']].head(top_n)
        piores = sub[['NO_MUNICIPIO', 'VL_OBSERVADO_2023']].tail(top_n).sort_values('VL_OBSERVADO_2023')

        print(f"\nCluster {_nome_cluster(df, cid)} | municípios: {len(sub)}")
        print("  Melhores IDEB:")
        print(melhores.to_string(index=False))
        print("  Piores IDEB:")
        print(piores.to_string(index=False))


def _separar_alto_baixo_por_quantis(cluster_df: pd.DataFrame, q: float = 0.25) -> tuple[pd.DataFrame, pd.DataFrame]:
    limiar_baixo = cluster_df['VL_OBSERVADO_2023'].quantile(q)
    limiar_alto = cluster_df['VL_OBSERVADO_2023'].quantile(1 - q)

    baixo = cluster_df[cluster_df['VL_OBSERVADO_2023'] <= limiar_baixo].copy()
    alto = cluster_df[cluster_df['VL_OBSERVADO_2023'] >= limiar_alto].copy()
    return alto, baixo


def variaveis_relevantes_por_cluster(
    df: pd.DataFrame,
    salvar_arquivo: bool = True,
    q: float = 0.25,
    min_amostras_por_grupo: int = 10,
) -> None:
    print("\n" + "=" * 60)
    print("VARIÁVEIS MAIS RELEVANTES PARA DIFERENCIAR DESTAQUES NO IDEB")
    print("=" * 60)

    for cid in _clusters_ordenados_por_renda(df):
        sub = df[df['CLUSTER'] == cid].copy()
        alto, baixo = _separar_alto_baixo_por_quantis(sub, q=q)
        nome = _nome_cluster(df, cid)

        if len(alto) < min_amostras_por_grupo or len(baixo) < min_amostras_por_grupo:
            print(
                f"\nCluster {nome}: amostra insuficiente para análise robusta "
                f"(alto={len(alto)}, baixo={len(baixo)})."
            )
            continue

        extremos = pd.concat([alto, baixo], axis=0).copy()
        extremos['DESTAQUE'] = (extremos['VL_OBSERVADO_2023'] >= alto['VL_OBSERVADO_2023'].min()).astype(int)

        variaveis_modelo = [
            var for var in VARS_EXPLICATIVAS_IDEB
            if var in extremos.columns and var != 'VL_OBSERVADO_2023'
        ]

        X = extremos[variaveis_modelo]
        y = extremos['DESTAQUE']

        clf = RandomForestClassifier(
            n_estimators=500,
            random_state=42,
            class_weight='balanced',
            min_samples_leaf=3,
        )
        clf.fit(X, y)

        importancias = pd.Series(clf.feature_importances_, index=variaveis_modelo)
        media_alto = alto[variaveis_modelo].mean()
        media_baixo = baixo[variaveis_modelo].mean()
        delta = media_alto - media_baixo

        pvalores = {}
        for var in variaveis_modelo:
            _, p = stats.mannwhitneyu(alto[var], baixo[var], alternative='two-sided')
            pvalores[var] = p

        tabela = pd.DataFrame({
            'variavel': variaveis_modelo,
            'importancia_rf': importancias.values,
            'media_alto': media_alto.values,
            'media_baixo': media_baixo.values,
            'delta_alto_menos_baixo': delta.values,
            'direcao': np.where(delta.values > 0, 'maior_nos_destaques', 'menor_nos_destaques'),
            'p_valor_mw': [pvalores[v] for v in variaveis_modelo],
        }).sort_values('importancia_rf', ascending=False)

        tabela['sig'] = tabela['p_valor_mw'].apply(
            lambda p: '***' if p < 0.01 else '**' if p < 0.05 else '*' if p < 0.1 else ''
        )

        print(
            f"\nCluster {nome} | alto={len(alto)} | baixo={len(baixo)} "
            f"| corte quantil={int(q * 100)}%"
        )
        print("Top 8 variáveis para diferenciar alto vs baixo IDEB no cluster:")
        print(
            tabela[['variavel', 'importancia_rf', 'delta_alto_menos_baixo', 'direcao', 'p_valor_mw', 'sig']]
            .head(8)
            .round(4)
            .to_string(index=False)
        )

        sugestoes = tabela[tabela['p_valor_mw'] < 0.10].head(5)
        print(f"\n  Principais oportunidades de melhoria para municípios do cluster '{nome}'")
        print(f"  (apenas variáveis com diferença estatisticamente significativa, p < 0.10):")
        if sugestoes.empty:
            print("  Nenhuma variável atingiu significância estatística neste cluster.")
        else:
            for _, row in sugestoes.iterrows():
                diff = abs(row['delta_alto_menos_baixo'])
                if row['delta_alto_menos_baixo'] > 0:
                    acao = f"Aumentar de {row['media_baixo']:.1f} para ~{row['media_alto']:.1f}"
                else:
                    acao = f"Reduzir de {row['media_baixo']:.1f} para ~{row['media_alto']:.1f}"
                print(f"  • {row['variavel']} {row['sig']}")
                print(f"    → {acao} (diferença de {diff:.1f}, p={row['p_valor_mw']:.3f})")

        if salvar_arquivo:
            fig, ax = plt.subplots(figsize=(10, 6))
            tabela.sort_values('importancia_rf').plot(
                x='variavel', y='importancia_rf', kind='barh',
                color='darkorange', legend=False, ax=ax
            )
            ax.set_title(f'Cluster {nome} — Relevância de Variáveis (alto vs baixo IDEB)')
            ax.set_xlabel('Importância no Random Forest Classifier')
            plt.tight_layout()
            _renderizar_ou_salvar(
                f"cluster_{_slug_cluster_nome(nome)}_variaveis_relevantes_destaque.png",
                salvar_arquivo=salvar_arquivo,
            )


def classificar_perfil(cluster_df: pd.DataFrame, q: float = 0.25) -> pd.DataFrame:
    cluster_df = cluster_df.copy()
    limiar_baixo = cluster_df['VL_OBSERVADO_2023'].quantile(q)
    limiar_alto = cluster_df['VL_OBSERVADO_2023'].quantile(1 - q)
    cluster_df['PERFIL'] = 'médio'
    cluster_df.loc[cluster_df['VL_OBSERVADO_2023'] >= limiar_alto, 'PERFIL'] = 'alto'
    cluster_df.loc[cluster_df['VL_OBSERVADO_2023'] <= limiar_baixo, 'PERFIL'] = 'baixo'
    return cluster_df


def comparar_perfis(df: pd.DataFrame, q: float = 0.25) -> None:
    vars_analise = ['VL_OBSERVADO_2023'] + [
        var for var in VARS_EXPLICATIVAS_IDEB if var in df.columns
    ]

    for cid in _clusters_analise_intragrupo(df):
        nome = _nome_cluster(df, cid)
        sub = classificar_perfil(df[df['CLUSTER'] == cid], q=q)
        print(f"\nDistribuição por perfil — Cluster {nome} (quantil {int(q * 100)}%):")
        print(sub['PERFIL'].value_counts())
        print(f"\nPerfil médio por grupo (Cluster {nome}):")
        print(sub.groupby('PERFIL')[vars_analise].mean().round(2).T.to_string())


def mann_whitney(df: pd.DataFrame, q: float = 0.25) -> None:
    vars_analise = [var for var in VARS_EXPLICATIVAS_IDEB if var in df.columns]

    for cid in _clusters_analise_intragrupo(df):
        nome = _nome_cluster(df, cid)
        sub = classificar_perfil(df[df['CLUSTER'] == cid], q=q)
        alto = sub[sub['PERFIL'] == 'alto']
        baixo = sub[sub['PERFIL'] == 'baixo']
        print(f"\nTestes Mann-Whitney (alto vs baixo, quantil {int(q * 100)}%) — Cluster {nome}:")
        if len(alto) < 5 or len(baixo) < 5:
            print(f"  Amostra insuficiente para teste robusto (alto={len(alto)}, baixo={len(baixo)}).")
            continue

        for var in vars_analise:
            _, p = stats.mannwhitneyu(alto[var], baixo[var], alternative='two-sided')
            sig = '***' if p < 0.01 else '**' if p < 0.05 else '*' if p < 0.1 else ''
            print(f"  {var:<45} p={p:.3f} {sig}")


def random_forest(df: pd.DataFrame, salvar_arquivo: bool = True) -> None:
    print("\n" + "=" * 60)
    print("RANDOM FOREST — Importância de variáveis")
    print("=" * 60)

    df_rf = df[df['CLUSTER'].isin(_clusters_analise_intragrupo(df))].copy()
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
    _renderizar_ou_salvar("random_forest_importancia.png", salvar_arquivo=salvar_arquivo)

def distribuicao_ideb(df: pd.DataFrame, salvar_arquivo: bool = True) -> None:
    ideb = df['VL_OBSERVADO_2023'].dropna()
    media = ideb.mean()
    mediana = ideb.median()
    std = ideb.std()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(ideb, bins=20, color='steelblue', edgecolor='white', alpha=0.85)
    ax.axvline(media, color='red', linestyle='--', linewidth=1.5, label=f'Média: {media:.2f}')
    ax.axvline(mediana, color='orange', linestyle='--', linewidth=1.5, label=f'Mediana: {mediana:.2f}')
    ax.axvspan(media - std, media + std, alpha=0.1, color='red', label=f'±1 desvio-padrão ({std:.2f})')
    ax.set_title('Distribuição do IDEB 2023 — Municípios Maranhenses (Rede Municipal)', fontsize=13, fontweight='bold')
    ax.set_xlabel('IDEB (Anos Iniciais do Ensino Fundamental)')
    ax.set_ylabel('Número de municípios')
    ax.legend()
    plt.tight_layout()
    _renderizar_ou_salvar("distribuicao_ideb.png", salvar_arquivo=salvar_arquivo)

    print(f"\nDistribuição do IDEB 2023:")
    print(f"  Municípios com dado: {len(ideb)}")
    print(f"  Média:   {media:.2f}")
    print(f"  Mediana: {mediana:.2f}")
    print(f"  Desvio-padrão: {std:.2f}")
    print(f"  Min: {ideb.min():.2f}  |  Max: {ideb.max():.2f}")

# ── PIPELINE PRINCIPAL ────────────────────────────────────────────────────────

def main(salvar_graficos: bool = True) -> None:
    df = carregar_dados()
    distribuicao_ideb(df, salvar_arquivo=salvar_graficos)
    X_scaled, _ = normalizar(df)

    k_range = range(2, 11)
    silhouettes = elbow_silhouette(X_scaled, k_range, salvar_arquivo=salvar_graficos)
    visualizar_pca(X_scaled, silhouettes, k_range, salvar_arquivo=salvar_graficos)

    df = clusterizar(df, X_scaled, k=CLUSTER_K)
    relevancia_variaveis_cluster(X_scaled, k=CLUSTER_K, n_bootstrap=25)
    destacar_municipios_por_cluster(df, top_n=5)
    variaveis_relevantes_por_cluster(df, salvar_arquivo=salvar_graficos, q=0.25)
    outliers_positivos(df)
    comparar_perfis(df)
    mann_whitney(df)
    random_forest(df, salvar_arquivo=salvar_graficos)


if __name__ == "__main__":
    main()