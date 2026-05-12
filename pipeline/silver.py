from pyspark.sql import Column, DataFrame, SparkSession
from pyspark.sql import functions as F

from pipeline import config

NAN_STRING = "nan"
NUMERIC_COLS = [
  "generation_mw",
  "demand_mw",
  "load_shedding",
  "gas",
  "liquid_fuel",
  "coal",
  "hydro",
  "solar",
  "wind",
  "india_bheramara_hvdc",
  "india_tripura",
  "india_adani",
  "nepal",
]


def _nullify_nan(col_name: str) -> Column:
  return F.when(
    (F.col(col_name) == NAN_STRING) | (F.col(col_name) == "NULL"), F.lit(None)
  ).otherwise(F.col(col_name))


def transform_silver(spark: SparkSession) -> DataFrame:
  """
  Read bronze data, clean it, de-duplicate, and overwrite silver.

  Cleaning:
    - Cast datetime to timestamp
    - Replace 'nan' and 'NULL' strings with NULL for numeric columns
    - Cast numeric columns to double precision
    - Drop rows with a null datetime
  """
  bronze = (
    spark.read.format("jdbc")
    .option("url", config.JDBC_URL)
    .option("dbtable", config.BRONZE_TABLE)
    .option("driver", config.POSTGRES_DRIVER)
    .option("user", config.JDBC_USER)
    .option("password", config.JDBC_PASS)
    .load()
  )

  df = bronze.withColumn("datetime", F.to_timestamp(F.col("datetime")))

  for col in NUMERIC_COLS:
    if col in df.columns:
      df = df.withColumn(col, _nullify_nan(col).cast("double"))

  df = df.dropna(subset=["datetime"])

  df = df.dropDuplicates(subset=["datetime"])

  # fmt: off
  df.write.format("jdbc") \
    .option("url", config.JDBC_URL) \
    .option("dbtable", config.SILVER_TABLE) \
    .option("driver", config.POSTGRES_DRIVER) \
    .option("user", config.JDBC_USER) \
    .option("password", config.JDBC_PASS) \
    .mode("overwrite") \
    .save()
  # fmt: on

  return df
