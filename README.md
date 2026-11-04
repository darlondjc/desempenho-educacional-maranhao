# Fatores intracontextuais do desempenho no IDEB (municípios do Maranhão)

Código de reprodução do artigo submetido à Revista Brasileira de Informática na Educação (RBIE). Esta versão foi anonimizada para a avaliação duplamente anônima.

O pipeline segmenta os municípios maranhenses por contexto socioeconômico (renda *per capita* e pobreza extrema, Censo Demográfico 2022) com *K-Means* e, dentro de cada grupo, compara os municípios de maior e de menor IDEB 2025 (anos iniciais, rede municipal) com o teste de Mann-Whitney.

## Requisitos

Python 3.12 ou superior e [uv](https://github.com/astral-sh/uv).

```bash
uv sync
```

## Dados

Já incluídos em `data/base/`:

- `divulgacao_anos_iniciais_municipios_2025.xlsx`: resultados do IDEB 2025 por município (INEP);
- `renda_per_capita_censo2022_ma.json` e `pobreza_extrema_censo2022_ma.json`: IBGE, Censo Demográfico 2022, Sidra, tabelas 10295 e 10296.

Por causa do tamanho (cerca de 600 MB), os arquivos do Censo Escolar 2025 não estão no repositório. Baixe-os do portal de dados abertos do INEP e coloque-os em `data/base/microdados_censo_escolar_2025/dados/`:

- Microdados do Censo Escolar da Educação Básica 2025 (<https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar>): `Tabela_Escola_2025_V2.csv`, `Tabela_Docente_2025_V2.csv`, `Tabela_Matricula_2025_V2.csv` e `Tabela_Turma_2025_V2.csv`;
- Sinopse Estatística da Educação Básica 2025 (<https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/sinopses-estatisticas/educacao-basica>): planilha de docentes, salva como `sinopse_docentes_2025.xlsx`.

## Execução

```bash
uv run python src/ingest.py      # data/base  -> data/raw
uv run python src/transform.py   # data/raw   -> data/trusted
uv run python src/analytics.py   # segmentação, testes e figuras
```

O notebook `src/analytics.ipynb` reproduz a análise passo a passo:

```bash
uv run jupyter nbconvert --to html --execute src/analytics.ipynb --output-dir reports
```

O *K-Means* usa semente fixa (`random_state=42`, `n_init=10`), e os resultados são determinísticos.
