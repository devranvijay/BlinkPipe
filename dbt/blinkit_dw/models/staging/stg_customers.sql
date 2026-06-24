with source as (
    select * from {{ source('blinkit_raw', 'raw_customers') }}
)

select
    customer_id,
    trim(name)      as customer_name,
    trim(city)      as city,
    trim(state)     as state,
    cast(tier as integer) as city_tier,
    cast(signup_date as date) as signup_date,
    datediff('day', cast(signup_date as date), current_date) as customer_age_days
from source
where customer_id is not null
