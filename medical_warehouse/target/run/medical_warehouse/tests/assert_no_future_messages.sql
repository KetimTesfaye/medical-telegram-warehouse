
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- This test fails if any message has a date ahead of the current timestamp
select
    message_id,
    message_at
from "medical-telegram-warehouse"."staging"."stg_telegram_messages"
where message_at > current_timestamp
  
  
      
    ) dbt_internal_test