
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select channel_key
from "medical-telegram-warehouse"."staging"."dim_channels"
where channel_key is null



  
  
      
    ) dbt_internal_test