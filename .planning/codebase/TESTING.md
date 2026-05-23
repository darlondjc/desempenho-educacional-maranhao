# Testing

## Framework

No testing framework is configured or used in this project. There are no references to `pytest`, `unittest`, `hypothesis`, or any other test library in `pyproject.toml` or anywhere in the codebase. The `[dependency-groups]` section in `pyproject.toml` contains only `dev = ["nbconvert>=7.17.1"]` — `nbconvert` is used for notebook execution/export, not testing.

No test runner configuration files exist (no `pytest.ini`, `setup.cfg`, `tox.ini`, `.pytest.ini`, or `conftest.py`).

## Structure

There is no test directory, no `tests/` folder, and no files matching `test_*.py` or `*_test.py` anywhere in the repository. The project has a single source module directory (`src/`) containing only production scripts:

- `src/ingest.py` — data ingestion pipeline
- `src/transform.py` — data cleaning and merging
- `src/analytics.py` — clustering, ML, and visualization
- `src/util.py` — timer utilities
- `src/analytics.ipynb` — Jupyter notebook wrapping `analytics.py`

Verification of correctness is done manually by inspecting print output during `main()` execution and by visual inspection of the generated HTML report (`reports/analytics-executado.html`) and PNG figures in `reports/figures/`.

## Coverage

### What is tested (informally, at runtime)

- **Schema presence:** `ensure_columns()` in `src/ingest.py` adds default zero-valued columns if expected columns are absent — a guard against source schema drift
- **Feature availability flags:** `has_doc_sup`, `has_doc_lic`, `has_corrfluxo` boolean flags check whether source data columns have non-zero values before computing derived indicators — prevents misleading zero-based ratios
- **File existence:** `resolve_censo_path()` raises `FileNotFoundError` if the large microdados CSV is missing before the pipeline proceeds
- **Shape/count printing:** `main()` in `src/ingest.py` prints row and column counts after each ingest step, providing a manual sanity check

### What is not tested

- **Data correctness:** No assertions or schema validation tests verify that output values are within expected ranges (e.g., percentages between 0 and 100, IDEB values between 0 and 10)
- **`pandera` is declared as a dependency** (`pandera>=0.30.1` in `pyproject.toml`) but is not imported or used anywhere in the source files — schema validation is set up as a dependency but never applied
- **Unit functions:** Pure utility functions like `safe_divide()`, `normalize_municipio_code()`, `ensure_columns()`, `_slug_cluster_nome()`, `_estabilidade_clusters()` have no unit tests
- **Transform logic:** All four `transform_*` functions in `src/transform.py` are untested; correctness of column drops, renames, and type conversions is verified only by inspection
- **Merge correctness:** The `merge_dataframes()` function in `src/transform.py` performs index-based merge (not key-based) for ideb + censo join — a potentially fragile assumption with no test guarding it
- **Analytics pipeline:** Clustering outputs, feature importance rankings, and Mann-Whitney test results are printed to stdout but never asserted against expected values
- **Notebook execution:** `src/analytics.ipynb` is executed via `jupyter nbconvert --execute` as part of the report generation step — this confirms the notebook runs end-to-end without errors, but verifies no outputs

## Notable Patterns

- **Notebook as integration test proxy:** Running `uv run jupyter nbconvert --to html --execute src/analytics.ipynb` acts as a de-facto end-to-end integration check. If the pipeline is broken, the nbconvert command fails. This is the closest thing to a CI check in the project
- **Print-driven validation:** `main()` functions print intermediate dataset shapes (`len(df)`, `df.shape[1]`, `df.info()`, `df.head()`) to the terminal, serving as an informal smoke test during development
- **`random_state=42` everywhere:** Deterministic seeds in KMeans, RandomForest, and bootstrap loops ensure that repeated runs produce identical results — a prerequisite for reproducible verification even without formal assertions
- **`pandera` gap:** The `pandera` schema validation library is listed as a production dependency but is unused. This represents a planned but unimplemented quality gate — the intent to add DataFrame schema validation is evident from the dependency declaration
- **No CI/CD pipeline:** No GitHub Actions, Makefile targets, or shell scripts automate test runs. The project relies entirely on manual execution
