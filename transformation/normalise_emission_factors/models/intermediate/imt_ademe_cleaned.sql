with ademe as (
    select *
    from {{ref('stg_ademe')}}
),
translations as (
    select * from {{ref('ademe_translations')}}
),
joined as (
    select 
    a.*,
    t.factor_name_en
    from ademe a
    left join translations t
    on t.factor_name_fr = a.factor_name
),
ademe_cleaned as (
    select
        *,
        coalesce(factor_name_en, factor_name) as factor_name_standardised,
        case
            when regexp_matches(
                lower(coalesce(factor_name_en, factor_name)),
                '\(k(?:gco2e|ge?c)/'
            )
                then gco2e_per_unit * 1000
            else gco2e_per_unit
        end as gCO2e_per_unit_normalised
    from joined
)

select
    id,
    regexp_replace(factor_name_standardised, '\s*\([^)]*\)\s*$', '') as factor_name,
    'Cradle-to-gate GHG emissions from the production of '
        || regexp_replace(lower(substr(factor_name_standardised,1,1)) || substr(factor_name_standardised, 2), '\s*\([^)]*\)\s*$', '') as description,
    gCO2e_per_unit_normalised as gCO2e_per_unit,
    unit,
    ghg_scope,
    country_code,
    source,
    source_year,
    valid_from,
    valid_to,
    uncertainty_pct,
    sport_federation_code
from ademe_cleaned