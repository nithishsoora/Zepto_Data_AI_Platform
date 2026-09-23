# SQL Query Set

The executable query set is defined in `scrape_pipeline.py` and is executed against the generated SQLite database.

1. `SELECT` + `WHERE`
2. `ORDER BY` + `LIMIT`
3. `DISTINCT`
4. `BETWEEN`
5. `JOIN` between `books` and `categories`

Running `python scrape_pipeline.py` creates the database and writes each query's output under `output/`, including a `pd.read_sql` vs `pd.merge` equivalence check for the join.
