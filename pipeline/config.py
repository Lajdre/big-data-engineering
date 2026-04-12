from pathlib import Path

JDBC_HOST = "localhost"
JDBC_PORT = "5432"
JDBC_DB   = "pgcb"
JDBC_USER = "pgcb"
JDBC_PASS = "pgcb"

JDBC_URL = f"jdbc:postgresql://{JDBC_HOST}:{JDBC_PORT}/{JDBC_DB}"

BRONZE_TABLE  = "bronze.raw_pgcb"
SILVER_TABLE  = "silver.pgcb_cleaned"
GOLD_DAILY    = "gold.daily_generation_mix"
GOLD_MONTHLY  = "gold.monthly_demand_summary"
GOLD_VS_MONTHLY = "gold.daily_vs_monthly"

CSV_PATH = Path("data/raw_pgcb.csv")

POSTGRES_DRIVER = "org.postgresql.Driver"
POSTGRES_PACKAGE = "org.postgresql:postgresql:42.7.4"
