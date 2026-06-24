{{ config(materialized='table') }}

with items as (
    select * from {{ ref('fct_order_items') }}
),

products as (
    select product_key, product_id, product_name, category, subcategory, mrp, price_band
    from {{ ref('dim_products') }}
),

dates as (
    select date_key, date_day, year, month from {{ ref('dim_date') }}
)

select
    d.year,
    d.month,
    p.product_id,
    p.product_name,
    p.category,
    p.subcategory,
    p.mrp,
    p.price_band,

    count(distinct i.order_id)          as orders_containing_product,
    sum(i.qty)                          as total_units_sold,
    round(sum(i.line_total), 2)         as total_revenue,
    round(avg(i.unit_price), 2)         as avg_selling_price,
    round(avg(i.qty), 2)                as avg_qty_per_order,
    round(sum(i.line_total) / nullif(sum(i.qty), 0), 2) as revenue_per_unit,

    dense_rank() over (
        partition by d.year, d.month, p.category
        order by sum(i.line_total) desc
    ) as rank_in_category,

    dense_rank() over (
        partition by d.year, d.month
        order by sum(i.line_total) desc
    ) as overall_rank

from items i
join products p on i.product_key = p.product_key
join dates    d on i.date_key    = d.date_key
where i.status = 'delivered'
group by 1, 2, 3, 4, 5, 6, 7, 8
order by d.year, d.month, overall_rank
