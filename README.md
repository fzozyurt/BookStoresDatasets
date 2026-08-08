# BookStores Datasets

> Automated book price tracking for Turkish online bookstores — scrape → diff → publish → visualize.

[![Python](https://img.shields.io/badge/python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/badge/uv-managed-2f8c9f?logo=astral)](https://docs.astral.sh/uv/)
[![CI](https://img.shields.io/badge/CI-lint%20%2B%20tests-2088ff)](#automation)
[![Kaggle](https://img.shields.io/badge/Data-Kaggle-20beff?logo=kaggle)](https://www.kaggle.com/)
[![GitHub Pages](https://img.shields.io/badge/Dashboard-GitHub%20Pages-222222?logo=github)](https://pages.github.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](#license)

`bookdata` is a clean, testable web-scraping pipeline that tracks book prices across Turkish
bookstores. It scrapes categories and products asynchronously, normalizes the data, computes
price changes, and maintains an append-only CSV dataset that lives on **Kaggle**. A scheduled
CI job renders an interactive **Plotly dashboard** and publishes it to **GitHub Pages** — fully
hands-free.

## Highlights

- ⚡ **Async scraping** — `httpx`-based concurrent fetcher with retries, backoff and per-host rate limiting
- 🧹 **Port-adapter architecture** — clean separation of concerns, mockable and fully unit-tested
- 📈 **Price-diff engine** — vectorized pandas diff so the dataset only grows with real price changes
- 🗂️ **Centralized ignore rules** — one global `ignore_categories.txt` applies to every store
- 🤖 **Zero-ops automation** — GitHub Actions runs on a CRON schedule *and* on demand
- 📊 **Interactive dashboard** — Plotly charts in a single small HTML file (CDN-hosted)
- 🔓 **Open source by default** — no credentials or personal IDs in the codebase; all configured via environment

## Architecture

```
                 ┌────────────────────────────── GitHub Actions ─────────────────────────────┐
                 │   schedule / workflow_dispatch                                             │
                 ▼                                                                           │
        ┌──────────────┐    ┌──────────────┐   ┌───────────────┐   ┌───────────────────┐      │
        │ fetch_        │    │ pipeline     │   │ dataset       │   │ Kaggle Publisher  │      │
        │ categories    ├───▶│ filter →     ├──▶│ store (CSV)   ├──▶│ (append-only)     │      │
        │ fetch_        │    │ standardize  │   │ price diff    │   └───────────────────┘      │
        │ products      │    │ → merge      │   └───────┬───────┘                             │
        └──────────────┘    └──────────────┘           │                                      │
                                                       ▼                                      │
                                        ┌──────────────────────┐   ┌───────────────────┐       │
                                        │ analyze + dashboard  │──▶│ GitHub Pages       │──────┘
                                        │ (Plotly HTML)        │   │ (public dashboard) │
                                        └──────────────────────┘   └───────────────────┘
```

## Project structure

```
src/bookdata/
├── cli.py              # Typer CLI (scrape / categories / report / publish / stores)
├── config.py           # Settings from environment variables
├── logging_setup.py    # Central log configuration
├── models.py           # Category / Product data models
├── analyze.py          # Price changes, weekly trends, summary stats
├── dashboard.py        # Plotly dashboard renderer (single-file HTML)
├── pipeline/
│   ├── runner.py       # Orchestrates the scrape flow + store registry
│   ├── filter.py       # Applies global ignore rules to categories
│   ├── products.py     # Concurrent product collection
│   ├── standardize.py  # Normalizes scraped rows into the dataset schema
│   └── merge.py        # Computes price diffs against the last known price
└── adapters/
    ├── http.py         # Async HTTP client (retries, rate limiting)
    ├── kaggle.py       # Kaggle dataset publisher
    ├── storage.py      # CSV dataset store
    └── stores/
        ├── base.py     # StorePort abstract interface
        ├── bkm.py      # BKM Kitap adapter
        └── kitapyurdu.py  # Kitap Yurdu adapter
```

## Quick start

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv sync                 # install runtime dependencies
uv sync --extra report  # + plotly for the dashboard
```

## Usage

Every command runs through the `bookdata` CLI:

| Command | Description |
| --- | --- |
| `bookdata scrape <store>` | Category → filter → products → standardize → price diff → append to dataset |
| `bookdata categories <store>` | List a store's categories (ignore rules applied) |
| `bookdata report` | Generate the interactive dashboard from all datasets |
| `bookdata publish <store>` | Upload the dataset to Kaggle |
| `bookdata stores` | List registered store adapters |

Examples:

```sh
uv run bookdata scrape bkm
uv run bookdata scrape kitapyurdu
uv run bookdata categories bkm -n 20
uv run bookdata report -o Report/index.html
uv run bookdata publish bkm
```

`KY` / `BKM` shortcuts are accepted for `kitapyurdu` / `bkm`.

### Ignore rules

`ignore_categories.txt` holds one pattern per line (blank lines and `#` comments are ignored).
Any category whose name or URL contains a pattern is skipped — **for every store**. This is the
single source of truth for "not a book" categories (stationery, toys, accessories, music, film…).
Override the file location with `BOOKDATA_IGNORE_FILE`.

### Configuration

All settings are environment-driven — nothing is hardcoded:

| Variable | Default | Purpose |
| --- | --- | --- |
| `BOOKDATA_STORE` | `bkm` | Default store for commands that need one |
| `BOOKDATA_DATA_DIR` | `Data` | Where `*_Datasets.csv` files live |
| `BOOKDATA_LOG_DIR` | `logs` | Log output directory |
| `BOOKDATA_LOG_LEVEL` | `INFO` | Log verbosity |
| `BOOKDATA_IGNORE_FILE` | `ignore_categories.txt` | Global category ignore patterns |
| `BOOKDATA_CONCURRENCY` | `12` | Parallel HTTP requests |
| `BOOKDATA_TIMEOUT` | `20` | Request timeout (seconds) |
| `BOOKDATA_RETRY_ATTEMPTS` | `3` | Retries per request |
| `BOOKDATA_MIN_INTERVAL` | `0.2` | Min seconds between requests per host |
| `BOOKDATA_MAX_PAGES` | `50` | Max pagination pages per category |
| `BOOKDATA_KAGGLE_DATASET` | — | Kaggle dataset id (`owner/slug`) for publishing |
| `KAGGLE_USERNAME` / `KAGGLE_KEY` | — | Kaggle API credentials |

## Automation

GitHub Actions drives everything — every workflow runs on a **CRON schedule** and can be
triggered **manually** from the Actions tab.

| Workflow | Trigger | What it does |
| --- | --- | --- |
| `BKM_Kitap.yml` | CRON (2×/day) + manual | Scrapes BKM, updates the Kaggle dataset, commits logs |
| `Kitap_Yurdu.yml` | CRON (2×/day) + manual | Scrapes Kitap Yurdu, updates the Kaggle dataset, commits logs |
| `generate_report.yml` | CRON (weekly) + manual | Pulls datasets from Kaggle, renders the dashboard, deploys it to GitHub Pages |
| `ci.yml` | push + PR | Runs `ruff check`, `ruff format --check`, and `pytest` |

Scrape workflows download the latest dataset from Kaggle, compute price diffs against it,
re-upload the updated dataset, and commit fresh logs — so the repository always shows recent
activity and the data stays authoritative on Kaggle.

### Setup

1. Add repository **secrets**: `KAGGLE_USERNAME`, `KAGGLE_KEY`.
2. Add repository **variables**: `KAGGLE_DATASET_BKM`, `KAGGLE_DATASET_KY` (e.g. `owner/your-dataset`).
3. Enable **GitHub Pages** (source: GitHub Actions) for the dashboard deployment.

## Dashboard features

The generated dashboard is a single self-contained HTML page:

- **Summary cards** — record/product counts, last scrape date, rising/falling stats
- **Store comparison** — average price change per store
- **Category analysis** — change distribution across categories and stores
- **Top movers** — 10 most increased / 10 most decreased titles
- **Weekly trend** — average price over time

Plotly loads from a CDN, keeping the HTML tiny while staying fully interactive.

## Adding a store

1. Create an adapter in `src/bookdata/adapters/stores/` implementing `StorePort`
   (use `bkm.py` or `kitapyurdu.py` as a template).
2. Register it in `STORE_REGISTRY` in `src/bookdata/pipeline/runner.py`.
3. Add any store-specific patterns to `ignore_categories.txt` if needed.

## Development

```sh
uv run pytest                 # run tests
uv run ruff check src tests   # lint
uv run ruff format src tests  # format
```

The test suite covers filtering, standardization, merging, storage, analysis and dashboard
rendering — and the CI workflow runs it on every push.

## License

[MIT](LICENSE) © BookStores Datasets contributors
