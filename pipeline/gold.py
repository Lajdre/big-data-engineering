from pyspark.sql import SparkSession

from pipeline import config


def build_gold(spark: SparkSession) -> None:
  """Build the three gold-layer tables via full overwrite of silver data."""

  # fmt: off
  silver = spark.read.format("jdbc") \
    .option("url", config.JDBC_URL) \
    .option("dbtable", config.SILVER_TABLE) \
    .option("driver", config.POSTGRES_DRIVER) \
    .option("user", config.JDBC_USER) \
    .option("password", config.JDBC_PASS) \
    .load()
  # fmt: on

  silver.createOrReplaceTempView("silver_src")

  _build_daily_mix(spark)
  _build_monthly_summary(spark)
  _build_daily_vs_monthly(spark)


def _build_daily_mix(spark: SparkSession) -> None:
  daily = spark.sql("""
    SELECT
        DATE(datetime)                                      AS day,
        ROUND(SUM(gas), 2)                                  AS total_gas_mwh,
        ROUND(SUM(liquid_fuel), 2)                          AS total_liquid_fuel_mwh,
        ROUND(SUM(coal), 2)                                 AS total_coal_mwh,
        ROUND(SUM(hydro), 2)                                AS total_hydro_mwh,
        ROUND(SUM(COALESCE(solar, 0)), 2)                   AS total_solar_mwh,
        ROUND(SUM(COALESCE(wind, 0)), 2)                    AS total_wind_mwh,
        ROUND(SUM(COALESCE(india_bheramara_hvdc, 0)), 2)    AS total_import_hvdc_mwh,
        ROUND(SUM(generation_mw), 2)                        AS total_generation_mwh,
        COUNT(*)                                            AS record_count
    FROM silver_src
    WHERE datetime IS NOT NULL
    GROUP BY DATE(datetime)
    ORDER BY day
   """)

  # fmt: off
  daily.write.format("jdbc") \
    .option("url", config.JDBC_URL) \
    .option("dbtable", config.GOLD_DAILY) \
    .option("driver", config.POSTGRES_DRIVER) \
    .option("user", config.JDBC_USER) \
    .option("password", config.JDBC_PASS) \
    .mode("overwrite") \
    .save()
  # fmt: on


def _build_monthly_summary(spark: SparkSession) -> None:
  monthly = spark.sql("""
    SELECT
        DATE_TRUNC('month', datetime)                       AS month,
        ROUND(AVG(demand_mw), 2)                            AS avg_demand_mw,
        ROUND(MAX(demand_mw), 2)                            AS peak_demand_mw,
        ROUND(AVG(generation_mw), 2)                        AS avg_generation_mw,
        ROUND(AVG(load_shedding), 2)                        AS avg_load_shedding_mw,
        ROUND(SUM(load_shedding), 2)                        AS total_load_shedding_mwh,
        ROUND(
            SUM(load_shedding) / NULLIF(SUM(demand_mw), 0) * 100,
            2
        )                                                   AS load_shedding_pct,
        MAX(CASE WHEN load_shedding > 0 THEN TRUE ELSE FALSE END) AS had_outages
    FROM silver_src
    WHERE datetime IS NOT NULL
    GROUP BY DATE_TRUNC('month', datetime)
    ORDER BY month
  """)

  # fmt: off
  monthly.write.format("jdbc") \
    .option("url", config.JDBC_URL) \
    .option("dbtable", config.GOLD_MONTHLY) \
    .option("driver", config.POSTGRES_DRIVER) \
    .option("user", config.JDBC_USER) \
    .option("password", config.JDBC_PASS) \
    .mode("overwrite") \
    .save()
  # fmt: on


def _build_daily_vs_monthly(spark: SparkSession) -> None:
  daily_vs_monthly = spark.sql("""
    WITH daily AS (
        SELECT
            DATE(datetime)                    AS day,
            ROUND(SUM(generation_mw), 2)      AS total_generation_mwh,
            ROUND(SUM(gas), 2)                AS total_gas_mwh,
            ROUND(SUM(coal), 2)               AS total_coal_mwh,
            ROUND(SUM(hydro), 2)              AS total_hydro_mwh
        FROM silver_src
        WHERE datetime IS NOT NULL
        GROUP BY DATE(datetime)
    ),
    monthly AS (
        SELECT
            DATE_TRUNC('month', datetime)  AS month,
            ROUND(AVG(demand_mw), 2)       AS avg_demand_mw,
            ROUND(MAX(demand_mw), 2)       AS peak_demand_mw,
            MAX(CASE WHEN load_shedding > 0 THEN TRUE ELSE FALSE END) AS had_outages
        FROM silver_src
        WHERE datetime IS NOT NULL
        GROUP BY DATE_TRUNC('month', datetime)
    )
    SELECT
        d.day,
        d.total_generation_mwh,
        d.total_gas_mwh,
        d.total_coal_mwh,
        d.total_hydro_mwh,
        m.avg_demand_mw  AS month_avg_demand_mw,
        m.peak_demand_mw AS month_peak_demand_mw,
        m.had_outages    AS month_had_outages,
        ROUND(
            d.total_generation_mwh / NULLIF(m.avg_demand_mw * 24, 0) * 100,
            2
        ) AS generation_to_monthly_demand_ratio
    FROM daily d
    JOIN monthly m ON DATE_TRUNC('month', d.day) = m.month
    ORDER BY d.day
  """)

  # fmt: off
  daily_vs_monthly.write.format("jdbc") \
    .option("url", config.JDBC_URL) \
    .option("dbtable", config.GOLD_VS_MONTHLY) \
    .option("driver", config.POSTGRES_DRIVER) \
    .option("user", config.JDBC_USER) \
    .option("password", config.JDBC_PASS) \
    .mode("overwrite") \
    .save()
  # fmt: on
