# BlinkPipe — Blinkit-style Data Engineering Platform

End-to-end data platform simulating Blinkit quick-commerce analytics. Generates realistic Indian grocery delivery data, processes it through a 5-layer medallion architecture, and serves live dashboards — fully containerized with Docker Compose.

## Dashboard Preview

| KPI | Value |
|-----|-------|
| Total Orders | 2,78,400 |
| Total GMV | ~₹19.4 Cr |
| Avg Order Value | ₹698.96 |
| Dark Stores | 17 |
| Cities | 10 |
| Days of Data | 30 |

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         Docker Compose                            │
│                                                                   │
│  scripts/generate_orders.py  (Faker · 8,000 orders/day)          │
│            │                                                      │
│            ▼                                                      │
│  ┌──────────────┐  CSV    ┌──────────────────────────┐           │
│  │    MinIO     │◄────────│  raw/  (Bronze layer)     │           │
│  │  :9000/9001  │         │  orders / order_items /   │           │
│  └──────┬───────┘         │  products / customers /   │           │
│         │                 │  stores                   │           │
│         │  Airflow DAG    └──────────────────────────┘           │
│         │  @daily · 6 tasks                                       │
│         ▼                                                         │
│  ┌──────────────┐ Parquet ┌──────────────────────────┐           │
│  │    MinIO     │◄────────│  processed/  (Silver)     │           │
│  │              │         │  cleaned + typed Parquet  │           │
│  └──────┬───────┘         └──────────────────────────┘           │
│         │                                                         │
│         ▼                                                         │
│  ┌──────────────┐         ┌──────────────────────────┐           │
│  │   DuckDB     │◄────────│  raw_* staging tables     │           │
│  │  (embedded)  │   dbt   ├──────────────────────────┤           │
│  │              │◄────────│  dim_* / fct_* / mart_*  │           │
│  └──────┬───────┘         │  (Gold layer)             │           │
│         │                 └──────────────────────────┘           │
│         │  sync_marts_to_postgres                                 │
│         ▼                                                         │
│  ┌──────────────┐                                                 │
│  │  PostgreSQL  │  schema: blinkit_marts                          │
│  └──────┬───────┘                                                 │
│         │                                                         │
│         ▼                                                         │
│  ┌──────────────┐                                                 │
│  │   Metabase   │  10+ charts · KPIs · Trend · Category · Ops    │
│  │    :3000     │                                                 │
│  └──────────────┘                                                 │
└──────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Orchestration | Apache Airflow 2.8 | Daily ETL scheduling & monitoring |
| Data Lake | MinIO (S3-compatible) | Bronze & Silver object storage |
| Warehouse | DuckDB | Embedded OLAP analytics engine |
| Transformation | dbt-duckdb | Dimensional star schema modeling |
| Serving DB | PostgreSQL 15 | Mart export for BI connectivity |
| BI | Metabase v0.49 | Self-serve dashboards |
| Data Simulation | Python + Faker | Realistic Indian quick-commerce data |
| Infrastructure | Docker Compose | Full local deployment |

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/devranvijay/BlinkPipe.git
cd BlinkPipe

# 2. Copy env file and edit if needed
cp .env.example .env

# 3. Start all services
docker-compose up -d

# 4. Wait ~60 seconds for services to be healthy, then generate data
docker exec blinkpipe-airflow-scheduler-1 python3 /opt/airflow/scripts/generate_orders.py

# 5. Trigger the ETL pipeline
# → Open http://localhost:8080  (admin / admin)
# → Enable toggle for: blinkpipe_ingestion
# → Click ▶ to trigger manually

# 6. View dashboards
# → Open http://localhost:3000
# → Connect PostgreSQL: host=postgres, port=5432, db=airflow, user=airflow, pass=airflow
# → Browse blinkit_marts schema
```

## Service Endpoints

| Service | URL | Credentials |
|---------|-----|-------------|
| Airflow | http://localhost:8080 | admin / admin |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin |
| Metabase | http://localhost:3000 | Set on first login |

## Airflow DAG — 6 Tasks

```
extract_from_raw
    → transform_and_load_processed
        → load_to_duckdb_staging
            → run_dbt_models
                → data_quality_checks
                    → sync_marts_to_postgres
```

| Task | What it does |
|------|-------------|
| `extract_from_raw` | Reads CSV files from MinIO `raw/` bucket |
| `transform_and_load_processed` | Cleans, types, deduplicates → writes Parquet to `processed/` |
| `load_to_duckdb_staging` | Loads Parquet into DuckDB `raw_*` staging tables |
| `run_dbt_models` | Runs dbt: staging views → dim/fct tables → mart aggregates |
| `data_quality_checks` | Asserts null rates, duplicates, referential integrity |
| `sync_marts_to_postgres` | Exports mart tables to Postgres `blinkit_marts` schema |

## dbt Star Schema

```
stg_orders ──────────────────────────────► fct_orders ──► mart_daily_sales
stg_customers ──► dim_customers ──────────►               mart_store_performance
stg_products  ──► dim_products  ──► fct_order_items ────► mart_product_rankings
stg_stores    ──► dim_stores    ──────────►
```

**Dimensions:** `dim_customers` · `dim_products` · `dim_stores`
**Facts:** `fct_orders` · `fct_order_items`
**Marts:** `mart_daily_sales` · `mart_store_performance` · `mart_product_rankings`

## Project Structure

```
BlinkPipe/
├── docker-compose.yml              # 5-service stack
├── .env.example                    # Config template (copy to .env)
├── docker/
│   └── airflow/
│       ├── Dockerfile              # Airflow + Python 3.11 + dbt
│       └── requirements.txt        # pip deps
├── dags/
│   └── ingestion_dag.py            # Main ETL DAG (TaskFlow API)
├── scripts/
│   ├── generate_orders.py          # Faker-based data generator
│   ├── schema.py                   # Reference data: cities, stores, products
│   └── validate_raw.py             # DuckDB sanity checks
└── dbt/blinkit_dw/
    ├── dbt_project.yml
    ├── profiles.yml
    ├── macros/
    │   └── generate_schema_name.sql
    └── models/
        ├── staging/                # stg_* views
        └── marts/                  # dim_* · fct_* · mart_*
```

## Data Model

- **10 Indian cities** — Mumbai, Delhi, Bengaluru, Hyderabad, Chennai, Kolkata, Pune, Ahmedabad, Jaipur, Lucknow
- **17 dark stores** (DS001–DS017)
- **40 SKUs** across 8 categories (Dairy, Beverages, Snacks, Staples, Personal Care…)
- **~8,000 orders/day** with realistic peak-hour & weekend patterns
- **Customer tiers** — Gold, Silver, Bronze with order behavior variation

## Resume Bullet

> Built **BlinkPipe**, an end-to-end data engineering platform processing 8,000+ daily quick-commerce orders through a 5-layer medallion architecture: MinIO data lake → Apache Airflow ETL → DuckDB OLAP warehouse → dbt star schema (3 dims, 2 facts, 3 marts) → Metabase dashboards. Includes automated data quality checks and full Docker Compose deployment.
