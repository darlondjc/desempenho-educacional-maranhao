# Integrations

## External APIs

- **None currently active.** The `requests>=2.33.1` package is declared as a dependency in `pyproject.toml` but no HTTP API calls appear in the current source code (`src/ingest.py`, `src/transform.py`, `src/analytics.py`). The package may be a placeholder for future data fetching or a transitive requirement.
- **PyPI** — `uv.lock` resolves all packages from `https://pypi.org/simple`.

## Databases

- **DuckDB (embedded)** — referenced in `reports/report.qmd` template as `duckdb.connect("data/analytics.duckdb", read_only=True)` with a SQL query `SELECT * FROM fato_principal LIMIT 1000`. The `.duckdb` file is expected in `data/mart/` (gitignored via `data/mart/*`). The package `duckdb>=1.5.2` is installed. The database file is generated locally; no remote database server is configured.

## Data Sources

All data sources are static files loaded locally. No live API calls are made during pipeline execution.

### Base Input Files (tracked in git under `data/base/`)

| File | Description | Format |
|------|-------------|--------|
| `data/base/divulgacao_anos_iniciais_municipios_2023.xlsx` | INEP IDEB 2023 — municipal results for early-years elementary education | Excel (.xlsx) |
| `data/base/ibge.xlsx` | IBGE 2010 — municipal indicators (per-capita income, urban population) | Excel (.xlsx) |
| `data/base/idhm.xlsx` | IDHM 2010 — Human Development Index by municipality | Excel (.xlsx) |
| `data/base/microdados_censo_escolar_2023/dados/microdados_ed_basica_2023.csv` | INEP Censo Escolar 2023 microdata — school-level infrastructure and teacher data | CSV (semicolon-separated, latin1 encoding) |
| `data/base/microdados_censo_escolar_2023/dados/docentes.ods` | INEP Sinopse Estatística 2023 Table 2.23 — EFAI teachers by municipality | ODS spreadsheet |

### Data Origin (institutional sources)

- **INEP (Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira)** — IDEB results and Censo Escolar microdata; data downloaded manually from [https://www.gov.br/inep](https://www.gov.br/inep)
- **IBGE (Instituto Brasileiro de Geografia e Estatística)** — 2010 Census municipal socioeconomic indicators
- **PNUD / Atlas Brasil** — IDHM (Human Development Index) 2010 data by municipality

### Generated Intermediate Files (gitignored, produced by pipeline)

| Path | Produced by | Description |
|------|-------------|-------------|
| `data/raw/indicadores_municipais_ma_ideb_2023.csv` | `src/ingest.py` | IDEB filtered for Maranhão municipal network |
| `data/raw/indicadores_municipais_ma_censo_escolar_2023.csv` | `src/ingest.py` | Censo Escolar aggregated infrastructure and teacher indicators by municipality |
| `data/raw/indicadores_municipais_ma_ibge_2010.csv` | `src/ingest.py` | IBGE 2010 indicators raw extract |
| `data/raw/indicadores_municipais_ma_idhm_2010.csv` | `src/ingest.py` | IDHM 2010 indicators raw extract |
| `data/trusted/indicadores_municipais_ma.csv` | `src/transform.py` | Merged and cleaned master dataset (IDEB + Censo + IBGE + IDHM) — semicolon-separated |
| `data/mart/analytics.duckdb` | Not yet implemented | DuckDB analytical database (referenced in report template) |

### Pipeline Architecture

```
data/base/          (raw source files — Excel, CSV, ODS)
    ↓  src/ingest.py
data/raw/           (per-source extracted CSVs)
    ↓  src/transform.py
data/trusted/       (merged, cleaned master CSV)
    ↓  src/analytics.py / analytics.ipynb
reports/figures/    (PNG charts)
reports/            (HTML report, slides)
```

## Authentication

- **None.** No authentication mechanisms are in use. All data sources are public institutional datasets loaded from local files. The `python-dotenv` package is installed (`.env` loading capability), but no `.env` file is tracked and no credentials are required by the current codebase.

## Other External Services

- **Quarto** — CLI tool for rendering `.qmd` documents to HTML and RevealJS. Invoked locally via `uv run quarto render reports/report.qmd` (as documented in the report template). Not a networked service; runs locally.
- **LaTeX / latexmk** — local TeX distribution for compiling `artigo/main.tex` to PDF. Build artifacts (`.aux`, `.bbl`, `.log`, etc.) are gitignored.
- **GitHub / Git remote** — the repository has a configured git remote (`.git/FETCH_HEAD` present, `.git/packed-refs` present), used for version control and collaboration. No CI/CD pipeline files (e.g., `.github/workflows/`) are present.
