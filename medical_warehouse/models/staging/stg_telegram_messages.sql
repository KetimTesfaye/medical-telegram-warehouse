{{ config(materialized='view') }}

with raw_source as (

    select * from {{ source('raw_data', 'telegram_messages') }}

),

cleaned as (

    select
        -- 1. Primary Keys & Identifiers
        cast(message_id as integer) as message_id,
        trim(channel_name) as channel_name,

        -- 2. Timestamps & Dates
        cast(message_date as timestamp with time zone) as message_at,

        -- 3. Text Fields & Cleaning
        trim(message_text) as message_text,

        -- 4. Flags & Metrics
        cast(views as integer) as view_count,
        cast(forwards as integer) as forward_count,
        cast(has_media as boolean) as has_media,
        length(trim(message_text)) as message_length

    from raw_source
    -- 5. Filter out empty or null rows
    where message_text is not null 
      and trim(message_text) != ''

)

select * from cleaned