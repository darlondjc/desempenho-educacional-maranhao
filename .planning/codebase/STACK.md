# Stack

## Languages

- **Python 3.12** — primary language for all data pipeline and analytics code
- **LaTeX** — academic article authoring (via `abntex2` document class, ABNT Brazilian standard)
- **Quarto Markdown (.qmd)** — report and slide generation (Quarto framework)
- **SCSS** — custom slide theme (`reports/theme.scss`)
- **SQL** — referenced in report template for DuckDB queries

## Runtime / Platform

- **CPython 3.12.3** — pinned via `.python-version` and `pyvenv.cfg`
- **uv 0.11.1** — package manager and virtual environment tool (replaces pip/venv)
- **Quarto** — document rendering engine for `.qmd` reports and RevealJS slides
- **LaTeX / latexmk** — PDF compilation for the academic article (`artigo/`)
- **Jupyter** — notebook runtime (`src/analytics.ipynb`), via `ipykernel` package

## Frameworks & Libraries

### Data Manipulation
- **pandas >= 3.0.2** — core DataFrame operations across all pipeline stages
- **numpy >= 2.3.3** — numerical operations and array manipulation
- **pandera >= 0.30.1** — data schema validation and type checking

### Machine Learning & Statistics
- **scikit-learn >= 1.8.0** — KMeans clustering, PCA, Random Forest (Regressor and Classifier), RobustScaler, silhouette score, adjusted_rand_score
- **scipy >= 1.16.2** — Mann-Whitney U test (`stats.mannwhitneyu`) for statistical significance

### Visualization
- **matplotlib >= 3.10.8** — static chart generation (histograms, bar charts, scatter plots)
- **seaborn >= 0.13.2** — declared as dependency (statistical visualization enhancement)
- **plotly** — referenced in `reports/report.qmd` template for interactive charts (not in pyproject.toml main deps; may be used in notebook)

### Data I/O
- **openpyxl >= 3.1.5** — reading `.xlsx` files (IDEB, IBGE, IDHM base data)
- **odfpy >= 1.4.1** — reading `.ods` files (Sinopse Estatística docentes table)
- **duckdb >= 1.5.2** — embedded analytical SQL database; referenced in report template for `data/analytics.duckdb`
- **requests >= 2.33.1** — HTTP client (declared; no explicit network calls found in current source)

### Environment & Utilities
- **python-dotenv >= 1.2.2** — `.env` file loading for environment variables
- **ipykernel >= 6.30.1** — Jupyter kernel support for `src/analytics.ipynb`

### Dev Dependencies
- **nbconvert >= 7.17.1** — Jupyter notebook to other format conversion

### LaTeX Packages (article)
- `abntex2` — ABNT Brazilian standards document class
- `abntex2cite` — ABNT citation style (author-year via `\citet`)
- `amsmath`, `amsfonts`, `amssymb` — mathematical typesetting
- `graphicx`, `caption`, `subcaption` — figure inclusion and captioning
- `hyperref`, `xurl` — hyperlinks and URL line-breaking
- `longtable`, `booktabs`, `multirow`, `array` — table formatting
- `babel` (brazil), `inputenc` (utf8), `fontenc` (T1) — language and encoding

## Dependencies

Declared in `pyproject.toml`:

```
duckdb>=1.5.2
ipykernel>=6.30.1
matplotlib>=3.10.8
numpy>=2.3.3
odfpy>=1.4.1
openpyxl>=3.1.5
pandas>=3.0.2
pandera>=0.30.1
python-dotenv>=1.2.2
requests>=2.33.1
scikit-learn>=1.8.0
scipy>=1.16.2
seaborn>=0.13.2
```

Dev group (declared in `pyproject.toml` under `[dependency-groups]`):
```
nbconvert>=7.17.1
```

Lock file: `uv.lock` (uv revision 3, resolves from PyPI `https://pypi.org/simple`)

## Configuration

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, Python version constraint (`>=3.12`), all runtime and dev dependencies |
| `.python-version` | Pins Python to `3.12` for uv/pyenv tooling |
| `uv.lock` | Full dependency lock file (all transitive packages with hashes) managed by uv |
| `.venv/pyvenv.cfg` | Virtual environment config (CPython 3.12.3, created by uv 0.11.1) |
| `.gitignore` | Excludes `.venv/`, `data/raw/*`, `data/trusted/*`, `data/mart/*`, `reports/figures/*`, LaTeX build artifacts |
| `.claude/settings.local.json` | Claude Code permissions config; grants access to `.planning/` additional directory |
| `reports/report.qmd` | Quarto report template with DuckDB + Plotly code blocks |
| `reports/seminario_slides.qmd` | Quarto RevealJS slide deck (language: pt-BR) |
| `reports/theme.scss` | Custom SCSS theme for RevealJS presentation |
| `artigo/main.tex` | Root LaTeX document for the academic paper |
| `artigo/references.bib` | BibTeX bibliography |
