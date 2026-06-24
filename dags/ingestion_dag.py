"""
BlinkPipe — Main ETL DAG
Schedule: daily at midnight
Flow: MinIO raw/ → clean + transform → MinIO processed/ → DuckDB staging → dbt run → DQ checks
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta

import duckdb
import pandas as pd
import boto3
import io
from botocore.client import Config
from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.utils.dates import days_ago

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS   = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
MINIO_SECRET   = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
DUCKDB_PATH    = os.getenv("DUCKDB_PATH", "/opt/airflow/data/blinkit.db")
DBT_PROJECT    = "/opt/airflow/dbt/blinkit_dw"

default_args = {
    "owner":            "blinkpipe",
    "retries":          2,
    "retry_delay":      timedelta(minutes=5),
    "email_on_failure": False,
}


def _s3():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS,
        aws_secret_access_key=MINIO_SECRET,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def _duckdb():
    con = duckdb.connect(DUCKDB_PATH)
    con.execute("INSTALL httpfs; LOAD httpfs;")
    host = MINIO_ENDPOINT.replace("http://", "").replace("https://", "")
    use_ssl = "true" if MINIO_ENDPOINT.startswith("https") else "false"
    con.execute(f"""
        SET s3_endpoint='{host}';
        SET s3_use_ssl={use_ssl};
        SET s3_url_style='path';
        SET s3_access_key_id='{MINIO_ACCESS}';
        SET s3_secret_access_key='{MINIO_SECRET}';
    """)
    return con


@dag(
    dag_id="blinkpipe_ingestion",
    schedule="@daily",
    start_date=days_ago(30),
    catchup=True,
    max_active_runs=1,
    default_args=default_args,
    tags=["blinkpipe", "etl"],
    doc_md="""
    ### BlinkPipe Daily Ingestion
    Reads CSV files from MinIO `raw/`, cleans, transforms, writes Parquet to `processed/`,
    loads into DuckDB staging, runs dbt models, and runs data quality checks.
    """,
)
def blinkpipe_ingestion():

    # ── Task 1: Extract ──────────────────────────────────────────────────────
    @task(task_id="extract_from_raw")
    def extract_from_raw(ds: str = None, **ctx):
        """Read CSV files for {{ ds }} from MinIO raw/ bucket."""
        date_path = ds.replace("-", "/")  # 2024-01-15 → 2024/01/15
        s3  = _s3()
        out = {}

        for table in ("orders", "order_items"):
            key = f"{table}/{date_path}/{table}.csv"
            try:
                obj  = s3.get_object(Bucket="raw", Key=key)
                body = obj["Body"].read().decode("utf-8")
                df   = pd.read_csv(io.StringIO(body))
                out[table] = {"rows": len(df), "key": key}
                print(f"  Extracted {table}: {len(df):,} rows from raw/{key}")
            except s3.exceptions.NoSuchKey:
                print(f"  WARN: No file at raw/{key} — skipping {table} for {ds}")
                out[table] = {"rows": 0, "key": key}

        # Reference tables (static — load only if not already in DuckDB)
        for table in ("products", "customers", "stores"):
            try:
                key = f"{table}/{table}.csv"
                obj  = s3.get_object(Bucket="raw", Key=key)
                body = obj["Body"].read().decode("utf-8")
                df   = pd.read_csv(io.StringIO(body))
                out[table] = {"rows": len(df), "key": key}
                print(f"  Extracted {table}: {len(df):,} rows")
            except Exception:
                out[table] = {"rows": 0, "key": ""}

        return json.dumps(out)

    # ── Task 2: Transform + write processed/ ─────────────────────────────────
    @task(task_id="transform_and_load_processed")
    def transform_and_load_processed(extract_info_json: str, ds: str = None, **ctx):
        """Clean data and write Parquet to MinIO processed/."""
        extract_info = json.loads(extract_info_json)
        date_path    = ds.replace("-", "/")
        s3           = _s3()
        results      = {}

        # ── Orders ────────────────────────────────────────────────────────────
        if extract_info.get("orders", {}).get("rows", 0) > 0:
            obj  = s3.get_object(Bucket="raw", Key=extract_info["orders"]["key"])
            df   = pd.read_csv(io.StringIO(obj["Body"].read().decode("utf-8")))

            df["created_at"]      = pd.to_datetime(df["created_at"], errors="coerce")
            df["total_amount"]    = pd.to_numeric(df["total_amount"], errors="coerce")
            df["delivery_minutes"]= pd.to_numeric(df["delivery_minutes"], errors="coerce")
            df["is_late"]         = df["is_late"].astype(bool)
            df = df.dropna(subset=["order_id", "customer_id", "store_id", "created_at"])
            df = df.drop_duplicates(subset=["order_id"])

            buf = io.BytesIO()
            df.to_parquet(buf, index=False, compression="snappy")
            s3.put_object(Bucket="processed", Key=f"orders/{date_path}/orders.parquet", Body=buf.getvalue())
            results["orders"] = len(df)
            print(f"  Processed orders: {len(df):,} rows → processed/orders/{date_path}/")

        # ── Order Items ───────────────────────────────────────────────────────
        if extract_info.get("order_items", {}).get("rows", 0) > 0:
            obj  = s3.get_object(Bucket="raw", Key=extract_info["order_items"]["key"])
            df   = pd.read_csv(io.StringIO(obj["Body"].read().decode("utf-8")))

            df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
            df["line_total"] = pd.to_numeric(df["line_total"], errors="coerce")
            df["qty"]        = pd.to_numeric(df["qty"], errors="coerce").astype("Int64")
            df = df.dropna(subset=["order_item_id", "order_id", "product_id"])
            df = df.drop_duplicates(subset=["order_item_id"])

            buf = io.BytesIO()
            df.to_parquet(buf, index=False, compression="snappy")
            s3.put_object(Bucket="processed", Key=f"order_items/{date_path}/order_items.parquet", Body=buf.getvalue())
            results["order_items"] = len(df)
            print(f"  Processed order_items: {len(df):,} rows")

        # ── Reference tables (write to processed/ on first run) ───────────────
        for table in ("products", "customers", "stores"):
            if extract_info.get(table, {}).get("rows", 0) > 0:
                obj = s3.get_object(Bucket="raw", Key=extract_info[table]["key"])
                df  = pd.read_csv(io.StringIO(obj["Body"].read().decode("utf-8")))
                buf = io.BytesIO()
                df.to_parquet(buf, index=False, compression="snappy")
                s3.put_object(Bucket="processed", Key=f"{table}/{table}.parquet", Body=buf.getvalue())
                results[table] = len(df)
                print(f"  Processed {table}: {len(df):,} rows")

        return json.dumps(results)

    # ── Task 3: Load into DuckDB staging ─────────────────────────────────────
    @task(task_id="load_to_duckdb_staging")
    def load_to_duckdb_staging(processed_info_json: str, ds: str = None, **ctx):
        """Load Parquet files from processed/ into DuckDB staging tables."""
        processed_info = json.loads(processed_info_json)
        date_path      = ds.replace("-", "/")
        con            = _duckdb()

        # Ensure staging tables exist
        con.execute("""
            CREATE TABLE IF NOT EXISTS raw_orders (
                order_id VARCHAR, customer_id VARCHAR, store_id VARCHAR, city VARCHAR,
                created_at TIMESTAMP, status VARCHAR, total_amount DOUBLE,
                delivery_minutes INTEGER, is_late BOOLEAN, date DATE
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS raw_order_items (
                order_item_id VARCHAR, order_id VARCHAR, product_id VARCHAR,
                qty INTEGER, unit_price DOUBLE, line_total DOUBLE, date DATE
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS raw_products (
                product_id VARCHAR, name VARCHAR, category VARCHAR,
                subcategory VARCHAR, mrp DOUBLE
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS raw_customers (
                customer_id VARCHAR, name VARCHAR, phone VARCHAR,
                city VARCHAR, tier INTEGER, state VARCHAR, signup_date DATE
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS raw_stores (
                store_id VARCHAR, city VARCHAR, zone VARCHAR,
                lat DOUBLE, lon DOUBLE
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                run_date DATE, table_name VARCHAR, rows_loaded INTEGER,
                check_name VARCHAR, status VARCHAR, message VARCHAR,
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        loaded = {}

        # Orders
        try:
            con.execute(f"DELETE FROM raw_orders WHERE date = '{ds}'")
            n = con.execute(f"""
                INSERT INTO raw_orders
                SELECT * FROM read_parquet('s3://processed/orders/{date_path}/orders.parquet')
            """).rowcount
            loaded["raw_orders"] = n
            print(f"  Loaded raw_orders: {n:,} rows for {ds}")
        except Exception as e:
            print(f"  WARN raw_orders: {e}")

        # Order Items
        try:
            con.execute(f"DELETE FROM raw_order_items WHERE date = '{ds}'")
            n = con.execute(f"""
                INSERT INTO raw_order_items
                SELECT * FROM read_parquet('s3://processed/order_items/{date_path}/order_items.parquet')
            """).rowcount
            loaded["raw_order_items"] = n
        except Exception as e:
            print(f"  WARN raw_order_items: {e}")

        # Reference tables — UPSERT (truncate and reload)
        for table in ("products", "customers", "stores"):
            try:
                con.execute(f"DELETE FROM raw_{table}")
                n = con.execute(f"""
                    INSERT INTO raw_{table}
                    SELECT * FROM read_parquet('s3://processed/{table}/{table}.parquet')
                """).rowcount
                loaded[f"raw_{table}"] = n
                print(f"  Loaded raw_{table}: {n:,} rows")
            except Exception as e:
                print(f"  WARN raw_{table}: {e}")

        con.close()
        return json.dumps(loaded)

    # ── Task 4: Run dbt models ────────────────────────────────────────────────
    @task(task_id="run_dbt_models")
    def run_dbt_models(ds: str = None, **ctx):
        import subprocess
        cmds = [
            f"cd {DBT_PROJECT} && dbt deps --profiles-dir .",
            f"cd {DBT_PROJECT} && dbt run --profiles-dir . --vars '{{\"run_date\": \"{ds}\"}}'",
            f"cd {DBT_PROJECT} && dbt test --profiles-dir . --store-failures",
        ]
        for cmd in cmds:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            print(result.stdout[-3000:] if len(result.stdout) > 3000 else result.stdout)
            if result.returncode != 0:
                print(result.stderr[-2000:])
                raise RuntimeError(f"dbt command failed (exit {result.returncode}): {cmd}")
        return f"dbt run complete for {ds}"

    # ── Task 5: Data quality checks ───────────────────────────────────────────
    @task(task_id="data_quality_checks")
    def data_quality_checks(loaded_info_json: str, ds: str = None, **ctx):
        """Assert row counts, null rates, and referential integrity."""
        loaded = json.loads(loaded_info_json)
        if loaded.get("raw_orders", 0) == 0:
            print(f"  No orders loaded for {ds} — skipping DQ checks")
            return f"DQ skipped for {ds}: no data for this date"
        con    = _duckdb()
        passed, failed = 0, 0

        def assert_check(name, sql, condition_fn):
            nonlocal passed, failed
            try:
                result = con.execute(sql).fetchone()[0]
                ok     = condition_fn(result)
                status = "PASS" if ok else "FAIL"
                if not ok:
                    failed += 1
                    print(f"  FAIL — {name}: value={result}")
                else:
                    passed += 1
                con.execute(
                    "INSERT INTO audit_log (run_date, table_name, rows_loaded, check_name, status, message) VALUES (?,?,?,?,?,?)",
                    [ds, name.split(":")[0].strip(), loaded.get("raw_orders", 0), name, status, str(result)]
                )
            except Exception as e:
                failed += 1
                print(f"  ERROR — {name}: {e}")

        assert_check(
            "raw_orders: no nulls on order_id",
            f"SELECT COUNT(*) FROM raw_orders WHERE order_id IS NULL AND date='{ds}'",
            lambda v: v == 0
        )
        assert_check(
            "raw_orders: positive total_amount",
            f"SELECT COUNT(*) FROM raw_orders WHERE total_amount <= 0 AND date='{ds}'",
            lambda v: v == 0
        )
        assert_check(
            "raw_orders: no duplicate order_ids",
            f"SELECT COUNT(*)-COUNT(DISTINCT order_id) FROM raw_orders WHERE date='{ds}'",
            lambda v: v == 0
        )
        assert_check(
            "raw_order_items: referential integrity",
            f"""
                SELECT COUNT(*) FROM raw_order_items oi
                LEFT JOIN raw_orders o ON oi.order_id = o.order_id
                WHERE o.order_id IS NULL AND oi.date='{ds}'
            """,
            lambda v: v == 0
        )
        assert_check(
            "raw_orders: min daily rows",
            f"SELECT COUNT(*) FROM raw_orders WHERE date='{ds}'",
            lambda v: int(v) >= 100
        )

        con.close()
        summary = f"DQ complete for {ds}: {passed} passed, {failed} failed"
        print(f"\n  {summary}")
        if failed > 0:
            raise ValueError(f"Data quality checks failed: {failed} failures")
        return summary

    # ── Task 6: Sync DuckDB marts → Postgres (for Metabase) ──────────────────
    @task(task_id="sync_marts_to_postgres")
    def sync_marts_to_postgres(ds: str = None, **ctx):
        """Copy DuckDB mart tables into Postgres blinkit_marts schema so Metabase can read them."""
        import duckdb
        from sqlalchemy import create_engine, text

        POSTGRES_CONN = "postgresql+psycopg2://airflow:airflow@postgres/airflow"
        pg = create_engine(POSTGRES_CONN)

        with pg.begin() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS blinkit_marts"))

        con = duckdb.connect(DUCKDB_PATH, read_only=True)

        MARTS = [
            ("marts", "mart_daily_sales"),
            ("marts", "mart_store_performance"),
            ("marts", "mart_product_rankings"),
            ("marts", "dim_customers"),
            ("marts", "dim_products"),
            ("marts", "dim_stores"),
            ("marts", "fct_orders"),
        ]

        synced = []
        for schema, table in MARTS:
            try:
                df = con.execute(f'SELECT * FROM "{schema}"."{table}"').fetchdf()
                df.to_sql(table, pg, schema="blinkit_marts", if_exists="replace", index=False, chunksize=10000)
                print(f"  Synced {table}: {len(df):,} rows → Postgres blinkit_marts")
                synced.append(table)
            except Exception as e:
                print(f"  WARN skipping {table}: {e}")

        con.close()
        return f"Synced {len(synced)} marts to Postgres for {ds}"

    # ── Wire tasks ─────────────────────────────────────────────────────────
    extracted  = extract_from_raw()
    processed  = transform_and_load_processed(extracted)
    loaded     = load_to_duckdb_staging(processed)
    dbt_run    = run_dbt_models()
    dq         = data_quality_checks(loaded)
    sync_pg    = sync_marts_to_postgres()

    loaded >> dbt_run >> dq >> sync_pg


blinkpipe_ingestion()
