"Contains constants used in the DAGs"

import os
from pathlib import Path
from cosmos import ExecutionConfig

PROJECT_ROOT_PATH = Path(__file__).parent.parent
DEFAULT_DBT_ROOT_PATH = PROJECT_ROOT_PATH / "dbt"
DBT_EXECUTABLE = PROJECT_ROOT_PATH / "dbt_venv" / "bin" / "dbt"
DBT_ROOT_PATH = Path(os.getenv("DBT_ROOT_PATH", DEFAULT_DBT_ROOT_PATH))

jaffle_shop_path = Path(DBT_ROOT_PATH / "jaffle_shop")

venv_execution_config = ExecutionConfig(
    dbt_executable_path=str(DBT_EXECUTABLE),
)
