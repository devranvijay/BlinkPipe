with source as (
    select * from {{ source('blinkit_raw', 'raw_order_items') }}
)

select
    order_item_id,
    order_id,
    product_id,
    cast(qty as integer)              as qty,
    cast(unit_price as decimal(10,2)) as unit_price,
    cast(line_total as decimal(12,2)) as line_total,
    cast(date as date)                as order_date
from source
where order_item_id is not null
  and order_id is not null
  and qty > 0
