with staging as (

    select * from {{ ref('stg_yahoo_price_history') }}

    QUALIFY row_number() over (partition by ticker_symbol, price_date order by load_timestamp desc) = 1

),

calculated as (

    select
        price_date,
        ticker_symbol,
        open_price,
        high_price,
        low_price,
        close_price,
        adjusted_close_price,
        volume,
        -- Calculate daily change (using previous day's close if available)
        lag(adjusted_close_price, 1) over (partition by ticker_symbol order by price_date) as prev_day_adj_close,
        (adjusted_close_price - lag(adjusted_close_price, 1) over (partition by ticker_symbol order by price_date)) as daily_change_abs,
        coalesce(((adjusted_close_price / lag(adjusted_close_price, 1) over (partition by ticker_symbol order by price_date)) - 1) * 100, 0) as daily_change_pct,
        load_timestamp

    from staging

)

select
    -- Create a surrogate key for the table
    {{ dbt_utils.generate_surrogate_key(['price_date', 'ticker_symbol']) }} as stock_day_id,
    price_date,
    ticker_symbol,
    open_price,
    high_price,
    low_price,
    close_price,
    adjusted_close_price,
    prev_day_adj_close,
    daily_change_abs,
    daily_change_pct,
    volume,
    load_timestamp
from calculated