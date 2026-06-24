{{ config(materialized='table') }}

with items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select order_id, customer_key, store_key, date_key, city, status
    from {{ ref('fct_orders') }}
),

dim_products as (
    select product_key, product_id from {{ ref('dim_products') }}
)

select
    i.order_item_id,
    i.order_id,
    o.date_key,
    o.customer_key,
    o.store_key,
    p.product_key,
    o.city,
    o.status,
    i.qty,
    i.unit_price,
    i.line_total,
    i.order_date,
    round(i.line_total / nullif(i.qty, 0), 2) as effective_unit_price
from items i
left join orders      o on i.order_id   = o.order_id
left join dim_products p on i.product_id = p.product_id
