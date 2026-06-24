{{ config(materialized='table') }}

with orders as (
    select * from {{ ref('fct_orders') }}
),

stores as (
    select store_key, store_id, city, zone, city_tier
    from {{ ref('dim_stores') }}
),

dates as (
    select date_key, date_day from {{ ref('dim_date') }}
)

select
    d.date_day,
    s.store_id,
    s.city,
    s.zone,
    s.city_tier,

    count(o.order_id)                                           as total_orders,
    count(case when o.status = 'delivered' then 1 end)         as delivered_orders,
    count(case when o.status = 'cancelled' then 1 end)         as cancelled_orders,
    count(distinct o.customer_key)                             as unique_customers,

    round(sum(o.total_amount), 2)                              as total_gmv,
    round(avg(o.total_amount), 2)                              as avg_order_value,
    round(avg(case when o.status='delivered' then o.delivery_minutes end), 1) as avg_delivery_minutes,
    round(
        count(case when o.is_late then 1 end) * 100.0 / nullif(count(case when o.status='delivered' then 1 end), 0),
        2
    ) as late_pct,
    round(
        count(case when o.status = 'cancelled' then 1 end) * 100.0 / nullif(count(o.order_id), 0),
        2
    ) as cancellation_pct,

    -- Peak hour (mode of order_hour for delivered orders)
    mode() within group (order by o.order_hour) as peak_hour

from orders o
join stores s on o.store_key = s.store_key
join dates  d on o.date_key  = d.date_key
group by 1, 2, 3, 4, 5
order by d.date_day desc, total_gmv desc
