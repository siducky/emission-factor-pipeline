with nve as (
    select
    *
    from {{ref('stg_nve')}}
),
nve_cleaned as (
    select
    id,
    factor_name,
    concat('GHG Emission factor for ', factor_name, ' beloning to category Energy') as description,
    gCO2e_per_unit,
    unit,
    ghg_scope,
    country_code,
    source,
    source_year,
    valid_from,
    valid_to
    from nve
)
select * from nve_cleaned
