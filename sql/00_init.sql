-- Initialize database schemas

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'bronze') THEN
        CREATE SCHEMA bronze;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'silver') THEN
        CREATE SCHEMA silver;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'gold') THEN
        CREATE SCHEMA gold;
    END IF;
END
$$;
