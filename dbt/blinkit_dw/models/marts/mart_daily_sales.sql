{{ config(materialized='table') }}

with orders as (
    select * from {{ ref('fct_orders') }}
),

dates as (
    select date_key, date_day, year, month, week_of_year, is_weekend
    from {{ ref('dim_date') }}
)

select
    d.date_day,
    d.year,
    d.month,
    d.week_of_year,
    d.is_weekend,
    o.city,

    count(o.order_id)                                               as total_orders,
    count(case when o.status = 'delivered' then 1 end)             as delivered_orders,
    count(case when o.status = 'cancelled' then 1 end)             as cancelled_orders,
    count(case when o.status = 'returned'  then 1 end)             as returned_orders,
    count(distinct o.customer_key)                                 as unique_customers,

    round(sum(o.total_amount), 2)                                  as total_gmv,
    round(sum(case when o.status = 'delivered' then o.total_amount else 0 end), 2) as net_revenue,
    round(avg(o.total_amount), 2)                                  as avg_order_value,
    round(avg(case when o.status = 'delivered' then o.delivery_minutes end), 1) as avg_delivery_minutes,
    round(
        count(case when o.status = 'cancelled' then 1 end) * 100.0 / nullif(count(o.order_id), 0),
        2
    ) as cancellation_rate_pct,
    round(
        count(case when o.is_late then 1 end) * 100.0 / nullif(count(case when o.status='delivered' then 1 end), 0),
        2
    ) as late_delivery_rate_pct

from orders o
join dates d on o.date_key = d.date_key
group by 1, 2, 3, 4, 5, 6
order by d.date_day desc, o.city
