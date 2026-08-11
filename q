                  Table "marts.dim_emission_factors"
     Column      |       Type        | Collation | Nullable | Default 
-----------------+-------------------+-----------+----------+---------
 ef_id           | character varying |           | not null | 
 source          | character varying |           | not null | 
 factor_name     | character varying |           | not null | 
 description     | character varying |           |          | 
 gCO2e_per_unit  | double precision  |           | not null | 
 unit            | character varying |           | not null | 
 ghg_scope       | character varying |           | not null | 
 category        | character varying |           |          | 
 sub_category    | character varying |           |          | 
 country_code    | character varying |           | not null | 
 source_year     | integer           |           | not null | 
 valid_from      | date              |           | not null | 
 valid_to        | date              |           | not null | 
 is_current      | boolean           |           | not null | 
 uncertainty_pct | double precision  |           |          | 
Indexes:
    "dim_emission_factors_pkey" PRIMARY KEY, btree (ef_id)

