
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- This test fails if any message has a view count less than 0
select
    message_id,
    view_count
from "medical-telegram-warehouse"."staging"."stg_telegram_messages"
where view_count < 0
  
  
      
    ) dbt_internal_test