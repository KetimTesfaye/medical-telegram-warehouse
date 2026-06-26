-- This test fails if any message has a date ahead of the current timestamp
select
    message_id,
    message_at
from {{ ref('stg_telegram_messages') }}
where message_at > current_timestamp