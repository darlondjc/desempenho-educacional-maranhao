# Conventions

## Code Style

- **Language:** Python 3.12 (pinned via `.python-version`)
- **Package manager:** `uv` with `pyproject.toml` for dependency declaration; `uv.lock` for reproducibility
- **Line length:** No enforced formatter (no `black`, `ruff`, or `flake8` config present); code uses 4-space indentation in `src/analytics.py` and `src/ingest.py`, but 2-space indentation in `src/transform.py` — inconsistency across files
- **Imports:** Standard library first (`pathlib`, `time`, `threading`, `unicodedata`), then third-party (`pandas`, `numpy`, `matplotlib`, `sklearn`, `scipy`). No `__init__.py` files; scripts import siblings with bare names (e.g., `from util import start_timer`)
- **Type hints:** Used consistently on function signatures (e.g., `-> pd.DataFrame`, `-> None`, `-> Path`, `-> tuple`, `-> float`, `-> list`); parameter types annotated with standard library and pandas types
- **String formatting:** f-strings throughout; Portuguese-language print statements for pipeline progress messages
- **Constants:** Module-level constants use `UPPER_SNAKE_CASE` and are defined at the top of each file (e.g., `BASE_DIR`, `RAW_DIR`, `TRUSTED_DIR`, `FIGURES_DIR`, `CLUSTER_K`, `VARS_CLUSTER`)

## Naming Conventions

- **Variables and columns:** Brazilian government naming conventions (`CO_MUNICIPIO`, `NO_MUNICIPIO`, `SG_UF`, `QT_MAT_BAS`, `PCT_ESCOLAS_COM_INTERNET`) — uppercase with underscores, mirroring source dataset schemas from INEP/IBGE
- **Derived indicator columns:** Prefix-coded: `QT_` (quantities/counts), `PCT_` (percentages), `VL_` (observed values), `IN_` (binary indicators), `MEDIA_` (averages), `PROXY_` embedded in names for proxy variables
- **Function names:** Snake case; semantically descriptive with verb-subject pattern:
  - `build_indicadores_municipais_ma_ideb_2023()` — build + subject + geo + source + year
  - `transform_indicadores_municipais_ma_ideb_2023()` — transform + subject + geo + source + year
  - `load_censo_microdados()`, `load_sinopse_docentes_efai_2023()` — load + subject
  - `safe_divide()`, `normalize_municipio_code()`, `ensure_columns()` — utility verbs
  - Private helpers: leading underscore (`_renderizar_ou_salvar`, `_slug_cluster_nome`, `_estabilidade_clusters`, `_clusters_ordenados_por_renda`, `_nome_cluster`)
- **Module names:** Short, functional nouns: `ingest.py`, `transform.py`, `analytics.py`, `util.py`
- **File and directory names:** Lowercase with underscores for Python files; lowercase with hyphens for the project root (`desempenho-educacional-maranhao`)
- **Data directory naming:** Layered architecture — `data/base/` (source files), `data/raw/` (post-ingest CSVs), `data/trusted/` (post-transform merged CSV), `data/mart/` (reserved for aggregated outputs)

## Patterns

- **Layered ETL pipeline:** Three explicit stages: ingest (`src/ingest.py`) → transform (`src/transform.py`) → analytics (`src/analytics.py`). Each stage reads from its preceding layer's output directory
- **`main()` entry point:** Every script defines a `main() -> None` function as the pipeline orchestrator, guarded by `if __name__ == "__main__": main()`
- **Pandas chain style:** Heavy use of method chaining — `groupby().agg().assign()` — to express multi-step transformations as a single readable expression (seen in `src/ingest.py` `build_indicadores_municipais_ma_censo_escolar_2023()`)
- **Feature flag pattern:** Boolean flags checked before computing optional features (e.g., `has_doc_sup`, `has_corrfluxo` in `src/ingest.py`) to handle missing columns in source data gracefully
- **Existence checks before merges:** `if ideb_path.exists():` guards optional enrichment merges; `FileNotFoundError` raised for required files
- **`safe_divide` utility:** Replaces denominator zero with `pd.NA` before division to produce `NA` (not `inf`) for downstream compatibility
- **`normalize_municipio_code` utility:** Normalizes municipality codes to nullable `Int64` then `string` so joins across heterogeneous sources (IDEB/Censo/IBGE) work without silent failures
- **`ensure_columns` utility:** Adds missing columns with default value `0` before operations, decoupling logic from source schema variations
- **Output persistence:** CSVs with semicolon separator (`sep=";"`) saved to the appropriate layer directory; figures saved as PNG at 150 DPI to `reports/figures/`
- **Random seed consistency:** `random_state=42` used everywhere ML randomness is involved (KMeans, RandomForest, bootstrap loops)
- **`_renderizar_ou_salvar` pattern:** A single private function centralizes the save-or-show decision for all matplotlib figures in `src/analytics.py`
- **Global module-level variable lists:** `VARS_CLUSTER`, `VARS_EXPLICATIVAS_IDEB`, `VARS_COMPARACAO`, `VARS_RF` in `src/analytics.py` act as configuration for which features are used in each analysis stage
- **Background timer utility:** `src/util.py` provides `start_timer()` / `stop_timer()` using a daemon thread to display elapsed time during long-running ingest operations

## Error Handling

- **`FileNotFoundError` for required files:** `resolve_censo_path()` in `src/ingest.py` raises `FileNotFoundError` with a descriptive message when the microdados CSV is absent — no silent fallback for critical inputs
- **Defensive column existence checks:** `if 'COLUMN' in df.columns:` guards `drop()` calls throughout `src/transform.py` to avoid KeyError on optional columns
- **`errors='coerce'` for numeric conversion:** All `pd.to_numeric()` calls use `errors='coerce'` to convert unparseable values to `NaN` rather than raising exceptions
- **`fillna(0)` for arithmetic safety:** Quantity columns from the sinopse are filled with `0` before integer casting to prevent NA-to-int conversion failures
- **No try/except blocks:** The codebase contains no explicit `try/except` error handling beyond the one `raise FileNotFoundError` — errors propagate as Python exceptions by default
- **`pd.NA` propagation:** `safe_divide` ensures division results stay as `NA` rather than `inf`/`nan` for downstream analytical consistency

## Documentation

- **Section banners:** Visual comment dividers used extensively: `# ── SECTION NAME ───────────────────` to separate logical sections within files
- **Inline comments:** Brief, contextual comments in Portuguese explaining business logic (e.g., `# Filtra apenas municípios do Maranhão`, `# Proxy 1 para distorção idade-série`)
- **Docstrings:** Sparse — only two functions have docstrings (`load_sinopse_docentes_efai_2023`, `build_indicadores_municipais_ma_censo_docentes_2023`), both in Portuguese
- **README.md:** Project-level documentation covers objective, project structure, and execution commands for the pipeline and Quarto reports
- **Quarto slides as documentation:** `reports/seminario_slides.qmd` doubles as technical documentation, explaining design decisions (why `safe_divide`, why `normalize_municipio_code`, tradeoffs of pandas vs DuckDB)
- **TODO comments:** Present in `reports/report.qmd` as Quarto template placeholders for sections not yet filled in
- **No automated API docs:** No Sphinx, MkDocs, or similar tooling configured
