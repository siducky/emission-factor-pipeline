with source as (
    select * from {{ source('bronze', 'nve') }}
),
renamed as (
    select
        uuid() as id,
        'Electricity - grid mix' as factor_name,
        cast(concat(factor_type, ' Electricity grid mix emission factor for Norway') as varchar) as description,
        cast(co2_per_kWh as double precision) as gCO2e_per_unit,
        'kWh' as unit,
        'Scope 2' as ghg_scope,
        'NO' as country_code,
        'nve' as source,
        cast(year as integer) as source_year,
        make_date(year, 1, 1) as valid_from,
        make_date(year, 12, 31) as valid_to
    from source
)

select * from renamed