"""
Quick sanity check on raw data via DuckDB — reads CSVs from MinIO
and prints baseline metrics before any pipeline runs.
Run this after generate_orders.py.
"""

import os
import duckdb

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS   = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET   = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
DUCKDB_PATH    = os.getenv("DUCKDB_PATH", ":memory:")

con = duckdb.connect(DUCKDB_PATH)
con.execute("INSTALL httpfs; LOAD httpfs;")
con.execute(f"""
    SET s3_endpoint='{MINIO_ENDPOINT.replace("http://", "")}';
    SET s3_use_ssl=false;
    SET s3_url_style='path';
    SET s3_access_key_id='{MINIO_ACCESS}';
    SET s3_secret_access_key='{MINIO_SECRET}';
""")

queries = {
    "Orders — date range & count": """
        SELECT
            COUNT(*)            AS total_orders,
            MIN(created_at)     AS earliest,
            MAX(created_at)     AS latest,
            COUNT(DISTINCT store_id)    AS distinct_stores,
            COUNT(DISTINCT customer_id) AS distinct_customers,
            ROUND(AVG(total_amount), 2) AS avg_order_value,
            SUM(total_amount)           AS total_gmv
        FROM read_csv_auto('s3://raw/orders/*/*/*.csv')
    """,
    "Orders — status distribution": """
        SELECT status, COUNT(*) AS cnt,
               ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER(), 1) AS pct
        FROM read_csv_auto('s3://raw/orders/*/*/*.csv')
        GROUP BY status ORDER BY cnt DESC
    """,
    "Order items — null check": """
        SELECT
            COUNT(*) AS total_rows,
            SUM(CASE WHEN order_id   IS NULL THEN 1 ELSE 0 END) AS null_order_id,
            SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END) AS null_product_id,
            SUM(CASE WHEN qty        IS NULL THEN 1 ELSE 0 END) AS null_qty
        FROM read_csv_auto('s3://raw/order_items/*/*/*.csv')
    """,
    "Category GMV distribution": """
        SELECT p.category,
               COUNT(*)              AS line_items,
               ROUND(SUM(oi.line_total), 0) AS gmv
        FROM read_csv_auto('s3://raw/order_items/*/*/*.csv') oi
        JOIN read_csv_auto('s3://raw/products/products.csv') p
          ON oi.product_id = p.product_id
        GROUP BY p.category ORDER BY gmv DESC
    """,
}

for title, sql in queries.items():
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print('─'*60)
    try:
        result = con.execute(sql).fetchdf()
        print(result.to_string(index=False))
    except Exception as e:
        print(f"  ERROR: {e}")

print("\nValidation complete.")
