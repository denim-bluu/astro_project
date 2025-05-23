from __future__ import annotations

import pendulum

from airflow.decorators import dag, task
from airflow.operators.empty import EmptyOperator
from cosmos import DbtTaskGroup, ProjectConfig, ProfileConfig, ExecutionConfig
from airflow.providers.snowflake.operators.snowflake import SnowflakeSqlApiOperator
from include.constants import DBT_ROOT_PATH, DBT_EXECUTABLE
from include.yfinance_loader import fetch_and_load_stock_data  # Import our function

# --- Configuration ---
SNOWFLAKE_CONN_ID = "snowflake_conn"
YAHOO_DATABASE = "dbt_dev"
YAHOO_SCHEMA = "YAHOO_FINANCE"
YAHOO_TABLE = "PRICE_HISTORY"
TICKERS_TO_FETCH = ["MSFT", "AAPL", "GOOGL"]

# dbt Configuration
DBT_PROJECT_PATH = DBT_ROOT_PATH / "yahoo_finance_dbt"

# IMPORTANT: Ensure profile in dbt/yahoo_finance_dbt/profiles.yml
# points to your Snowflake account correctly AND uses secure credential methods
# (e.g., environment variables set by Airflow connection, NOT hardcoded passwords)
DBT_PROFILE_CONFIG = ProfileConfig(
    profile_name="yahoo_finance_profile",  # Must match profiles.yml
    target_name="dev",  # Must match profiles.yml
    profiles_yml_filepath=DBT_PROJECT_PATH / "profiles.yml",
)
DBT_EXECUTION_CONFIG = ExecutionConfig(
    dbt_executable_path=str(DBT_EXECUTABLE),
)


# --- /Configuration ---
@dag(
    dag_id="yahoo_finance_to_snowflake_pipeline",
    start_date=pendulum.datetime(2025, 4, 1, tz="UTC"),
    schedule="@daily",
    catchup=False,
    tags=["yahoo_finance", "snowflake", "dbt", "cosmos"],
    default_args={"retries": 1, "retry_delay": pendulum.duration(minutes=5)},
)
def yahoo_finance_pipeline():
    ensure_schema_exist = SnowflakeSqlApiOperator(
        task_id="ensure_schema_exist",
        snowflake_conn_id=SNOWFLAKE_CONN_ID,
        sql=f"""
    CREATE SCHEMA IF NOT EXISTS {YAHOO_DATABASE}.{YAHOO_SCHEMA};
    """,
    )
    ensure_table_exist = SnowflakeSqlApiOperator(
        task_id="ensure_table_exist",
        snowflake_conn_id=SNOWFLAKE_CONN_ID,
        sql=f"""
    CREATE TABLE IF NOT EXISTS {YAHOO_DATABASE}.{YAHOO_SCHEMA}.{YAHOO_TABLE} (
        DATE TIMESTAMP_NTZ,
        OPEN FLOAT,
        HIGH FLOAT,
        LOW FLOAT,
        CLOSE FLOAT,
        ADJ_CLOSE FLOAT,
        VOLUME NUMBER,
        DIVIDENDS FLOAT,
        STOCK_SPLITS FLOAT,
        TICKER VARCHAR,
        LOADTIMESTAMP TIMESTAMP_NTZ
    );
    """,
    )

    @task
    def extract_load_yahoo_finance(
        tickers: list[str],
        conn_id: str,
        db: str,
        schema: str,
        table: str,
        logical_date,  # Airflow injects this!
    ):
        """
        Task to extract data for the previous day and load it into Snowflake.
        """
        # Calculate start and end dates for the previous day based on logical_date
        # logical_date is the *start* of the DAG run interval
        end_date_str = logical_date
        start_date = pendulum.from_format(logical_date, "YYYY-MM-DD", tz="UTC")
        start_date = start_date.subtract(days=1)  # Use subtract for clarity
        start_date_str = start_date.to_date_string()
        print(
            f"Fetching data from {start_date_str} up to (but not including) {end_date_str}"
        )

        fetch_and_load_stock_data(
            tickers=tickers,
            snowflake_conn_id=conn_id,
            database=db,
            schema=schema,
            table_name=table,
            start_date_str=start_date_str,
            end_date_str=end_date_str,
        )

    # Task to run the extraction and loading function
    fetch_and_load_task = extract_load_yahoo_finance(
        tickers=TICKERS_TO_FETCH,
        conn_id=SNOWFLAKE_CONN_ID,
        db=YAHOO_DATABASE,
        schema=YAHOO_SCHEMA,
        table=YAHOO_TABLE,
        logical_date="{{ ds }}",  # Pass logical_date using Airflow's macro
    )

    # Define the dbt task group using Cosmos
    # This will run all models in your dbt project by default
    transform_data = DbtTaskGroup(
        group_id="dbt_transform_yahoo",
        project_config=ProjectConfig(DBT_PROJECT_PATH),
        profile_config=DBT_PROFILE_CONFIG,
        execution_config=DBT_EXECUTION_CONFIG,
        operator_args={"install_deps": True},
    )

    start = EmptyOperator(task_id="start")
    end = EmptyOperator(task_id="end")

    # Define dependencies
    (
        start
        >> ensure_schema_exist
        >> ensure_table_exist
        >> fetch_and_load_task
        >> transform_data
        >> end
    )


# Instantiate the DAG
yahoo_finance_pipeline()
