with source as (
    select * from {{ source('bronze', 'ademe') }}
),

renamed as (
    select
        uuid() as id,
        cast("Produit à l'unité" as varchar) as factor_name,
        cast("Facteur d'émission" as double precision) as gCO2e_per_unit,
        'piece' as unit,
        'Scope 3' as ghg_scope,
        'GL' as country_code,
        'ademe' as source,
        2016 as source_year,
        date '2016-01-01' as valid_from,
        date 'infinity' as valid_to,
        coalesce(cast ("Incertitude en %" as double precision),0) as uncertainty_pct,
        cast(CodeFede as varchar) as sport_federation_code,
        cast(Federation as varchar) as federation
    from source
)

select * from renamed