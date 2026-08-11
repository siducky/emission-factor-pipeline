with

overrides_applied as (
    select
        s.* exclude (sub_category),
        case
            when s.category = 'WTT- fuels'
                then s.category
            else s.sub_category
        end as sub_category,
        o.should_drop
    from {{ ref('stg_defra') }} s
    left join {{ ref('defra_overrides') }} o
        on s.category = o.category
        and s.sub_category = o.sub_category
    where coalesce(o.should_drop, false) = false
),
category_normalised as (
    select
        oa.*,
        cm.category_new
    from overrides_applied oa
    left join {{ ref('defra_category_mapping') }} cm
        on oa.category = cm.category_old
),
sub_category_normalised as (
    select
        cn.*,
        scm.sub_category_new
    from category_normalised cn
    left join {{ ref('defra_sub_category_mapping') }} scm
        on cn.sub_category = scm.sub_category_old
),
defra_intermediate as (
    select
        id,
        case
            when coalesce(sub_category_new,sub_category) in ('Hotel stay')
                then sub_category || ' - ' || factor_name
            when sub_category_new in ('Cars')
                then factor_name || ' - ' || column_text
            when coalesce(sub_category_new,sub_category) in ('Motorbike')
                then factor_name || ' ' || lower(substr(sub_category,1,1)) || substr(sub_category, 2)
            when coalesce(sub_category_new,sub_category) in ('WTT- Motorbike')
                then 'WTT- ' || factor_name || ' ' || 'motorbike'
            when coalesce(sub_category_new,sub_category) in ('Heavy Goods Vehicles','Heavy Goods Vehicles - Refrigerated','Vans','WTT- Heavy Goods Vehicles','WTT- Heavy Goods Vehicles - Refrigerated','WTT- Vans', 'WTT- Cars')
                then coalesce(sub_category_new,sub_category) || ' - '|| factor_name ||' - '|| column_text
            when coalesce(sub_category_new,sub_category) in ('Cargo Ship')
                then factor_name || ' - '|| coalesce(sub_category_new,sub_category)  ||' - '|| sub_sub_category
            when coalesce(sub_category_new,sub_category) in ('WTT- Cargo Ship')
                then 'WTT- ' || factor_name || ' - '|| 'Cargo' ||' - '|| sub_sub_category
            when coalesce(sub_category_new,sub_category) in ('Electricity','WTT- Electricity','Electricity T&D', 'WTT- Electricity (T&D)','WTT- district heat & steam distribution')
                then sub_category_new
            when category_new in ('Waste','Materials')
                then factor_name || ' - '|| column_text
            when coalesce(sub_category_new,sub_category) in ('Ferry', 'WTT- ferry')
                then coalesce(sub_category_new,sub_category) || ' -' || factor_name
            when coalesce(sub_category_new,sub_category) in ('WTT- biomass','WTT- heat and steam', 'WTT- biogas','WTT- fuels', 'WTT- Bus','WTT- Taxis','WTT- Rail','WTT- Freight Flights','WTT- Sea Tanker', 'WTT- biofuel')
                then 'WTT- ' || factor_name
            else factor_name
        end as factor_name,
        concat('GHG Emission factor for ',coalesce(sub_category_new,sub_category),' belonging to category ', coalesce(category_new,category)) as description,
        gco2e_per_unit,
        unit,
        ghg_scope,
        case
            when coalesce(sub_category_new,sub_category) in (
                'Electricity',
                'WTT- Electricity',
                'Electricity T&D',
                'Heat and steam',
                'WTT- heat and steam', 
                'WTT- UK electricity (T&D)',
                'WTT- district heat & steam distribution'
            )
                then 'GB'
            else country_code
        end as country_code,
        source,
        source_year,
        valid_from,
        valid_to,
        coalesce(category_new, category) as category,
        coalesce(sub_category_new, sub_category) as sub_category,
        sub_sub_category,
        column_text
    from sub_category_normalised)
select * from defra_intermediate