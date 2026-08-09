with source as (
    select * from {{ ref('imt_all_sources') }}
),

prepared as (
    select
        -- Stable surrogate key computed in staging (source + real identifiers + year).
        -- Deterministic across re-runs -> idempotent Gold loads.
        id,
        source,
        coalesce(factor_name, sub_category) as factor_name,
        description,
        gCO2e_per_unit,
        unit,
        ghg_scope,
        category,
        sub_category,
        country_code,
        source_year,
        valid_from,
        valid_to,
        coalesce(uncertainty_pct, 0) as uncertainty_pct
    from source
),

flagged as (
    select
        *,
        -- Temporal: flag the latest published edition of each factor
        -- (per source + factor_name) as current, regardless of whether
        -- its valid_to has passed. Source of truth for "usable now"
        -- remains valid_from/valid_to (convenience flag per rule #2).
        row_number() over (
            partition by source, factor_name, unit
            order by valid_from desc, valid_to desc
        ) as rn
    from prepared
)

select
    id as ef_id,
    source,
    factor_name,
    description,
    gCO2e_per_unit,
    unit,
    ghg_scope,
    category,
    sub_category,
    country_code,
    source_year,
    valid_from,
    valid_to,
    case
        when rn = 1 then true
        else false
    end as is_current,

    uncertainty_pct

from flagged
order by source, country_code, factor_name, source_year, valid_from
