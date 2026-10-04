-- 01 Brand scorecard: scale, labour efficiency and unit economics per brand.
-- Techniques: aggregation, window SUM() OVER () for share of total, CTE.
WITH brand AS (
    SELECT brand,
           COUNT(*)                      AS factories,
           SUM(workers)                  AS total_workers,
           SUM(monthly_output)           AS total_monthly_output,
           SUM(production_cost_index)    AS sum_cost_index
    FROM vw_factory_flat
    GROUP BY brand
)
SELECT brand,
       factories,
       total_workers,
       total_monthly_output,
       ROUND(100.0 * total_monthly_output / SUM(total_monthly_output) OVER (), 1) AS pct_of_combined_output,
       ROUND(1.0 * total_monthly_output / total_workers, 2)                       AS output_per_worker,
       ROUND(sum_cost_index * 1000000.0 / total_monthly_output, 2)                AS cost_index_per_million_units
FROM brand
ORDER BY brand;
