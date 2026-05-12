from pyspark.sql import DataFrame, SparkSession

from pipeline import config


def load_bronze(spark: SparkSession, csv_path: str | None = None) -> DataFrame:
  """Ingest raw CSV into the bronze schema via JDBC append."""
  path = csv_path or str(config.CSV_PATH)

  df = spark.read.csv(path, header=True, inferSchema=False)

  deduped = df.dropDuplicates(subset=["datetime"])

  # fmt: off
  deduped.write.format("jdbc") \
    .option("url", config.JDBC_URL) \
    .option("dbtable", config.BRONZE_TABLE) \
    .option("driver", config.POSTGRES_DRIVER) \
    .option("user", config.JDBC_USER) \
    .option("password", config.JDBC_PASS) \
    .mode("append") \
    .save()
  # fmt: on

  return deduped
