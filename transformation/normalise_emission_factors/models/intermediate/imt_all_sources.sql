with defra as (
    select
        id, factor_name, description, gCO2e_per_unit, unit, ghg_scope,
        country_code, source, source_year, valid_from, valid_to,
        sub_category, category,
        cast(null as double) as uncertainty_pct,
    from {{ ref('imt_defra_cleaned') }}
),

nve as (
    select
        id, factor_name, description, gCO2e_per_unit, unit, ghg_scope,
        country_code, source, source_year, valid_from, valid_to,
        'Electricity' as sub_category,
        'Energy' as category,
        cast(null as double) as uncertainty_pct
    from {{ ref('imt_nve_cleaned') }}
),

ademe as (
    select
        id, factor_name, description, gCO2e_per_unit, unit, ghg_scope,
        country_code, source, source_year, valid_from, valid_to,
        'Sports Equipment' as sub_category,
        'Materials' as category,
        uncertainty_pct
    from {{ ref('imt_ademe_cleaned') }}
)

select * from defra
union all
select * from nve
union all
select * from ademe
