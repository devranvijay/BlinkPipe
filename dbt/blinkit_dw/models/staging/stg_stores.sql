with source as (
    select * from {{ source('blinkit_raw', 'raw_stores') }}
)

select
    store_id,
    trim(city) as city,
    trim(zone) as zone,
    cast(lat as double) as latitude,
    cast(lon as double) as longitude
from source
where store_id is not null
