# Structure

## Directory Layout

```
desempenho-educacional-maranhao/
│
├── src/                          # Python source code (pipeline scripts + notebook)
│   ├── ingest.py                 # ETL ingestion: source files → data/raw/
│   ├── transform.py              # ETL transformation: data/raw/ → data/trusted/
│   ├── analytics.py              # Analysis module: clustering, ML, visualizations
│   ├── analytics.ipynb           # Jupyter notebook (mirrors analytics.py, interactive)
│   └── util.py                   # Shared utilities (CLI timer)
│
├── data/                         # Three-zone data lake
│   ├── base/                     # Landing zone: original source files (not gitignored)
│   │   ├── divulgacao_anos_iniciais_municipios_2023.xlsx   # IDEB EFAI 2023 (INEP)
│   │   ├── ibge.xlsx                                       # IBGE socioeconomic data 2010
│   │   ├── idhm.xlsx                                       # HDI by municipality 2010
│   │   └── microdados_censo_escolar_2023/
│   │       └── dados/
│   │           ├── microdados_ed_basica_2023.csv           # School census microdata (large)
│   │           └── docentes.ods                            # Teacher qualification sinopse
│   │
│   ├── raw/                      # Per-source cleaned CSVs (gitignored, regenerated)
│   │   ├── indicadores_municipiais_ma_ideb_2023.csv
│   │   ├── indicadores_municipiais_ma_censo_escolar_2023.csv
│   │   ├── indicadores_municipiais_ma_ibge_2010.csv
│   │   └── indicadores_municipiais_ma_idhm_2010.csv
│   │
│   ├── trusted/                  # Analysis-ready merged dataset (gitignored)
│   │   └── indicadores_municipais_ma.csv                   # 48-column municipality table
│   │
│   └── mart/                     # Downstream aggregations (currently empty)
│
├── reports/                      # Outputs and presentation materials
│   ├── analytics-executado.html  # Primary deliverable: executed notebook as HTML
│   ├── report.qmd                # Quarto analytical report template (scaffold)
│   ├── seminario_slides.qmd      # Quarto RevealJS presentation
│   ├── seminario_slides.html     # Compiled RevealJS HTML
│   ├── seminario_conceitos_python.md  # Supporting markdown notes
│   ├── theme.scss                # Custom RevealJS theme
│   ├── figures/                  # Generated PNG charts (gitignored, regenerated)
│   │   ├── distribuicao_ideb.png
│   │   ├── elbow_silhouette.png
│   │   ├── pca_clusters.png
│   │   ├── random_forest_importancia.png
│   │   └── cluster_<name>_variaveis_relevantes_destaque.png
│   └── seminario_slides_files/   # Quarto build artifacts (JS/CSS libs)
│
├── artigo/                       # LaTeX academic paper manuscript
│   ├── main.tex                  # Root LaTeX file (includes all sections)
│   ├── 0_abstract.tex
│   ├── 1_introduction.tex
│   ├── 2_related_works.tex
│   ├── 3_material_and_methods.tex
│   ├── 4_computational_experiments.tex
│   ├── 5_conclusions.tex
│   ├── 6_acknowlegment_and_credits.tex
│   ├── references.bib            # BibTeX bibliography
│   ├── main.pdf                  # Compiled paper (gitignored via *.pdf rule excluded here)
│   └── images/
│       └── logo_ifma.png
│
├── pyproject.toml                # Project metadata and dependency declarations (uv/PEP 517)
├── uv.lock                       # Locked dependency versions
├── .python-version               # Python version pin (3.12)
├── .gitignore                    # Excludes raw/trusted/mart data, venv, LaTeX artifacts
├── README.md                     # Setup and execution instructions
├── .venv/                        # Virtual environment (gitignored)
└── .planning/                    # Planning and architecture docs
    └── codebase/
        ├── ARCHITECTURE.md
        └── STRUCTURE.md
```

## Key Locations

| What | Where |
|---|---|
| Ingestion script (source → raw) | `src/ingest.py` |
| Transformation script (raw → trusted) | `src/transform.py` |
| Analysis module | `src/analytics.py` |
| Interactive notebook | `src/analytics.ipynb` |
| Shared utilities | `src/util.py` |
| Primary analytical dataset | `data/trusted/indicadores_municipais_ma.csv` |
| IDEB source data | `data/base/divulgacao_anos_iniciais_municipios_2023.xlsx` |
| Census microdata | `data/base/microdados_censo_escolar_2023/dados/microdados_ed_basica_2023.csv` |
| Teacher qualification sinopse | `data/base/microdados_censo_escolar_2023/dados/docentes.ods` |
| Main report output | `reports/analytics-executado.html` |
| Generated figures | `reports/figures/` |
| Presentation slides source | `reports/seminario_slides.qmd` |
| LaTeX article root | `artigo/main.tex` |
| Dependency declaration | `pyproject.toml` |

## Naming Conventions

### Files
- Python modules use lowercase single-word names: `ingest.py`, `transform.py`, `analytics.py`, `util.py`
- Data files follow the pattern `indicadores_municipais_ma_<source>_<year>.<ext>` (e.g., `indicadores_municipais_ma_ideb_2023.csv`)
- The merged trusted file drops the source suffix: `indicadores_municipais_ma.csv`
- Report output files use Portuguese descriptive names with hyphens: `analytics-executado.html`, `seminario_slides.qmd`
- Generated figures use underscores: `elbow_silhouette.png`, `pca_clusters.png`, `random_forest_importancia.png`
- Per-cluster figures follow: `cluster_<slug>_variaveis_relevantes_destaque.png` (e.g., `cluster_vulneraveis_variaveis_relevantes_destaque.png`)
- LaTeX sections are numbered: `0_abstract.tex`, `1_introduction.tex`, etc.

### Columns / Variables
- Municipality identifier: `CO_MUNICIPIO` (IBGE 7-digit code, stored as string to preserve leading zeros)
- Municipality name: `NO_MUNICIPIO` (uppercased for joins)
- Count columns: prefix `QT_` (e.g., `QT_ESCOLAS`, `QT_DOC_BAS`, `QT_MAT_BAS`)
- Percentage columns: prefix `PCT_` (e.g., `PCT_ESCOLAS_COM_INTERNET`, `PCT_DOC_SUPERIOR_COMPLETO`)
- Average columns: prefix `MEDIA_` (e.g., `MEDIA_ALUNOS_POR_TURMA_BAS`)
- IDEB value: `VL_OBSERVADO_2023`; approval rate: `VL_APROVACAO_2023_*`; score: `VL_NOTA_MEDIA_2023`
- Socioeconomic: `RENDA_PER_CAPITA_2010`, `POPULACAO_URBANA_2010`, `IDHM_2010`
- Derived/proxy variables: suffix `_PROXY_<meaning>` (e.g., `PCT_MAT_15_ANOS_OU_MAIS_PROXY_DISTSERIE`)
- Cluster outputs: `CLUSTER` (integer), `CLUSTER_NOME` (string label), `PERFIL` (string: alto/médio/baixo)

### Python Functions
- Builder functions: `build_<entity>_<source>_<year>()` in `ingest.py`
- Transformer functions: `transform_<entity>_<source>_<year>()` in `transform.py`
- Analysis functions: Portuguese verb names — `carregar_dados()`, `normalizar()`, `clusterizar()`, `nomear_clusters()`, `visualizar_pca()`, `comparar_perfis()`, `mann_whitney()`, `random_forest()`
- Private helpers: underscore prefix — `_renderizar_ou_salvar()`, `_clusters_ordenados_por_renda()`, `_nome_cluster()`, `_slug_cluster_nome()`, `_estabilidade_clusters()`, `_separar_alto_baixo_por_quantis()`
- Section comments use the pattern `# ── DESCRIPTION ───────────────────` throughout source files
