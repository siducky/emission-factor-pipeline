WITH source AS (
    SELECT * FROM {{ source('bronze', 'defra') }}
),

extracted AS (
    SELECT *,
        CAST(
            REGEXP_EXTRACT(
                alias(COLUMNS('GHG Conversion Factor*')), 
                '\d{4}'
            ) AS INTEGER
        ) AS source_year
    FROM source
    WHERE "GHG/Unit" = 'kg CO2e'
),

renamed AS (
    SELECT
        uuid() AS id,
        CAST("Level 3" AS VARCHAR) AS factor_name,
        CONCAT('Emission factor for ', "Level 3",
                CASE WHEN "Level 4" IS NOT NULL OR "Column Text" IS NOT NULL
                    THEN ' (' || COALESCE("Level 4", '') || COALESCE(' ' || "Column Text", '') || ')' 
                    ELSE ''
                END,
                ' mapped to category ', "Level 2",
                 ' and aggregated category ', "Level 1") AS description,
                 
        -- Added the '*' wildcard here
        CAST(COLUMNS('GHG Conversion Factor*') AS DOUBLE PRECISION) / 1000.0 AS gCO2e_per_unit,
        
        CAST(UOM AS VARCHAR) AS unit,
        CAST(Scope AS VARCHAR) AS ghg_scope,
        'GL' AS country_code,
        'defra' AS source,
        source_year,
        CAST("Level 2" AS VARCHAR) AS category,
        CAST("Level 1" AS VARCHAR) AS aggregated_category,
        make_date(source_year, 1, 1) AS valid_from,
        make_date(source_year, 12, 31) AS valid_to
    FROM extracted
    
    -- Added the '*' wildcard here as well
    WHERE COLUMNS('GHG Conversion Factor*') IS NOT NULL
)

SELECT * FROM renamed