-- Star/snowflake warehouse model (SQLite). dim_country -> dim_location -> dim_factory is the snowflaked branch.
PRAGMA foreign_keys = ON;

DROP VIEW  IF EXISTS vw_factory_flat;
DROP TABLE IF EXISTS fact_factory_snapshot;
DROP TABLE IF EXISTS dim_factory;
DROP TABLE IF EXISTS dim_location;
DROP TABLE IF EXISTS dim_country;
DROP TABLE IF EXISTS dim_year;
DROP TABLE IF EXISTS dim_brand;

CREATE TABLE dim_brand (
    brand_key    INTEGER PRIMARY KEY,
    brand_name   TEXT NOT NULL UNIQUE CHECK (brand_name IN ('Nike', 'Adidas')),
    code_prefix  TEXT NOT NULL UNIQUE
);

CREATE TABLE dim_year (
    year_key     INTEGER PRIMARY KEY CHECK (year_key BETWEEN 2000 AND 2100)  -- calendar year
);

CREATE TABLE dim_country (
    country_key  INTEGER PRIMARY KEY,
    country_name TEXT NOT NULL UNIQUE,
    iso2         TEXT NOT NULL UNIQUE,
    region       TEXT NOT NULL
);

CREATE TABLE dim_location (
    location_key INTEGER PRIMARY KEY,
    country_key  INTEGER NOT NULL REFERENCES dim_country (country_key),
    city         TEXT NOT NULL,
    latitude     REAL NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude    REAL NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    UNIQUE (country_key, city)
);

CREATE TABLE dim_factory (
    factory_key       INTEGER PRIMARY KEY,
    source_factory_id INTEGER NOT NULL UNIQUE,   -- factory_id in the source CSV
    factory_code      TEXT NOT NULL UNIQUE,
    brand_key         INTEGER NOT NULL REFERENCES dim_brand (brand_key),
    location_key      INTEGER NOT NULL REFERENCES dim_location (location_key)
);

CREATE TABLE fact_factory_snapshot (
    factory_key                 INTEGER PRIMARY KEY REFERENCES dim_factory (factory_key),
    brand_key                   INTEGER NOT NULL REFERENCES dim_brand (brand_key),
    location_key                INTEGER NOT NULL REFERENCES dim_location (location_key),
    country_key                 INTEGER NOT NULL REFERENCES dim_country (country_key),
    year_key                    INTEGER NOT NULL REFERENCES dim_year (year_key),
    workers                     INTEGER NOT NULL CHECK (workers > 0),
    monthly_output              INTEGER NOT NULL CHECK (monthly_output > 0),
    production_cost_index       REAL    NOT NULL CHECK (production_cost_index > 0),
    output_per_worker           REAL    NOT NULL,
    cost_index_per_million_units REAL   NOT NULL,
    size_tier                   TEXT    NOT NULL CHECK (size_tier IN ('Small', 'Medium', 'Large')),
    cost_band                   TEXT    NOT NULL CHECK (cost_band IN ('Low', 'Medium', 'High'))
);

CREATE INDEX ix_fact_brand    ON fact_factory_snapshot (brand_key);
CREATE INDEX ix_fact_country  ON fact_factory_snapshot (country_key);
CREATE INDEX ix_fact_location ON fact_factory_snapshot (location_key);
CREATE INDEX ix_fact_year     ON fact_factory_snapshot (year_key);
CREATE INDEX ix_location_country ON dim_location (country_key);
CREATE INDEX ix_factory_brand ON dim_factory (brand_key);

CREATE VIEW vw_factory_flat AS
SELECT f.factory_key, df.factory_code, b.brand_name AS brand, c.country_name AS country, c.region,
       l.city, l.latitude, l.longitude, f.year_key AS year, f.workers, f.monthly_output,
       f.production_cost_index, f.output_per_worker, f.cost_index_per_million_units,
       f.size_tier, f.cost_band
FROM fact_factory_snapshot f
JOIN dim_factory  df ON df.factory_key  = f.factory_key
JOIN dim_brand    b  ON b.brand_key     = f.brand_key
JOIN dim_location l  ON l.location_key  = f.location_key
JOIN dim_country  c  ON c.country_key   = f.country_key;
