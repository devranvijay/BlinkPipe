{{ config(materialized='table') }}

with stores as (
    select * from {{ ref('stg_stores') }}
),

city_info as (
    select distinct city,
        case city
            when 'Mumbai'    then 1 when 'Delhi'     then 1
            when 'Bangalore' then 1 when 'Hyderabad' then 1
            when 'Chennai'   then 1 when 'Pune'      then 1
            else 2
        end as city_tier
    from stores
)

select
    {{ dbt_utils.generate_surrogate_key(['s.store_id']) }} as store_key,
    s.store_id,
    s.city,
    s.zone,
    s.latitude,
    s.longitude,
    c.city_tier
from stores s
left join city_info c on s.city = c.city
