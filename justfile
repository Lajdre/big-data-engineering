default:
    @just --list

up:
    docker compose up -d
    @echo "Waiting for PostgreSQL to be ready..."
    @while ! podman-compose exec -T postgres pg_isready -U pgcb -d pgcb >/dev/null 2>&1; do sleep 1; done && echo "PostgreSQL is ready."

down:
    docker compose down

load-csv:
    uv run scripts/load.py

ingest-bronze: load-csv
    docker compose exec -T postgres psql -U pgcb -d pgcb -f /sql/01_bronze.sql

silver:
    docker compose exec -T postgres psql -U pgcb -d pgcb -f /sql/02_silver.sql

gold:
    docker compose exec -T postgres psql -U pgcb -d pgcb -f /sql/03_gold.sql

pipeline: up
    just ingest-bronze
    just silver
    just gold
    @echo ""
    @echo "Pipeline complete. Row counts:"
    docker compose exec -T postgres psql -U pgcb -d pgcb -c "SELECT 'bronze.raw_pgcb' AS tbl, COUNT(*) AS n FROM bronze.raw_pgcb UNION ALL SELECT 'silver.pgcb_cleaned', COUNT(*) FROM silver.pgcb_cleaned UNION ALL SELECT 'gold.daily_generation_mix', COUNT(*) FROM gold.daily_generation_mix UNION ALL SELECT 'gold.monthly_demand_summary', COUNT(*) FROM gold.monthly_demand_summary;"

clean-db:
    docker compose exec -T postgres psql -U pgcb -d pgcb -c "TRUNCATE TABLE bronze.raw_pgcb, silver.pgcb_cleaned, gold.daily_generation_mix, gold.monthly_demand_summary, gold.daily_vs_monthly;"
    @echo "All tables truncated. Schemas and structures preserved."

spark-pipeline:
    uv run python -m pipeline.main

inspect-tbl:
    docker compose exec -T postgres psql -U pgcb -d pgcb -c "SELECT 'bronze.raw_pgcb' AS tbl, COUNT(*) AS n FROM bronze.raw_pgcb UNION ALL SELECT 'silver.pgcb_cleaned', COUNT(*) FROM silver.pgcb_cleaned UNION ALL SELECT 'gold.daily_generation_mix', COUNT(*) FROM gold.daily_generation_mix UNION ALL SELECT 'gold.monthly_demand_summary', COUNT(*) FROM gold.monthly_demand_summary UNION ALL SELECT 'gold.daily_vs_monthly', COUNT(*) FROM gold.daily_vs_monthly;"

postgres-repl:
    docker compose exec postgres psql -U pgcb -d pgcb
