with source as (
    select * from {{ source('bronze', 'defra') }}
    where "GHG/Unit" = 'kg CO2e'
      and "GHG Conversion Factor" is not null
),

renamed as (
    select
        uuid() as id,
        cast("Level 3" as varchar) as factor_name,
        round(cast("GHG Conversion Factor" as double precision), 3) * 1000.0 as gCO2e_per_unit,
        cast(uom as varchar) as unit,
        cast(scope as varchar) as ghg_scope,
        'GLOBAL' as country_code,
        'defra' as source,
        cast(year as integer) as source_year,
        make_date(cast(year as integer), 1, 1) as valid_from,
        make_date(cast(year as integer), 12, 31) as valid_to,
        cast("Level 2" as varchar) as sub_category,
        cast("Level 1" as varchar) as category,
        cast("Level 4" as varchar) as sub_sub_category,
        cast("Column Text" as varchar) as column_text
    from source
)

select * from renamed