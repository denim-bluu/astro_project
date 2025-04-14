{{ config(
    full_refresh = true
) }}

with source_data as (

    select
        DATE as price_date,
        OPEN as open_price,
        HIGH as high_price,
        LOW as low_price,
        CLOSE as close_price,
        ADJ_CLOSE as adjusted_close_price,
        VOLUME as volume,
        TICKER as ticker_symbol,
        LOADTIMESTAMP as load_timestamp

    -- References source defined in staging/schema.yml
    from {{ source('yahoo_raw', 'PRICE_HISTORY') }}

)

select
    -- Cast data types explicitly if needed, although Snowflake is often good at inference
    -- For example: price_date::date as price_date, volume::number as volume
    price_date,
    open_price,
    high_price,
    low_price,
    close_price,
    adjusted_close_price,
    volume,
    ticker_symbol,
    load_timestamp
from source_data

-- You could add incremental logic here if desired, using {{ this }} and is_incremental()
-- Example for incremental based on load_timestamp:
-- {% if is_incremental() %}
-- where load_timestamp > (select max(load_timestamp) from {{ this }})
-- {% endif %}
