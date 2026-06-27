{{ config(
    materialized='table'
) }}

with raw_yolo as (
    select
        -- Extract message_id by parsing numeric characters out of the image filename (e.g., '26.jpg' -> 26)
        cast(regexp_replace(image_name, '[^0-9]', '', 'g') as integer) as message_id,
        channel_folder,
        detected_objects,
        confidence_scores,
        primary_object as detected_class,
        image_category
    from {{ source('raw_data', 'yolo_image_detections') }}
),

fct_messages_base as (
    select
        message_id,
        channel_key,
        date_key
    from {{ ref('fct_messages') }}
)

select
    f.message_id,
    f.channel_key,
    f.date_key,
    y.detected_class,
    y.confidence_scores as confidence_score,  -- Keeping full confidence string or fallback array context
    y.image_category
from raw_yolo y
inner join fct_messages_base f 
    on y.message_id = f.message_id