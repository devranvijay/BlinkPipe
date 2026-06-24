"""
Blinkit data generator — produces realistic quick-commerce transactions
and uploads them to MinIO raw/ bucket as date-partitioned CSV files.

Usage:
    python generate_orders.py --days 30 --base-orders 8000
    python generate_orders.py --days 30 --local-only   # skip MinIO upload
"""

import argparse
import io
import os
import random
import string
import sys
from datetime import datetime, timedelta

import boto3
import pandas as pd
from botocore.client import Config
from faker import Faker

sys.path.insert(0, os.path.dirname(__file__))
from schema import (
    CITIES, DARK_STORES, PRODUCTS,
    ORDER_STATUSES, HOURLY_WEIGHTS, WEEKDAY_MULTIPLIER,
)

fake = Faker("en_IN")
random.seed(42)

MINIO_ENDPOINT  = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS    = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET    = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
RAW_BUCKET      = "raw"


def get_s3():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS,
        aws_secret_access_key=MINIO_SECRET,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def rand_id(prefix, n=8):
    return prefix + "".join(random.choices(string.ascii_uppercase + string.digits, k=n))


def build_customers(n=5000):
    rows = []
    for _ in range(n):
        city_rec = random.choice(CITIES)
        signup   = fake.date_between(start_date="-2y", end_date="-30d")
        rows.append({
            "customer_id":  rand_id("C"),
            "name":         fake.name(),
            "phone":        fake.phone_number(),
            "city":         city_rec["city"],
            "tier":         city_rec["tier"],
            "state":        city_rec["state"],
            "signup_date":  str(signup),
        })
    return pd.DataFrame(rows)


def build_products():
    return pd.DataFrame(PRODUCTS)


def build_stores():
    return pd.DataFrame(DARK_STORES)


def generate_orders_for_day(date, customers_df, stores_df, base_orders=8000):
    weekday_mult  = WEEKDAY_MULTIPLIER[date.weekday()]
    daily_target  = int(base_orders * weekday_mult)
    store_ids     = stores_df["store_id"].tolist()
    city_store    = stores_df.set_index("store_id")["city"].to_dict()

    orders, items = [], []

    for _ in range(daily_target):
        hour       = random.choices(range(24), weights=HOURLY_WEIGHTS)[0]
        minute     = random.randint(0, 59)
        second     = random.randint(0, 59)
        created_at = datetime(date.year, date.month, date.day, hour, minute, second)

        store_id   = random.choice(store_ids)
        cust       = customers_df.sample(1).iloc[0]
        status     = random.choice(ORDER_STATUSES)

        delivery_min = None
        if status == "delivered":
            delivery_min = random.randint(8, 35)
        elif status in ("cancelled", "returned"):
            delivery_min = None

        order_id = rand_id("ORD")
        n_items  = random.choices([1, 2, 3, 4, 5], weights=[30, 30, 20, 12, 8])[0]
        products = random.sample(PRODUCTS, n_items)

        total = 0.0
        for prod in products:
            qty        = random.randint(1, 3)
            unit_price = round(prod["mrp"] * random.uniform(0.85, 1.0), 2)
            line_total = round(qty * unit_price, 2)
            total     += line_total
            items.append({
                "order_item_id": rand_id("OI"),
                "order_id":      order_id,
                "product_id":    prod["product_id"],
                "qty":           qty,
                "unit_price":    unit_price,
                "line_total":    line_total,
                "date":          str(date),
            })

        orders.append({
            "order_id":        order_id,
            "customer_id":     cust["customer_id"],
            "store_id":        store_id,
            "city":            city_store[store_id],
            "created_at":      created_at.isoformat(),
            "status":          status,
            "total_amount":    round(total, 2),
            "delivery_minutes": delivery_min,
            "is_late":         (delivery_min or 0) > 25,
            "date":            str(date),
        })

    return pd.DataFrame(orders), pd.DataFrame(items)


def upload_to_minio(s3, df, bucket, key):
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    s3.put_object(Bucket=bucket, Key=key, Body=buf.getvalue().encode("utf-8"))
    print(f"  Uploaded s3://{bucket}/{key}  ({len(df):,} rows)")


def save_locally(df, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"  Saved {path}  ({len(df):,} rows)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days",         type=int,  default=30)
    parser.add_argument("--base-orders",  type=int,  default=8000)
    parser.add_argument("--local-only",   action="store_true")
    args = parser.parse_args()

    print("Building reference tables...")
    customers = build_customers(n=5000)
    products  = build_products()
    stores    = build_stores()

    s3 = None if args.local_only else get_s3()

    if not args.local_only:
        upload_to_minio(s3, customers, RAW_BUCKET, "customers/customers.csv")
        upload_to_minio(s3, products,  RAW_BUCKET, "products/products.csv")
        upload_to_minio(s3, stores,    RAW_BUCKET, "stores/stores.csv")
    else:
        save_locally(customers, "data/raw/customers/customers.csv")
        save_locally(products,  "data/raw/products/products.csv")
        save_locally(stores,    "data/raw/stores/stores.csv")

    end_date   = datetime.today().date() - timedelta(days=1)
    start_date = end_date - timedelta(days=args.days - 1)
    current    = start_date

    print(f"\nGenerating {args.days} days of orders ({start_date} → {end_date})...")
    while current <= end_date:
        ds = current.strftime("%Y/%m/%d")
        orders_df, items_df = generate_orders_for_day(current, customers, stores, args.base_orders)

        if not args.local_only:
            upload_to_minio(s3, orders_df, RAW_BUCKET, f"orders/{ds}/orders.csv")
            upload_to_minio(s3, items_df,  RAW_BUCKET, f"order_items/{ds}/order_items.csv")
        else:
            save_locally(orders_df, f"data/raw/orders/{ds}/orders.csv")
            save_locally(items_df,  f"data/raw/order_items/{ds}/order_items.csv")

        total_orders = len(orders_df)
        total_rev    = orders_df["total_amount"].sum()
        print(f"  {current}  orders={total_orders:,}  GMV=₹{total_rev:,.0f}")
        current += timedelta(days=1)

    print("\nData generation complete.")


if __name__ == "__main__":
    main()
