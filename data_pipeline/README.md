# Module 1 — Data Pipeline

## Scope

The script scrapes the first five pages of Books to Scrape (100 catalogue rows), follows each book detail page for its category, cleans the required fields, converts price using the fixed project baseline `1 GBP = 105.50 INR`, loads a normalized SQLite database, and demonstrates SQL plus pandas access.

## Cleaning decisions

- `price_gbp`: remove `£` and parse as float.
- `rating`: map `One`…`Five` to 1…5.
- `in_stock`: parse availability text into a boolean.
- Numeric parsing failures are median-imputed.
- Rows missing unrecoverable required text fields are dropped and the count is logged.

## Required SQL coverage

The script executes queries covering `SELECT/WHERE`, `ORDER BY`, `LIMIT`, `DISTINCT`, `BETWEEN`, and a `JOIN`. It saves both the SQL strings and outputs under `output/`.
