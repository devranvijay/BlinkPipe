with source as (
    select * from {{ source('blinkit_raw', 'raw_products') }}
)

select
    product_id,
    trim(name)                          as product_name,
    trim(category)                      as category,
    trim(subcategory)                   as subcategory,
    cast(mrp as decimal(10,2))          as mrp,
    case
        when mrp < 50   then 'Budget'
        when mrp < 150  then 'Mid-range'
        when mrp < 500  then 'Premium'
        else 'Luxury'
    end as price_band
from source
where product_id is not null
