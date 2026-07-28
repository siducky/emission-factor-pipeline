with source as (
    select * from {{ source('bronze', 'ademe') }}
),

renamed as (
    select
        __id as id,
        regexp_replace(
            "Produit à l'unité",'\s*\(.*\)$',''
            ) as factor_name,
        concat('Emissions from the production of ',"Produit à l'unité") as description,
        case
            when "Produit à l'unité" like '%(kgeC%'
                then cast("Facteur d'émission" as double precision) / 1000.0
            else cast("Facteur d'émission" as double precision)
        end as gCO2e_per_unit,
        'piece' as unit,
        'Scope 3' as ghg_scope,
        'GL' as country_code,
        'ademe' as source,
        2016 as source_year,
        date '2016-01-01' as valid_from,
        date 'infinity' as valid_to,
        cast ("Incertitude en %" as double precision) as uncertainty_pct,
        cast(CodeFede as varchar) as sport_federation_code,
        cast(Federation as varchar) as federation,
    from source
)

select * from renamed