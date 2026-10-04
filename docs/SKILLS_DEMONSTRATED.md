# Skills Demonstrated

Every path below exists in this repo and is exercised by the tests or CI.

| Skill | Where to see it |
|---|---|
| SQL: CTEs, joins, aggregation, `CASE` | [`sql/analysis/01_brand_scorecard.sql`](../sql/analysis/01_brand_scorecard.sql), [`04_country_brand_crosstab.sql`](../sql/analysis/04_country_brand_crosstab.sql), [`08_head_to_head_same_city.sql`](../sql/analysis/08_head_to_head_same_city.sql) |
| SQL: window functions (`RANK`, `PERCENT_RANK`, `LAG`, running totals, partitioned shares) | [`02_efficiency_rank.sql`](../sql/analysis/02_efficiency_rank.sql), [`06_output_pareto_running_total.sql`](../sql/analysis/06_output_pareto_running_total.sql), [`07_cost_ladder_lag.sql`](../sql/analysis/07_cost_ladder_lag.sql), [`03_country_concentration_hhi.sql`](../sql/analysis/03_country_concentration_hhi.sql) |
| SQL: anti-join / frontier logic (`NOT EXISTS`) | [`09_efficiency_frontier.sql`](../sql/analysis/09_efficiency_frontier.sql) |
| Original PostgreSQL schema and queries | [`sql/nike_adidas_factories.sql`](../sql/nike_adidas_factories.sql) |
| Dimensional modelling (star/snowflake, surrogate keys, grain) | [`pipeline/schema.sql`](../pipeline/schema.sql), [`docs/DATA_MODEL.md`](DATA_MODEL.md) |
| ETL in Python (extract, transform, load, idempotent full refresh) | [`pipeline/extract.py`](../pipeline/extract.py), [`transform.py`](../pipeline/transform.py), [`load.py`](../pipeline/load.py), [`__main__.py`](../pipeline/__main__.py) |
| Data quality (nulls, duplicates, ranges, referential, reconciliation, outliers) | [`pipeline/validate.py`](../pipeline/validate.py), report in [`docs/DATA_QUALITY.md`](DATA_QUALITY.md) |
| Data documentation (generated dictionary, ER diagram) | [`pipeline/docgen.py`](../pipeline/docgen.py), [`docs/DATA_DICTIONARY.md`](DATA_DICTIONARY.md), [`docs/DATA_MODEL.md`](DATA_MODEL.md) |
| Reproducible query outputs | [`sql/run_queries.py`](../sql/run_queries.py), [`docs/query_results/`](query_results/) |
| Testing (pytest: defect injection, determinism, query correctness vs pandas) | [`tests/test_pipeline.py`](../tests/test_pipeline.py), [`tests/test_queries.py`](../tests/test_queries.py), [`tests/test_dataset.py`](../tests/test_dataset.py) |
| CI (tests, end-to-end run, generated-docs freshness gate) | [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) |
| BI / visualisation | Tableau dashboard linked from the [README](../README.md) (workbook not in the repo); Power BI report with DAX measures in [`powerbi/nike_adidas_dashboard.pbix`](../powerbi/nike_adidas_dashboard.pbix), previews in [`docs/powerbi/`](powerbi/) |

Not claimed: no scraping or API ingestion, no orchestration tool, no cloud warehouse, no time-series modelling.
