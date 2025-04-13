from cosmos import ProfileConfig
from include.constants import jaffle_shop_path
from cosmos.profiles import (
    PostgresUserPasswordProfileMapping,
)


airflow_db = ProfileConfig(
    profile_name="airflow_db",
    target_name="dev",
    profile_mapping=PostgresUserPasswordProfileMapping(
        conn_id="airflow_metadata_db",
        profile_args={"schema": "dbt"},
    ),
)
duckdbt_profile = ProfileConfig(
    # these map to dbt/jaffle_shop/profiles.yml
    profile_name="duckdb_profile",
    target_name="dev",
    profiles_yml_filepath=jaffle_shop_path / "profiles.yml",
)
snowflake_profile = ProfileConfig(
    profile_name="snowflake_profile",
    target_name="dev",
    profiles_yml_filepath=jaffle_shop_path / "profiles.yml",
    # profile_mapping=SnowflakeUserPasswordProfileMapping(
    #     conn_id="snowflake_conn",
    #     profile_args={
    #         "account": "{{ conn.snowflake_conn.extra_dejson['account'] }}",
    #         "database": "{{ conn.snowflake_conn.extra_dejson['database'] }}",
    #         "warehouse": "{{ conn.snowflake_conn.extra_dejson['warehouse'] }}",
    #         "role": "{{ conn.snowflake_conn.extra_dejson['role'] }}",
    #         "schema": "{{ conn.snowflake_conn.extra_dejson['schema'] }}",
    #     },
    # ),
)
