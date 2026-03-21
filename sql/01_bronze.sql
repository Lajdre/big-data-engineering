-- Bronze layer: raw ingestion from PGCB csv

DROP SCHEMA IF EXISTS bronze CASCADE;
CREATE SCHEMA bronze;

CREATE TABLE bronze.raw_pgcb (
    datetime                  TEXT,
    generation_mw             TEXT,
    demand_mw                 TEXT,
    load_shedding             TEXT,
    gas                       TEXT,
    liquid_fuel               TEXT,
    coal                      TEXT,
    hydro                     TEXT,
    solar                     TEXT,
    wind                      TEXT,
    india_bheramara_hvdc      TEXT,
    india_tripura             TEXT,
    india_adani               TEXT,
    nepal                     TEXT,
    remarks                   TEXT
);

COPY bronze.raw_pgcb(
    datetime, generation_mw, demand_mw, load_shedding,
    gas, liquid_fuel, coal, hydro, solar, wind,
    india_bheramara_hvdc, india_tripura, india_adani, nepal, remarks
) FROM '/data/raw_pgcb.csv' WITH (FORMAT csv, HEADER true, NULL 'NULL');

COMMENT ON TABLE bronze.raw_pgcb IS 'Raw PGCB power grid data -- ingested verbatim from xlsx';
