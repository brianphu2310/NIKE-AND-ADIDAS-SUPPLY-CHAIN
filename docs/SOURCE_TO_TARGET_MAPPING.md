# Source-to-Target Mapping

Maps every column of the source file to the warehouse tables built by `python -m pipeline`
(`pipeline/extract.py` -> `validate.py` -> `transform.py` -> `load.py`). Model: [DATA_MODEL.md](DATA_MODEL.md). Column meanings: [DATA_DICTIONARY.md](DATA_DICTIONARY.md).

**Source:** `data/nike_adidas_factories.csv` (one row per factory). The PostgreSQL script `sql/nike_adidas_factories.sql` is parsed only to reconcile row-for-row with the CSV; it is not a second source of values.

## Column mapping

| Source column | Target table.column | Rule |
|---|---|---|
| `factory_id` | `dim_factory.source_factory_id` | Cast to int; kept as the natural source id (UNIQUE). Surrogate `factory_key` is generated 1..n ordered by `factory_code`. |
| `brand` | `dim_brand.brand_name` -> `fact_factory_snapshot.brand_key`, `dim_factory.brand_key` | Trim, title-case; distinct values get surrogate `brand_key`; must be `Nike` or `Adidas`. |
| (derived) | `dim_brand.code_prefix` | Lookup `BRAND_PREFIX` (brand -> factory-code prefix); validated against `factory_code`. |
| `factory_code` | `dim_factory.factory_code` | Trim, upper-case; de-duplicated on this key (UNIQUE). |
| `country` | `dim_country.country_name` -> `*.country_key` | Trim; distinct values get surrogate key. |
| (derived) | `dim_country.iso2`, `dim_country.region` | Lookup `COUNTRY_REF` (reference table in `validate.py`); unknown countries fail validation. |
| `city` | `dim_location.city` | Trim; one location row per (`country`, `city`). |
| `latitude`, `longitude` | `dim_location.latitude`, `.longitude` | Cast to float; first value per (country, city); range-checked (-90..90, -180..180). |
| `year` | `dim_year.year_key`, `fact_factory_snapshot.year_key` | Cast to int; distinct years form `dim_year`. |
| `workers` | `fact_factory_snapshot.workers` | Cast to int; must be > 0. |
| `monthly_output` | `fact_factory_snapshot.monthly_output` | Cast to int; must be > 0. |
| `production_cost` | `fact_factory_snapshot.production_cost_index` | Cast to float; renamed because it is a normalised index, not an absolute cost. |

## Derived columns (no source column)

| Target | Formula |
|---|---|
| `fact_factory_snapshot.output_per_worker` | `monthly_output / workers`, rounded to 2 dp |
| `fact_factory_snapshot.cost_index_per_million_units` | `production_cost / monthly_output * 1,000,000`, rounded to 2 dp |
| `fact_factory_snapshot.size_tier` | `workers` >= 25,000 -> Large; >= 10,000 -> Medium; else Small (analyst-defined) |
| `fact_factory_snapshot.cost_band` | `production_cost` >= 50 -> High; >= 40 -> Medium; else Low (analyst-defined) |
| surrogate keys (`*_key`) | 1..n over sorted natural keys, so a rebuild gives identical keys |

## Load order and integrity

`dim_brand`, `dim_year`, `dim_country` -> `dim_location` -> `dim_factory` -> `fact_factory_snapshot` (foreign keys enforced, `PRAGMA foreign_keys = ON`).
Row counts per table are written to the load audit and reconciled in [DATA_QUALITY.md](DATA_QUALITY.md).

## Not mapped / known limits

- The source has no date other than `year`, so the fact is a snapshot (grain: one factory, one reference year), not a time series.
- No column is dropped; every source column lands in exactly one target column (or, for `brand`/`country`/`city`, in a dimension key).
