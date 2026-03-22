-- Silver layer: cleaned and type-corrected version of bronze data

DROP SCHEMA IF EXISTS silver CASCADE;
CREATE SCHEMA silver;

CREATE TABLE silver.pgcb_cleaned (
    datetime                  TIMESTAMP NOT NULL,
    generation_mw             DOUBLE PRECISION NOT NULL,
    demand_mw                 DOUBLE PRECISION NOT NULL,
    load_shedding             DOUBLE PRECISION NOT NULL,
    gas                       DOUBLE PRECISION,
    liquid_fuel               DOUBLE PRECISION,
    coal                      DOUBLE PRECISION,
    hydro                     DOUBLE PRECISION,
    solar                     DOUBLE PRECISION,
    wind                      DOUBLE PRECISION,
    india_bheramara_hvdc      DOUBLE PRECISION,
    india_tripura             DOUBLE PRECISION,
    india_adani               DOUBLE PRECISION,
    nepal                     DOUBLE PRECISION,
    remarks                   TEXT,
    loaded_at                 TIMESTAMP DEFAULT NOW()
);

INSERT INTO silver.pgcb_cleaned (
    datetime, generation_mw, demand_mw, load_shedding,
    gas, liquid_fuel, coal, hydro, solar, wind,
    india_bheramara_hvdc, india_tripura, india_adani, nepal, remarks
)
SELECT
    CASE WHEN b.datetime ~ '^\d{4}-\d{2}-\d{2}' THEN b.datetime::timestamp ELSE NULL END,
    NULLIF(b.generation_mw,        'nan')::double precision,
    NULLIF(b.demand_mw,            'nan')::integer,
    NULLIF(b.load_shedding,        'nan')::integer,
    NULLIF(b.gas,                  'nan')::integer,
    NULLIF(b.liquid_fuel,          'nan')::integer,
    NULLIF(b.coal,                 'nan')::integer,
    NULLIF(b.hydro,                'nan')::integer,
    NULLIF(b.solar,                'nan')::double precision,
    NULLIF(b.wind,                 'nan')::double precision,
    NULLIF(b.india_bheramara_hvdc, 'nan')::integer,
    NULLIF(b.india_tripura,        'nan')::integer,
    NULLIF(b.india_adani,          'nan')::double precision,
    NULLIF(b.nepal,                'nan')::double precision,
    NULLIF(b.remarks,              'nan')::text
FROM bronze.raw_pgcb b;

CREATE INDEX idx_silver_datetime ON silver.pgcb_cleaned (datetime);

COMMENT ON TABLE silver.pgcb_cleaned IS 'Cleaned PGCB data — nan strings cast to NULL, proper types, sorted';
