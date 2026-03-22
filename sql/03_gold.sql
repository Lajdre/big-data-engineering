-- Gold layer: analytical views for grid operations and generation mix analysis

DROP SCHEMA IF EXISTS gold CASCADE;
CREATE SCHEMA gold;

-- 1. Daily generation mix: total MWh per source per day
--   (hourly readings assumed to be 1-hour intervals; SUM is the MWh approximation)
CREATE TABLE gold.daily_generation_mix AS
SELECT
   DATE(datetime)                                                AS day,
   ROUND((SUM(gas))::numeric, 2)                                 AS total_gas_mwh,
   ROUND((SUM(liquid_fuel))::numeric, 2)                         AS total_liquid_fuel_mwh,
   ROUND((SUM(coal))::numeric, 2)                                AS total_coal_mwh,
   ROUND((SUM(hydro))::numeric, 2)                               AS total_hydro_mwh,
   ROUND((SUM(COALESCE(solar, 0)))::numeric, 2)                  AS total_solar_mwh,
   ROUND((SUM(COALESCE(wind, 0)))::numeric, 2)                   AS total_wind_mwh,
   ROUND((SUM(COALESCE(india_bheramara_hvdc, 0)))::numeric, 2)   AS total_import_hvdc_mwh,
   ROUND((SUM(generation_mw))::numeric, 2)                       AS total_generation_mwh,
   COUNT(*)                                                      AS record_count
FROM silver.pgcb_cleaned
WHERE datetime IS NOT NULL
GROUP BY DATE(datetime)
ORDER BY day;

-- 2. Monthly demand and supply summary with unmet demand flag
CREATE TABLE gold.monthly_demand_summary AS
SELECT
   DATE_TRUNC('month', s.datetime)::DATE                         AS month,
   ROUND((AVG(s.demand_mw))::numeric, 2)                         AS avg_demand_mw,
   ROUND((MAX(s.demand_mw))::numeric, 2)                         AS peak_demand_mw,
   ROUND((AVG(s.generation_mw))::numeric, 2)                     AS avg_generation_mw,
   ROUND((AVG(s.load_shedding))::numeric, 2)                     AS avg_load_shedding_mw,
   ROUND((SUM(s.load_shedding))::numeric, 2)                     AS total_load_shedding_mwh,
   ROUND(
       ((SUM(s.load_shedding))::numeric / NULLIF((SUM(s.demand_mw))::numeric, 0)) * 100,
       2
   )                                                             AS load_shedding_pct,
   CASE WHEN SUM(s.load_shedding) > 0 THEN TRUE ELSE FALSE END   AS had_outages
FROM silver.pgcb_cleaned s
WHERE s.datetime IS NOT NULL
GROUP BY DATE_TRUNC('month', s.datetime)
ORDER BY month;

-- 3. Cross-layer JOIN: daily generation mix enriched with monthly demand context
--   Each day is annotated with its month's average/peak demand and outage flag,
--   enabling per-day anomaly detection.
CREATE TABLE gold.daily_vs_monthly AS
SELECT
   d.day,
   d.total_generation_mwh,
   d.total_gas_mwh,
   d.total_coal_mwh,
   d.total_hydro_mwh,
   m.avg_demand_mw                                               AS month_avg_demand_mw,
   m.peak_demand_mw                                              AS month_peak_demand_mw,
   m.had_outages                                                 AS month_had_outages,
   ROUND(
       (d.total_generation_mwh / NULLIF((m.avg_demand_mw * 24)::numeric, 0)) * 100,
       2
   )                                                             AS generation_to_monthly_demand_ratio
FROM gold.daily_generation_mix d
JOIN gold.monthly_demand_summary m ON DATE_TRUNC('month', d.day) = m.month
ORDER BY d.day;
