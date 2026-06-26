select
    message_id,
    -- Foreign Keys matching your Dimensions
    md5(channel_name) as channel_key,
    cast(to_char(message_at, 'YYYYMMDD') as integer) as date_key,
    
    -- Text Metrics
    message_text,
    message_length,
    
    -- Core Measurable Quantities
    view_count,
    forward_count,
    has_media as has_image_flag
from "medical-telegram-warehouse"."staging"."stg_telegram_messages"