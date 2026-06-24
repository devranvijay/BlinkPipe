with source as (
    select * from {{ source('blinkit_raw', 'raw_orders') }}
),

cleaned as (
    select
        order_id,
        customer_id,
        store_id,
        city,
        cast(created_at as timestamp)   as created_at,
        cast(date as date)              as order_date,
        lower(trim(status))             as status,
        cast(total_amount as decimal(12,2))     as total_amount,
        cast(delivery_minutes as integer)       as delivery_minutes,
        cast(is_late as boolean)                as is_late,

        -- Derived
        extract(hour from cast(created_at as timestamp))   as order_hour,
        extract(dow  from cast(created_at as timestamp))   as order_dow,
        case
            when extract(dow from cast(created_at as timestamp)) in (0, 6) then true
            else false
        end as is_weekend
    from source
    where order_id is not null
      and customer_id is not null
      and total_amount > 0
)

select * from cleaned
