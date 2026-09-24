from __future__ import annotations

import sqlite3
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"
GBP_TO_INR = 105.50
ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "books.db"
OUTPUT_DIR = ROOT / "output"
RAW_CSV = ROOT / "data" / "books_clean.csv"

RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def get_soup(session: requests.Session, url: str) -> BeautifulSoup:
    response = session.get(url, timeout=20)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def scrape_catalogue(max_pages: int = 5) -> list[dict]:
    rows: list[dict] = []
    with requests.Session() as session:
        session.headers.update({"User-Agent": "Mozilla/5.0 (educational scraping assignment)"})
        page_url = BASE_URL
        for page_number in range(1, max_pages + 1):
            soup = get_soup(session, page_url)
            cards = soup.select("article.product_pod")
            for card in cards:
                link = card.select_one("h3 a")
                title = link.get("title") if link else None
                detail_url = urljoin(page_url, link.get("href")) if link else None
                price_text = card.select_one(".price_color").get_text(strip=True) if card.select_one(".price_color") else None
                rating_node = card.select_one("p.star-rating")
                rating_text = next((c for c in rating_node.get("class", []) if c != "star-rating"), None) if rating_node else None
                availability = card.select_one(".availability").get_text(" ", strip=True) if card.select_one(".availability") else None

                category = None
                if detail_url:
                    detail = get_soup(session, detail_url)
                    crumbs = detail.select("ul.breadcrumb li a")
                    if len(crumbs) >= 2:
                        category = crumbs[-1].get_text(strip=True)

                rows.append({
                    "title": title,
                    "price": price_text,
                    "star_rating": rating_text,
                    "availability": availability,
                    "category": category,
                })

            next_link = soup.select_one("li.next a")
            if page_number < max_pages and next_link:
                page_url = urljoin(page_url, next_link.get("href"))
            else:
                break
    return rows


def clean_data(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No rows were scraped.")

    df["price_gbp"] = pd.to_numeric(
        df["price"].astype(str).str.replace("Â", "", regex=False).str.replace("£", "", regex=False).str.replace(",", "", regex=False),
        errors="coerce",
    )
    df["rating"] = df["star_rating"].map(RATING_MAP)
    df["in_stock"] = df["availability"].astype(str).str.contains("In stock", case=False, na=False)

    numeric_medians = {c: df[c].median() for c in ["price_gbp", "rating"]}
    for col, median in numeric_medians.items():
        df[col] = df[col].fillna(median)

    before = len(df)
    df = df.dropna(subset=["title", "category"]).copy()
    dropped = before - len(df)
    if dropped:
        print(f"Dropped {dropped} rows with unrecoverable title/category values.")

    df["rating"] = df["rating"].astype(int)
    df["price_inr"] = (df["price_gbp"] * GBP_TO_INR).round(2)
    return df[["title", "price_gbp", "price_inr", "rating", "in_stock", "category"]]


def create_database(df: pd.DataFrame) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript("""
        CREATE TABLE categories (
            category_id INTEGER PRIMARY KEY,
            category_name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE books (
            book_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            price_gbp REAL NOT NULL,
            price_inr REAL NOT NULL,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            in_stock INTEGER NOT NULL CHECK(in_stock IN (0, 1)),
            category_id INTEGER NOT NULL,
            FOREIGN KEY(category_id) REFERENCES categories(category_id)
        );
        """)

        categories = pd.DataFrame({"category_name": sorted(df["category"].unique())})
        categories.to_sql("categories", conn, if_exists="append", index=False)
        cat_lookup = pd.read_sql("SELECT category_id, category_name FROM categories", conn)
        merged = df.merge(cat_lookup, left_on="category", right_on="category_name", how="left")
        books = merged[["title", "price_gbp", "price_inr", "rating", "in_stock", "category_id"]].copy()
        books["in_stock"] = books["in_stock"].astype(int)
        books.to_sql("books", conn, if_exists="append", index=False)


def run_queries(df: pd.DataFrame) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    queries = {
        "01_where": "SELECT title, price_gbp, rating FROM books WHERE rating >= 4;",
        "02_order_limit": "SELECT title, price_inr FROM books ORDER BY price_inr DESC LIMIT 10;",
        "03_distinct": "SELECT DISTINCT category_name FROM categories ORDER BY category_name;",
        "04_between": "SELECT title, price_gbp FROM books WHERE price_gbp BETWEEN 20 AND 40 ORDER BY price_gbp;",
        "05_join": "SELECT c.category_name, b.title, b.rating, b.price_inr FROM books b JOIN categories c ON b.category_id = c.category_id ORDER BY b.rating DESC, c.category_name, b.title LIMIT 20;",
    }
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        with (OUTPUT_DIR / "sql_outputs.md").open("w", encoding="utf-8") as f:
            for name, sql in queries.items():
                result = pd.read_sql(sql, conn)
                result.to_csv(OUTPUT_DIR / f"{name}.csv", index=False)
                try:
                    result_markdown = result.to_markdown(index=False)
                except ImportError:
                    result_markdown = result.to_string(index=False)
                f.write(f"## {name}\n\n```sql\n{sql}\n```\n\n{result_markdown}\n\n")

        sql_join = pd.read_sql(queries["05_join"], conn)

    # Two read_sql examples, as required.
    with sqlite3.connect(DB_PATH) as conn:
        top10 = pd.read_sql(queries["02_order_limit"], conn)
        distinct = pd.read_sql(queries["03_distinct"], conn)

    # Reproduce the join directly with in-memory frames using pd.merge.
    cat_df = pd.DataFrame({"category_id": df["category"].factorize(sort=True)[0] + 1, "category_name": df["category"]})
    # Build a stable lookup matching SQLite's category ids.
    cat_lookup = pd.DataFrame({"category_name": sorted(df["category"].unique())})
    cat_lookup["category_id"] = range(1, len(cat_lookup) + 1)
    book_df = df.merge(cat_lookup, left_on="category", right_on="category_name")
    pandas_join = book_df[["category_name", "title", "rating", "price_inr"]].sort_values(["rating", "category_name", "title"], ascending=[False, True, True]).head(20)

    sql_join_norm = sql_join.reset_index(drop=True)
    pandas_join_norm = pandas_join.reset_index(drop=True)
    comparison = sql_join_norm.equals(pandas_join_norm)
    pandas_join.to_csv(OUTPUT_DIR / "05_join_pd_merge.csv", index=False)
    (OUTPUT_DIR / "join_equivalence.txt").write_text(
        f"pd.read_sql JOIN equals pd.merge result: {comparison}\n\nSQL result:\n{sql_join_norm.to_string(index=False)}\n\nPandas merge result:\n{pandas_join_norm.to_string(index=False)}\n",
        encoding="utf-8",
    )
    print(f"pd.read_sql JOIN equals pd.merge result: {comparison}")
    print(f"read_sql examples: {len(top10)} rows and {len(distinct)} categories")


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    rows = scrape_catalogue(max_pages=5)
    df = clean_data(rows)
    if len(df) < 60 or df["category"].nunique() < 3:
        raise RuntimeError(f"Acceptance criteria failed: {len(df)} rows, {df['category'].nunique()} categories")
    df.to_csv(RAW_CSV, index=False)
    create_database(df)
    run_queries(df)
    print(f"Scraped {len(df)} books across {df['category'].nunique()} categories.")
    print(f"Database: {DB_PATH}")


if __name__ == "__main__":
    main()
