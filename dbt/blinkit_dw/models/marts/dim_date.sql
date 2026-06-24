{{ config(materialized='table') }}

with date_spine as (
    select unnest(generate_series(
        date '2023-01-01',
        date '2026-12-31',
        interval '1 day'
    ))::date as date_day
)

select
    cast(strftime(date_day, '%Y%m%d') as integer)   as date_key,
    date_day,
    extract(year  from date_day)::integer            as year,
    extract(month from date_day)::integer            as month,
    extract(day   from date_day)::integer            as day,
    extract(week  from date_day)::integer            as week_of_year,
    extract(quarter from date_day)::integer          as quarter,
    strftime(date_day, '%B')                         as month_name,
    strftime(date_day, '%A')                         as day_name,
    extract(dow from date_day)::integer              as day_of_week,
    case when extract(dow from date_day) in (0, 6) then true else false end as is_weekend,
    case
        when strftime(date_day, '%m-%d') in (
            '01-26','08-15','10-02','10-24','11-01','12-25'
        ) then true else false
    end as is_holiday,
    date_trunc('month', date_day)::date              as month_start,
    (date_trunc('month', date_day) + interval '1 month' - interval '1 day')::date as month_end
from date_spine
