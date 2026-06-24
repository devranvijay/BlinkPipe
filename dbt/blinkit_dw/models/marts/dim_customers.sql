{{ config(materialized='table') }}

with customers as (
    select * from {{ ref('stg_customers') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['customer_id']) }} as customer_key,
    customer_id,
    customer_name,
    city,
    state,
    city_tier,
    signup_date,
    customer_age_days,
    case
        when customer_age_days < 30  then 'New'
        when customer_age_days < 180 then 'Growing'
        when customer_age_days < 365 then 'Established'
        else 'Loyal'
    end as customer_segment
from customers
