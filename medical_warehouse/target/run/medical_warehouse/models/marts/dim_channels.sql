
  
    

  create  table "medical-telegram-warehouse"."staging"."dim_channels__dbt_tmp"
  
  
    as
  
  (
    with channel_metrics as (
    select
        channel_name,
        min(message_at) as first_post_date,
        max(message_at) as last_post_date,
        count(message_id) as total_posts,
        avg(view_count) as avg_views
    from "medical-telegram-warehouse"."staging"."stg_telegram_messages"
    group by channel_name
)

select
    -- Generate a clean text surrogate key using MD5
    md5(channel_name) as channel_key,
    channel_name,
    
    -- Channel Type Classification Rule
    case 
        when lower(channel_name) like '%pharma%' or lower(channel_name) like '%tena%' then 'Pharmaceutical'
        when lower(channel_name) like '%cosm%' or lower(channel_name) like '%beauty%' then 'Cosmetics'
        else 'Medical'
    end as channel_type,
    
    first_post_date,
    last_post_date,
    total_posts,
    round(avg_views, 2) as avg_views
from channel_metrics
  );
  