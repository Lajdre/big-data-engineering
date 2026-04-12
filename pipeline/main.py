from prefect import flow, task
from pyspark.sql import SparkSession

from pipeline import config
from pipeline.bronze import load_bronze
from pipeline.gold import build_gold
from pipeline.silver import transform_silver


def get_spark() -> SparkSession:
  return (
    SparkSession.builder.appName("pgcb-pipeline")
    .config("spark.jars.packages", config.POSTGRES_PACKAGE)
    .config("spark.driver.memory", "2g")
    .config("spark.executor.memory", "1g")
    .getOrCreate()
  )


@task(name="Bronze Layer", log_prints=True)
def bronze_task(csv_path: str | None = None) -> None:
  spark = get_spark()
  try:
    load_bronze(spark, csv_path)
  finally:
    spark.stop()


@task(name="Silver Layer", log_prints=True)
def silver_task() -> None:
  spark = get_spark()
  try:
    transform_silver(spark)
  finally:
    spark.stop()


@task(name="Gold Layer", log_prints=True)
def gold_task() -> None:
  spark = get_spark()
  try:
    build_gold(spark)
  finally:
    spark.stop()


@flow(name="PGCB ELT Pipeline", log_prints=True)
def pgcb_pipeline(csv_path: str | None = None) -> None:
  csv_path = csv_path or str(config.CSV_PATH)
  bronze_task(csv_path)
  silver_task()
  gold_task()


if __name__ == "__main__":
  pgcb_pipeline()
