# Zepto Data & AI Platform — Capstone Project

A single repository containing three connected AI/ML engineering modules:

- `/data_pipeline` — scrape → clean → convert → normalize into SQLite → query with SQL/pandas.
- `/analytics` — profile and clean Titanic once → EDA → classification → imbalance comparison → RF tuning → regression → save complete pipeline.
- `/support_assistant` — policy corpus → local embeddings → ChromaDB retrieval → LangGraph routing → deterministic mock/optional LLM generation → FastAPI → Docker.

## Repository rules implemented

- One repository with all three modules.
- Markdown-only written interpretations.
- No paid services are required.
- The required GBP/INR conversion is the fixed project baseline **1 GBP = 105.50 INR**; no API is used.
- The support assistant defaults to `MOCK_LLM=1`, so the graded path makes no LLM API calls.
- The analytics module loads the raw Titanic dataset once with `sns.load_dataset('titanic')`, immediately writes `/analytics/titanic.csv`, and all later work reads that same cleaned DataFrame/CSV.

## Setup

Python 3.11+ is recommended.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Run Module 1

```bash
cd data_pipeline
python scrape_pipeline.py
```

This scrapes the first five paginated catalogue pages (100 books), follows each book detail page to obtain its category, cleans fields, converts GBP to INR using 105.50, creates `books.db`, runs the required SQL queries, and saves outputs under `data_pipeline/output/`.

## Run Module 2

The first run requires internet access because `sns.load_dataset('titanic')` fetches the source dataset. It is loaded only once.

```bash
cd analytics
python run_analytics.py
```

This creates/refreshes `titanic.csv`, performs EDA and modeling, saves charts under `analytics/outputs/`, and saves the complete fitted classifier pipeline under `analytics/models/best_pipeline.joblib`.

For grading/offline reruns after `titanic.csv` has been committed, use:

```bash
python run_analytics.py --offline
```

The offline mode reads the committed `titanic.csv` and does not call `sns.load_dataset`.

## Run Module 3

```bash
cd support_assistant
set MOCK_LLM=1          # Windows CMD
# export MOCK_LLM=1     # macOS/Linux
python -m uvicorn main:app --host 0.0.0.0 --port 7860
```

Then POST JSON to `/ask`, for example:

```bash
curl -X POST http://localhost:7860/ask \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"What is the delivery policy?\"}"
```

The first support-assistant run downloads the open-source `all-MiniLM-L6-v2` model if it is not already cached. No API key is needed.

## Docker

```bash
cd support_assistant
docker build -t zepto-support-assistant .
docker run --rm -p 7860:7860 -e MOCK_LLM=1 zepto-support-assistant
```

## Design decisions

### Data pipeline

The pipeline uses the first five catalogue pages because that gives 100 rows while keeping the scrape scope deterministic. Each book detail page is visited to capture the category. Numeric parsing failures are median-imputed; rows with unrecoverable required text fields are dropped with a logged count. SQLite uses `categories(category_id, category_name)` and `books(book_id, ..., category_id)` with a foreign key relationship.

### Analytics

The raw Titanic data is loaded once. Missing-value handling follows the required threshold: under 5% → drop rows; 5–30% → impute; above 30% → drop the column when it is not an independent measured feature. Thus `embarked` rows are dropped because its missing rate is below 5%, `age` is median-imputed because it is between 5% and 30%, and `deck` is dropped because its missingness is above 30%. The classification preprocessing is separately fit only on the training split inside a `Pipeline`/`ColumnTransformer`.

### Support assistant

The 8 supplied policy documents are loaded and chunked one document per chunk. `sentence-transformers` generates local embeddings and ChromaDB stores them. LangGraph routes queries using the required keyword heuristic in mock mode. Retrieval always happens for policy questions; only generation changes with `MOCK_LLM`. The final Pydantic schema is deterministic in mock mode.

## Git workflow

The repository history contains a feature branch with at least two commits merged back into `main`. Verify with:

```bash
git log --graph --all --oneline
```

## Source note

The assignment specification itself requires the exact 8 policy texts and the stated fixed conversion rate. The code in this repository follows those requirements. The Titanic fallback was generated from the standard Titanic sample data and transformed to the same column structure used by Seaborn's `titanic` dataset; the runtime code still uses `sns.load_dataset('titanic')` for the required online load path.
