# ELT Pipeline: PGCB Power Grid Data

## Analytical Goal

**Question:** How has Bangladesh's national grid performed over time in terms of
generation mix, demand coverage, and the frequency and severity of load-shedding
events?

This pipeline ingests hourly power grid telemetry published by the Power Grid Company
of Bangladesh (PGCB), transforms it through a medallion architecture (bronze → silver
→ gold), and produces analytical tables suitable for time-series analysis, generation
mix reporting, and demand-supply gap monitoring.

---

## Medallion Layers

### Bronze — Raw Ingestion

**Table:** `bronze.raw_pgcb`

Raw rows loaded verbatim from `PGCB_date_power_demand.xlsx`. All columns are `TEXT`
to capture the source exactly, including `nan` string literals and free-text
`remarks` values. No cleaning or type casting is applied at this layer.

**Source:** 92,650 hourly records spanning April 2015 onwards.

### Silver — Cleaned and Typed

**Table:** `silver.pgcb_cleaned`

The bronze table is transformed to enforce correct data types.

### Gold — Analytical Aggregations

**Table:** `gold.daily_generation_mix`  
Daily totals (MWh) per generation source (gas, liquid fuel, coal, hydro, solar, wind,
HVDC import) plus total generation and record count.

**Table:** `gold.monthly_demand_summary`  
Monthly statistics: average demand, peak demand, average load-shedding, total
load-shedding MWh, load-shedding as a percentage of demand, and a boolean
`had_outages` flag.

**Table:** `gold.daily_vs_monthly`  
A JOIN between daily generation mix and monthly demand summary, enabling per-day
views of how each day's output relates to the monthly context — useful for anomaly
detection.

---

## Data Quality Risks

### Risk 1 — Literal `'nan'` Strings in Numeric Columns

Several columns (`solar`, `wind`, `india_adani`, `nepal`) contain the string `"nan"`
rather than NULL or a numeric value in the raw source. Without explicit `NULLIF`
casting in the silver layer, these would either cause type-cast errors or silently
propagate through aggregations as non-NULL non-numeric values. **Mitigation:** All
numeric columns are wrapped with `NULLIF(..., 'nan')` before casting.

### Risk 2 — Inconsistent Time-Series Interval

The data mixes 30-minute and 60-minute records (e.g., `18:30` alongside `19:00`). A
simple `SUM()` across hourly buckets will double-count or under-count the energy
contribution of half-hour intervals if not resampled.

### Risk 3 — Unvalidated remarks Column

The `remarks` column is TEXT type without CHECK constraints or ENUM enforcement. While
currently sparse (7% populated, 2 distinct values), the schema allows any string
value. Future uncontrolled entries (e.g., 'Evening_Peak', 'evening_peak', 'EP') will
not be rejected at the database level.
