{{ config(materialized='table') }}

with orders as (
    select * from {{ ref('stg_orders') }}
),

dim_customers as (
    select customer_key, customer_id from {{ ref('dim_customers') }}
),

dim_stores as (
    select store_key, store_id from {{ ref('dim_stores') }}
),

dim_date as (
    select date_key, date_day from {{ ref('dim_date') }}
)

select
    o.order_id,
    dd.date_key,
    dc.customer_key,
    ds.store_key,
    o.city,
    o.status,
    o.total_amount,
    o.delivery_minutes,
    o.is_late,
    o.order_hour,
    o.order_dow,
    o.is_weekend,
    o.created_at,
    o.order_date,

    -- Convenience flags
    case when o.status = 'delivered'  then 1 else 0 end as is_delivered,
    case when o.status = 'cancelled'  then 1 else 0 end as is_cancelled,
    case when o.status = 'returned'   then 1 else 0 end as is_returned,
    case when o.status = 'delivered' and o.delivery_minutes <= 15 then 1 else 0 end as is_express

from orders o
left join dim_customers dc on o.customer_id = dc.customer_id
left join dim_stores     ds on o.store_id   = ds.store_id
left join dim_date       dd on o.order_date = dd.date_day
