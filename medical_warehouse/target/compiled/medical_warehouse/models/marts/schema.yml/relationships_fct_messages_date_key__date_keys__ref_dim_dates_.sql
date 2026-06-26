
    
    

with child as (
    select date_key as from_field
    from "medical-telegram-warehouse"."staging"."fct_messages"
    where date_key is not null
),

parent as (
    select date_keys as to_field
    from "medical-telegram-warehouse"."staging"."dim_dates"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


