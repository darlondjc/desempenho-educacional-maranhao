# Seminário do Pré-Projeto

## Título sugerido
Padrões de Desempenho Educacional nos Municípios Maranhenses: Conceitos de Python, Classes e Métodos Aplicados

## Objetivo central (enunciado da disciplina)
Cada discente deverá apresentar os conceitos de Python mobilizados em sua pesquisa, detalhando a implementação de classes e métodos específicos que compõem a lógica do seu pré-projeto.

## Tempo sugerido
15 a 20 minutos

## Estrutura do seminário (12 slides)

### 1) Abertura e problema de pesquisa
- Tema: desigualdades no desempenho educacional municipal no Maranhão.
- Pergunta norteadora: quais fatores estruturais e escolares se associam aos diferentes níveis de IDEB?
- Recorte temporal e geográfico: municípios maranhenses, com foco em 2023 (IDEB/Censo) e controles de 2010 (IBGE/IDHM).

### 2) Arquitetura do projeto em Python
- Camadas de dados: base -> raw -> trusted -> reports.
- Módulos principais:
  - ingestão: src/ingest.py
  - transformação: src/transform.py
  - análise/modelagem: src/analytics.py
  - utilitários: src/util.py
- Paradigma predominante: programação funcional orientada a pipeline.

### 3) Conceitos de Python mobilizados
- Tipagem com type hints (ex.: -> pd.DataFrame, -> None).
- Manipulação de caminhos com pathlib.Path.
- Tratamento de exceções com FileNotFoundError.
- Uso de funções auxiliares para reuso e clareza (safe_divide, normalize_municipio_code, ensure_columns).
- Encadeamento de métodos para transformação tabular com pandas.

### 4) Classes usadas na ingestão (com foco em implementação)
- Classe Path (módulo pathlib): composição segura de caminhos com operador / e métodos como exists() e mkdir().
- Classe DataFrame (pandas): leitura e estruturação de bases via read_csv(), read_excel(), groupby(), agg(), assign(), merge().
- Classe Series (pandas): vetorização de cálculos, conversões e limpeza com replace(), astype(), str methods.

Ponto de defesa: embora não existam classes autorais no projeto atual, a lógica é construída sobre classes robustas do ecossistema científico Python.

### 5) Métodos-chave da ingestão e lógica implementada
- build_indicadores_municipais_ma_censo_escolar_2023:
  - filtra Maranhão e rede municipal;
  - cria indicadores derivados (biblioteca/leitura, água e esgoto adequados);
  - agrega por município;
  - calcula percentuais e proxies educacionais.
- build_indicadores_municipais_ma_censo_docentes_2023:
  - integra Sinopse de docentes;
  - recalcula percentuais com numerador e denominador consistentes.
- safe_divide:
  - evita divisão por zero substituindo denominador zero por NA.

### 6) Transformação: limpeza e integração dos dados
- Funções de transformação por fonte:
  - transform_indicadores_municipais_ma_ideb_2023
  - transform_indicadores_municipais_ma_censo_2023
  - transform_indicadores_municipais_ma_ibge_2010
  - transform_indicadores_municipais_ma_idhm_2010
- Métodos críticos:
  - dropna, rename, to_numeric, astype, str.replace, merge.
- Decisão metodológica: padronização de NO_MUNICIPIO para garantir junção entre bases heterogêneas.

### 7) Classes e métodos na etapa analítica
- Classe RobustScaler (scikit-learn): padronização robusta para reduzir impacto de outliers.
- Classe KMeans: segmentação de municípios por perfil estrutural.
  - métodos fit_predict e atributos de qualidade (inércia via modelo; silhouette com função externa).
- Classe PCA: redução de dimensionalidade para visualização dos clusters.
  - método fit_transform.
- Classe RandomForestRegressor: estima relevância de variáveis na explicação do IDEB.
  - métodos fit, score e atributo feature_importances_.

### 8) Testes estatísticos e interpretação
- Método mannwhitneyu (scipy.stats): comparação não paramétrica entre perfis alto e baixo dentro de clusters.
- Justificativa: variáveis com distribuição potencialmente não normal e amostras de tamanho moderado.

### 9) Encadeamento lógico do pipeline
- Entrada: microdados e indicadores oficiais.
- Processo:
  - ingestão e engenharia de indicadores;
  - transformação e consolidação em base trusted;
  - clusterização, comparação de perfis e importância de variáveis.
- Saída:
  - base final consolidada (indicadores_municipais_ma.csv);
  - figuras para interpretação (elbow/silhouette, PCA, importância de variáveis).

### 10) Evidências de maturidade técnica em Python
- Modularização por responsabilidade (ingest, transform, analytics, util).
- Reuso de funções auxiliares.
- Vetorização com pandas (eficiência e legibilidade).
- Reprodutibilidade com dependências declaradas no pyproject.toml.

### 11) Limitação atual e proposta de evolução (classe autoral)
- Limitação: ausência de classes próprias para orquestração do fluxo.
- Evolução recomendada:
  - classe PipelineEducacional
  - métodos: run_ingest(), run_transform(), run_analytics(), run_all().
- Ganho esperado: melhor encapsulamento, testabilidade e clareza de execução por etapa.

### 12) Conclusão
- O projeto mobiliza conceitos centrais de Python científico aplicados a problema social relevante.
- As classes utilizadas (pandas, sklearn, pathlib, scipy) sustentam toda a lógica metodológica.
- A evolução natural do código é incorporar classes autorais para orquestração sem perder a robustez funcional já consolidada.

## Roteiro de fala (resumo por bloco)

### Bloco A: Contexto (2-3 min)
Este projeto investiga padrões de desempenho educacional nos municípios maranhenses, com base em indicadores de infraestrutura escolar, contexto socioeconômico e resultados do IDEB. O foco é transformar bases públicas heterogêneas em evidências analíticas comparáveis.

### Bloco B: Conceitos Python e implementação (6-8 min)
A implementação é modular e orientada a pipeline. Na ingestão, usamos pathlib.Path para portabilidade de arquivos e pandas.DataFrame para leitura e agregação. Na transformação, aplicamos limpeza sistemática com métodos vetorizados e integração entre fontes. Na análise, classes do scikit-learn como RobustScaler, KMeans, PCA e RandomForestRegressor estruturam clusterização, visualização e explicação de variáveis.

### Bloco C: Resultados metodológicos (4-5 min)
A lógica analítica combina segmentação de municípios, análise de outliers positivos e comparação estatística de perfis internos. Assim, o projeto não apenas descreve desigualdades, mas identifica fatores com maior potencial explicativo para desempenho educacional.

### Bloco D: Fechamento (2-3 min)
Concluo que a base técnica em Python está consistente para pesquisa aplicada e tomada de decisão pública. Como evolução, proponho encapsular o pipeline em classe autoral para elevar organização e facilitar testes de regressão.

## Perguntas prováveis da banca e respostas curtas

1. Onde estão as classes do seu projeto?
- Atualmente, a maior parte da lógica está em funções, mas o projeto usa classes essenciais do ecossistema Python (DataFrame, Path, KMeans, PCA, RandomForestRegressor). A classe autoral é a próxima evolução planejada.

2. Por que usar RobustScaler e não StandardScaler?
- Porque há municípios com valores extremos; o RobustScaler usa mediana e intervalo interquartílico, reduzindo sensibilidade a outliers.

3. Como você evita erros em cálculos percentuais?
- Com safe_divide, substituindo denominadores zero por NA antes da divisão.

4. Como garante consistência no merge entre bases?
- Padronizando NO_MUNICIPIO (strip e upper) e harmonizando tipos/códigos municipais.

5. Qual a principal contribuição técnica?
- Integração reprodutível de múltiplas bases públicas com pipeline analítico orientado a evidência para diagnóstico municipal.

## Checklist de preparação final
- Revisar nomes das variáveis explicativas e seus significados substantivos.
- Validar se todos os gráficos em reports/figures refletem a versão mais recente da base trusted.
- Ensaiar a fala com cronômetro para fechar em 15-20 minutos.
- Levar uma versão curta (10 min) e uma estendida (20 min).

## Exemplos de código para mostrar no seminário

### Exemplo 1: função auxiliar para divisão segura (slide 5)
Objetivo didático: mostrar tratamento de erro numérico sem interromper o pipeline.

```python
def safe_divide(numerator: pd.Series, denominator: pd.Series, factor: float = 1.0) -> pd.Series:
  denominator = denominator.replace(0, pd.NA)
  return (numerator / denominator) * factor
```

Ponto para falar: a função evita divisão por zero e retorna NA quando o denominador é inválido.

### Exemplo 2: normalização de código de município (slide 5)
Objetivo didático: evidenciar padronização de chaves para merge.

```python
def normalize_municipio_code(series: pd.Series) -> pd.Series:
  return pd.to_numeric(series, errors="coerce").astype("Int64").astype("string")
```

Ponto para falar: sem padronização de tipo, joins entre bases públicas podem falhar silenciosamente.

### Exemplo 3: agregação municipal com groupby e agg (slide 5)
Objetivo didático: mostrar transformação vetorizada com DataFrame.

```python
indicadores = (
  censo.groupby("CO_MUNICIPIO", as_index=False)
  .agg(
    NO_MUNICIPIO=("NO_MUNICIPIO", "first"),
    QT_ESCOLAS=("CO_ENTIDADE", "nunique"),
    PCT_ESCOLAS_COM_INTERNET=("IN_INTERNET", "mean"),
    QT_MAT_BAS=("QT_MAT_BAS", "sum"),
    QT_TUR_BAS=("QT_TUR_BAS", "sum"),
  )
  .assign(
    PCT_ESCOLAS_COM_INTERNET=lambda x: x["PCT_ESCOLAS_COM_INTERNET"] * 100,
    MEDIA_ALUNOS_POR_TURMA_BAS=lambda x: x["QT_MAT_BAS"] / x["QT_TUR_BAS"],
  )
)
```

Ponto para falar: essa abordagem reduz laços explícitos e melhora legibilidade da regra de negócio.

### Exemplo 4: limpeza de valores especiais do IDEB (slide 6)
Objetivo didático: mostrar estratégia de saneamento antes de converter para número.

```python
valores_nulos = ["ND", "ND*", "ND***", "(*)", "(**)", "--", "-", ""]

for col in cols_numericas:
  df_ideb[col] = df_ideb[col].replace(valores_nulos, np.nan)
  df_ideb[col] = df_ideb[col].astype(str).str.strip()
  df_ideb[col] = df_ideb[col].replace("nan", np.nan)
  df_ideb[col] = df_ideb[col].str.replace(",", ".", regex=False)
  df_ideb[col] = pd.to_numeric(df_ideb[col], errors="coerce")
```

Ponto para falar: o bloco transforma dados administrativos heterogêneos em dados analíticos consistentes.

### Exemplo 5: clusterização com KMeans e validação por silhouette (slide 7)
Objetivo didático: apresentar uso de classe de machine learning com método fit_predict.

```python
inertias, silhouettes = [], []
for k in range(2, 11):
  km = KMeans(n_clusters=k, random_state=42, n_init=10)
  labels = km.fit_predict(X_scaled)
  inertias.append(km.inertia_)
  silhouettes.append(silhouette_score(X_scaled, labels))

best_k = range(2, 11)[silhouettes.index(max(silhouettes))]
print(f"Melhor k pelo silhouette: {best_k}")
```

Ponto para falar: o melhor número de grupos não é arbitrário; ele é selecionado por critério quantitativo.

### Exemplo 6: importância de variáveis com Random Forest (slide 7 ou 8)
Objetivo didático: mostrar interpretação do modelo para pesquisa aplicada.

```python
rf = RandomForestRegressor(n_estimators=200, random_state=42)
rf.fit(X_rf, y_rf)

importancias = pd.Series(
  rf.feature_importances_,
  index=VARS_RF,
).sort_values(ascending=False)

print(importancias)
```

Ponto para falar: além de prever, o modelo ajuda a ranquear fatores mais relevantes para explicar variação do IDEB.

## Dica de apresentação dos trechos
- Mostrar no máximo 12 a 18 linhas por slide para manter legibilidade.
- Destacar em cor apenas 2 elementos por exemplo: nome da classe e método principal.
- Encerrar cada exemplo com uma frase de impacto metodológico: o que esse trecho viabiliza na pesquisa.
