import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import locale
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
# Dados tabulares por trás dos gráficos (permitem redesenhar as figuras).
DADOS_GRAFICOS_DIR = PROJECT_ROOT / "reports" / "dados_graficos"

VARS_CLUSTER = [
    'RENDA_PER_CAPITA_2022',
    'PCT_POBREZA_EXTREMA_2022',
]

CLUSTER_K = 3

VARS_EXPLICATIVAS_IDEB = [
    'RENDA_PER_CAPITA_2022',
    'PCT_POBREZA_EXTREMA_2022',
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
    'VL_OBSERVADO_2025',
    'RENDA_PER_CAPITA_2022',
    'PCT_POBREZA_EXTREMA_2022',
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

ROTULOS_VARIAVEIS = {
    'RENDA_PER_CAPITA_2022': 'Renda per capita',
    'PCT_POBREZA_EXTREMA_2022': 'Pobreza extrema',
    'PCT_ESCOLAS_COM_INTERNET': '% escolas com internet',
    'PCT_ESCOLAS_COM_BIBLIOTECA_LEITURA': '% escolas com biblioteca/sala de leitura',
    'PCT_ESCOLAS_COM_LAB_INFORMATICA': '% escolas com laboratório de informática',
    'PCT_ESCOLAS_COM_QUADRA': '% escolas com quadra esportiva',
    'PCT_ESCOLAS_COM_AGUA_ADEQUADA': '% escolas com água adequada',
    'PCT_ESCOLAS_COM_ESGOTO_ADEQUADO': '% escolas com esgoto adequado',
    'PCT_DOC_SUPERIOR_COMPLETO': '% docentes com ensino superior',
    'PCT_DOC_LICENCIATURA_TOTAL': '% docentes com licenciatura',
    'MEDIA_ALUNOS_POR_TURMA_BAS': 'Média de alunos/turma (educação básica)',
    'MEDIA_ALUNOS_POR_TURMA_FUND': 'Média de alunos/turma (ensino fundamental)',
    'MEDIA_ALUNOS_POR_TURMA_MED': 'Média de alunos/turma (ensino médio)',
    'PCT_MAT_15_ANOS_OU_MAIS_PROXY_DISTSERIE': 'Proxy de distorção idade-série',
    'PCT_TURMAS_CORRFLUXO_FUND_AF': '% turmas de correção de fluxo (anos finais)',
}


# ── FUNÇÕES ───────────────────────────────────────────────────────────────────

def carregar_dados() -> pd.DataFrame:
    df = pd.read_csv(TRUSTED_DIR / "indicadores_municipais_ma.csv", sep=";")
    # Municípios sem IDEB divulgado (Nova Iorque em 2025) ficam fora de toda a análise.
    df = df.dropna(subset=['VL_OBSERVADO_2025']).reset_index(drop=True)
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


# Gráficos no padrão brasileiro (vírgula decimal nos eixos), como no artigo.
try:
    locale.setlocale(locale.LC_NUMERIC, 'pt_BR.UTF-8')
    plt.rcParams['axes.formatter.use_locale'] = True
except locale.Error:
    pass


def _br(valor: float, casas: int = 2) -> str:
    """Número com vírgula decimal, para rótulos e legendas dos gráficos."""
    return f"{valor:.{casas}f}".replace('.', ',')


def _renderizar_ou_salvar(nome_arquivo: str, salvar_arquivo: bool = True) -> None:
    if salvar_arquivo:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        plt.savefig(FIGURES_DIR / nome_arquivo, dpi=150, bbox_inches='tight')
    else:
        plt.show()
    plt.close()


def _exportar_dados_grafico(nome: str, dados: pd.DataFrame) -> None:
    DADOS_GRAFICOS_DIR.mkdir(parents=True, exist_ok=True)
    dados.to_csv(DADOS_GRAFICOS_DIR / f"{nome}.csv", sep=";", index=False)


def elbow_silhouette(X_scaled, k_range: range, salvar_arquivo: bool = True) -> list:
    inertias, silhouettes = [], []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        inertias.append(km.inertia_)
        silhouettes.append(silhouette_score(X_scaled, labels))

    best_k = k_range[silhouettes.index(max(silhouettes))]
    _exportar_dados_grafico("elbow_silhouette", pd.DataFrame(
        {"k": list(k_range), "inercia": inertias, "silhouette": silhouettes}))

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].plot(k_range, inertias, marker='o', color='steelblue', linewidth=2)
    axes[0].set_title('Inércia (método do cotovelo)')
    axes[0].set_xlabel('Número de clusters (k)')
    axes[0].set_ylabel('Inércia')

    axes[1].plot(k_range, silhouettes, marker='o', color='darkorange', linewidth=2)
    axes[1].set_title('Silhouette Score')
    axes[1].set_xlabel('Número de clusters (k)')
    axes[1].set_ylabel('Silhouette Score médio')
    axes[1].axvline(best_k, color='red', linestyle='--',
                    label=f'Melhor k = {best_k} ({_br(max(silhouettes), 3)})')
    axes[1].legend()

    plt.tight_layout()
    _renderizar_ou_salvar("elbow_silhouette.png", salvar_arquivo=salvar_arquivo)

    print(f"\nMelhor k pelo Silhouette: {best_k} (score: {max(silhouettes):.3f})")
    print("\nTodos os scores:")
    for k, s in zip(k_range, silhouettes):
        print(f"  k={k}: {s:.3f}")

    return silhouettes


def visualizar_pca(df: pd.DataFrame, X_scaled, silhouettes: list, k_range: range, salvar_arquivo: bool = True) -> None:
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    variancia = pca.explained_variance_ratio_

    km = KMeans(n_clusters=CLUSTER_K, random_state=42, n_init=10)
    nomeado = nomear_clusters(df.assign(CLUSTER=km.fit_predict(X_scaled)))
    projecao = pd.DataFrame({
        "municipio": nomeado['NO_MUNICIPIO'],
        "grupo": nomeado['CLUSTER_NOME'],
        "pc1": X_pca[:, 0],
        "pc2": X_pca[:, 1],
    })
    _exportar_dados_grafico("pca_clusters", projecao)

    fig, ax = plt.subplots(figsize=(7, 5))
    for grupo, cor in zip(['vulneráveis', 'intermediários', 'alta renda'], ['tab:red', 'tab:blue', 'tab:green']):
        sub = projecao[projecao['grupo'] == grupo]
        ax.scatter(sub['pc1'], sub['pc2'], color=cor, alpha=0.6, s=40, label=grupo)
    ax.set_title(f'k = {CLUSTER_K} | silhouette = {_br(silhouettes[CLUSTER_K - 2], 3)}')
    ax.set_xlabel(f'PC1 ({_br(variancia[0]*100, 1)}% da variância)')
    ax.set_ylabel(f'PC2 ({_br(variancia[1]*100, 1)}% da variância)')
    ax.legend(title='Grupo')

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
        print(sub[['NO_MUNICIPIO', 'RENDA_PER_CAPITA_2022', 'VL_OBSERVADO_2025']]
              .sort_values('RENDA_PER_CAPITA_2022', ascending=False)
              .to_string(index=False))

    for nome in [n for n in df['CLUSTER_NOME'].dropna().unique() if n != 'alta renda']:
        sub = df[df['CLUSTER_NOME'] == nome]['VL_OBSERVADO_2025']
        print(f"\nCluster {nome} ({len(sub)} municípios):")
        print(f"  IDEB médio: {sub.mean():.2f}  |  min: {sub.min():.2f}  |  max: {sub.max():.2f}")

    return df


def nomear_clusters(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    medias_renda = df.groupby('CLUSTER')['RENDA_PER_CAPITA_2022'].mean().sort_values()
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
        df.groupby(['CLUSTER', 'CLUSTER_NOME'])['RENDA_PER_CAPITA_2022']
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
        limiar = sub['VL_OBSERVADO_2025'].mean() + sub['VL_OBSERVADO_2025'].std()
        top = sub[sub['VL_OBSERVADO_2025'] >= limiar]
        print(f"\nOutliers positivos Cluster {_nome_cluster(df, cid)} (IDEB >= {limiar:.2f}):")
        print(top[['NO_MUNICIPIO', 'VL_OBSERVADO_2025',
                   'RENDA_PER_CAPITA_2022', 'PCT_POBREZA_EXTREMA_2022']].sort_values(
            'VL_OBSERVADO_2025', ascending=False).to_string())


def destacar_municipios_por_cluster(df: pd.DataFrame, top_n: int = 5) -> None:
    print("\n" + "=" * 60)
    print("DESTAQUES DE IDEB DENTRO DE CADA CLUSTER")
    print("=" * 60)

    for cid in _clusters_ordenados_por_renda(df):
        sub = df[df['CLUSTER'] == cid].copy()
        sub = sub.sort_values('VL_OBSERVADO_2025', ascending=False)

        melhores = sub[['NO_MUNICIPIO', 'VL_OBSERVADO_2025']].head(top_n)
        piores = sub[['NO_MUNICIPIO', 'VL_OBSERVADO_2025']].tail(top_n).sort_values('VL_OBSERVADO_2025')

        print(f"\nCluster {_nome_cluster(df, cid)} | municípios: {len(sub)}")
        print("  Melhores IDEB:")
        print(melhores.to_string(index=False))
        print("  Piores IDEB:")
        print(piores.to_string(index=False))


def _separar_alto_baixo_por_quantis(cluster_df: pd.DataFrame, q: float = 0.25) -> tuple[pd.DataFrame, pd.DataFrame]:
    limiar_baixo = cluster_df['VL_OBSERVADO_2025'].quantile(q)
    limiar_alto = cluster_df['VL_OBSERVADO_2025'].quantile(1 - q)

    baixo = cluster_df[cluster_df['VL_OBSERVADO_2025'] <= limiar_baixo].copy()
    alto = cluster_df[cluster_df['VL_OBSERVADO_2025'] >= limiar_alto].copy()
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
        extremos['DESTAQUE'] = (extremos['VL_OBSERVADO_2025'] >= alto['VL_OBSERVADO_2025'].min()).astype(int)

        variaveis_modelo = [
            var for var in VARS_EXPLICATIVAS_IDEB
            if var in extremos.columns and var != 'VL_OBSERVADO_2025'
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

        sugestoes = tabela[tabela["p_valor_mw"] < 0.10]
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
            grafico = tabela.sort_values('importancia_rf').assign(
                rotulo=lambda t: t['variavel'].map(ROTULOS_VARIAVEIS).fillna(t['variavel'])
            )
            grafico.plot(
                x='rotulo', y='importancia_rf', kind='barh',
                color='darkorange', legend=False, ax=ax
            )
            ax.set_ylabel('')
            ax.set_xlabel('Importância no Random Forest Classifier')
            plt.tight_layout()
            _renderizar_ou_salvar(
                f"cluster_{_slug_cluster_nome(nome)}_variaveis_relevantes_destaque.png",
                salvar_arquivo=salvar_arquivo,
            )


def _benjamini_hochberg(pvalores) -> np.ndarray:
    """Valores q (taxa de falsas descobertas) de Benjamini e Hochberg (1995)."""
    p = np.asarray(pvalores, dtype=float)
    n = len(p)
    ordem = np.argsort(p)
    ajustado = p[ordem] * n / np.arange(1, n + 1)
    ajustado = np.minimum.accumulate(ajustado[::-1])[::-1]
    q = np.empty(n)
    q[ordem] = np.minimum(ajustado, 1)
    return q


def comparar_extremos_por_cluster(
    df: pd.DataFrame,
    q: float = 0.25,
    min_amostras_por_grupo: int = 10,
) -> dict:
    """Estágio 2 do artigo: compara os quartis superior e inferior de IDEB em
    cada cluster (Mann-Whitney bicaudal, delta de Cliff e valor q de
    Benjamini-Hochberg) e, como robustez, correlaciona cada variável com o
    IDEB em todos os municípios do cluster (Spearman)."""
    print("\n" + "=" * 60)
    print("ESTÁGIO 2: ALTO x BAIXO IDEB DENTRO DE CADA CLUSTER")
    print("=" * 60)

    resultados = {}
    for cid in _clusters_ordenados_por_renda(df):
        sub = df[df['CLUSTER'] == cid].dropna(subset=['VL_OBSERVADO_2025'])
        alto, baixo = _separar_alto_baixo_por_quantis(sub, q=q)
        nome = _nome_cluster(df, cid)
        if len(alto) < min_amostras_por_grupo or len(baixo) < min_amostras_por_grupo:
            continue

        variaveis = [v for v in VARS_EXPLICATIVAS_IDEB if v in sub.columns]
        linhas = []
        for var in variaveis:
            u, p = stats.mannwhitneyu(alto[var], baixo[var], alternative='two-sided')
            rho, p_rho = stats.spearmanr(sub[var], sub['VL_OBSERVADO_2025'])
            linhas.append({
                'variavel': var,
                'media_alto': alto[var].mean(),
                'media_baixo': baixo[var].mean(),
                'delta': alto[var].mean() - baixo[var].mean(),
                'cliff': 2 * u / (len(alto) * len(baixo)) - 1,
                'p_mw': p,
                'rho': rho,
                'p_rho': p_rho,
            })
        tabela = pd.DataFrame(linhas)
        tabela['q_mw'] = _benjamini_hochberg(tabela['p_mw'])
        tabela['q_rho'] = _benjamini_hochberg(tabela['p_rho'])
        tabela = tabela.sort_values('p_mw')
        resultados[nome] = tabela

        print(f"\nCluster {nome} | n={len(sub)} | alto={len(alto)} | baixo={len(baixo)}")
        print(tabela.round(3).to_string(index=False))
    return resultados


def sensibilidade_rede_municipal(df: pd.DataFrame, q: float = 0.25) -> None:
    """Refaz a comparação da formação docente com a medida restrita à rede
    municipal (microdados, educação básica), já que a Tabela 2.29 da Sinopse
    inclui todas as redes do município, e o IDEB analisado é só o municipal."""
    print("\n" + "=" * 60)
    print("SENSIBILIDADE: FORMAÇÃO DOCENTE SÓ NA REDE MUNICIPAL")
    print("=" * 60)
    print("\nParticipação da rede municipal nos docentes EFAI do município (%):")
    print(df.groupby('CLUSTER_NOME')['PCT_DOC_EFAI_REDE_MUN'].describe().round(1).to_string())

    for cid in _clusters_ordenados_por_renda(df):
        sub = df[df['CLUSTER'] == cid].dropna(subset=['VL_OBSERVADO_2025'])
        alto, baixo = _separar_alto_baixo_por_quantis(sub, q=q)
        if len(alto) < 10 or len(baixo) < 10:
            continue
        for var in ['PCT_DOC_SUPERIOR_REDE_MUN', 'PCT_DOC_LICENCIATURA_REDE_MUN']:
            u, p = stats.mannwhitneyu(alto[var], baixo[var], alternative='two-sided')
            rho, p_rho = stats.spearmanr(sub[var], sub['VL_OBSERVADO_2025'])
            print(
                f"Cluster {_nome_cluster(df, cid)} | {var} | alto={alto[var].mean():.1f} "
                f"baixo={baixo[var].mean():.1f} | p={p:.3f} | cliff={2 * u / (len(alto) * len(baixo)) - 1:.2f} "
                f"| rho={rho:.2f} (p={p_rho:.3f})"
            )


def validacao_preditiva(df: pd.DataFrame, q: float = 0.25, n_repeticoes: int = 20) -> None:
    """Poder preditivo conjunto das variáveis, em validação cruzada (5 partes,
    repetida): Random Forest para separar alto x baixo IDEB em cada cluster
    (AUC) e regressão ridge para o IDEB contínuo, no estado e nos clusters (R²)."""
    from sklearn.linear_model import RidgeCV
    from sklearn.model_selection import (
        RepeatedKFold, RepeatedStratifiedKFold, cross_val_score,
    )
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    print("\n" + "=" * 60)
    print("VALIDAÇÃO PREDITIVA (VALIDAÇÃO CRUZADA)")
    print("=" * 60)

    base = df.dropna(subset=['VL_OBSERVADO_2025'])
    variaveis = [v for v in VARS_EXPLICATIVAS_IDEB if v in base.columns]
    ridge = make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-2, 3, 20)))
    cv_reg = RepeatedKFold(n_splits=5, n_repeats=n_repeticoes, random_state=42)

    r2 = cross_val_score(ridge, base[variaveis], base['VL_OBSERVADO_2025'], cv=cv_reg, scoring='r2')
    print(f"\nEstado (n={len(base)}) | ridge R² = {r2.mean():.3f} ± {r2.std():.3f}")

    for cid in _clusters_ordenados_por_renda(base):
        sub = base[base['CLUSTER'] == cid]
        alto, baixo = _separar_alto_baixo_por_quantis(sub, q=q)
        if len(alto) < 10 or len(baixo) < 10:
            continue
        extremos = pd.concat([alto, baixo])
        y = (extremos['VL_OBSERVADO_2025'] >= alto['VL_OBSERVADO_2025'].min()).astype(int)
        clf = RandomForestClassifier(
            n_estimators=500, random_state=42, class_weight='balanced', min_samples_leaf=3,
        )
        cv_clf = RepeatedStratifiedKFold(n_splits=5, n_repeats=n_repeticoes, random_state=42)
        auc = cross_val_score(clf, extremos[variaveis], y, cv=cv_clf, scoring='roc_auc')
        r2 = cross_val_score(ridge, sub[variaveis], sub['VL_OBSERVADO_2025'], cv=cv_reg, scoring='r2')
        print(
            f"Cluster {_nome_cluster(base, cid)} (n={len(sub)}; extremos={len(extremos)}) | "
            f"RF AUC = {auc.mean():.3f} ± {auc.std():.3f} | ridge R² = {r2.mean():.3f} ± {r2.std():.3f}"
        )


def classificar_perfil(cluster_df: pd.DataFrame, q: float = 0.25) -> pd.DataFrame:
    cluster_df = cluster_df.copy()
    limiar_baixo = cluster_df['VL_OBSERVADO_2025'].quantile(q)
    limiar_alto = cluster_df['VL_OBSERVADO_2025'].quantile(1 - q)
    cluster_df['PERFIL'] = 'médio'
    cluster_df.loc[cluster_df['VL_OBSERVADO_2025'] >= limiar_alto, 'PERFIL'] = 'alto'
    cluster_df.loc[cluster_df['VL_OBSERVADO_2025'] <= limiar_baixo, 'PERFIL'] = 'baixo'
    return cluster_df


def comparar_perfis(df: pd.DataFrame, q: float = 0.25) -> None:
    vars_analise = ['VL_OBSERVADO_2025'] + [
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
    df_rf = df_rf.dropna(subset=['VL_OBSERVADO_2025'])
    X_rf = df_rf[VARS_RF]
    y_rf = df_rf['VL_OBSERVADO_2025']

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

def distribuicao_quartis_cluster(
    df: pd.DataFrame,
    cluster_nome: str = 'vulneráveis',
    q: float = 0.25,
    salvar_arquivo: bool = True,
) -> None:
    sub = df[df['CLUSTER_NOME'] == cluster_nome].copy()
    sub = classificar_perfil(sub, q=q)

    ideb_all = sub['VL_OBSERVADO_2025']
    q_baixo = ideb_all.quantile(q)
    q_alto = ideb_all.quantile(1 - q)

    cores = {'baixo': '#e74c3c', 'médio': '#95a5a6', 'alto': '#27ae60'}
    xmin = ideb_all.min() - 0.15
    xmax = ideb_all.max() + 0.15
    bins = np.linspace(xmin, xmax, 22)

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.axvspan(xmin, q_baixo, alpha=0.10, color=cores['baixo'])
    ax.axvspan(q_baixo, q_alto, alpha=0.06, color=cores['médio'])
    ax.axvspan(q_alto, xmax, alpha=0.10, color=cores['alto'])

    for perfil in ['baixo', 'médio', 'alto']:
        grupo = sub[sub['PERFIL'] == perfil]['VL_OBSERVADO_2025']
        ax.hist(
            grupo, bins=bins, alpha=0.80,
            color=cores[perfil], edgecolor='white', linewidth=0.5,
            label=f'{perfil.capitalize()} IDEB (n={len(grupo)})',
        )

    ax.axvline(q_baixo, color=cores['baixo'], linestyle='--', linewidth=2,
               label=f'Q{int(q * 100)} = {q_baixo:.2f}')
    ax.axvline(q_alto, color=cores['alto'], linestyle='--', linewidth=2,
               label=f'Q{int((1 - q) * 100)} = {q_alto:.2f}')

    ax.set_xlim(xmin, xmax)
    ax.set_title(
        f'Distribuição do IDEB — Cluster {cluster_nome} (n={len(sub)})\n'
        f'Grupos alto e baixo definidos pelos quartis Q{int(q * 100)} e Q{int((1 - q) * 100)}',
        fontsize=12, fontweight='bold',
    )
    ax.set_xlabel('IDEB 2025 (Anos Iniciais do Ensino Fundamental)')
    ax.set_ylabel('Número de municípios')
    ax.legend(loc='upper right', fontsize=9)
    plt.tight_layout()
    _renderizar_ou_salvar(
        f'distribuicao_quartis_{_slug_cluster_nome(cluster_nome)}.png',
        salvar_arquivo=salvar_arquivo,
    )

    print(f'\nDistribuição por perfil — Cluster {cluster_nome}:')
    for perfil in ['alto', 'médio', 'baixo']:
        grupo = sub[sub['PERFIL'] == perfil]['VL_OBSERVADO_2025']
        print(
            f'  {perfil.capitalize()}: n={len(grupo)}'
            f' | média={grupo.mean():.2f}'
            f' | [{grupo.min():.2f}–{grupo.max():.2f}]'
        )


def distribuicao_ideb(df: pd.DataFrame, salvar_arquivo: bool = True) -> None:
    ideb = df['VL_OBSERVADO_2025'].dropna()
    media = ideb.mean()
    mediana = ideb.median()
    std = ideb.std()

    contagem, limites = np.histogram(ideb, bins=20)
    _exportar_dados_grafico("distribuicao_ideb", pd.DataFrame(
        {"inicio": limites[:-1], "fim": limites[1:], "municipios": contagem}))

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(ideb, bins=20, color='steelblue', edgecolor='white', alpha=0.85)
    ax.axvline(media, color='red', linestyle='--', linewidth=1.5, label=f'Média: {_br(media)}')
    ax.axvline(mediana, color='orange', linestyle='--', linewidth=1.5, label=f'Mediana: {_br(mediana)}')
    ax.axvspan(media - std, media + std, alpha=0.1, color='red', label=f'±1 desvio-padrão ({_br(std)})')
    ax.set_xlabel('IDEB (Anos Iniciais do Ensino Fundamental)')
    ax.set_ylabel('Número de municípios')
    ax.legend()
    plt.tight_layout()
    _renderizar_ou_salvar("distribuicao_ideb.png", salvar_arquivo=salvar_arquivo)

    print(f"\nDistribuição do IDEB 2025:")
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
    visualizar_pca(df, X_scaled, silhouettes, k_range, salvar_arquivo=salvar_graficos)

    df = clusterizar(df, X_scaled, k=CLUSTER_K)
    relevancia_variaveis_cluster(X_scaled, k=CLUSTER_K, n_bootstrap=25)
    destacar_municipios_por_cluster(df, top_n=5)
    variaveis_relevantes_por_cluster(df, salvar_arquivo=salvar_graficos, q=0.25)
    comparar_extremos_por_cluster(df, q=0.25)
    sensibilidade_rede_municipal(df, q=0.25)
    validacao_preditiva(df, q=0.25)
    distribuicao_quartis_cluster(df, cluster_nome='vulneráveis', q=0.25, salvar_arquivo=salvar_graficos)
    outliers_positivos(df)
    comparar_perfis(df)
    mann_whitney(df)
    random_forest(df, salvar_arquivo=salvar_graficos)


if __name__ == "__main__":
    main()