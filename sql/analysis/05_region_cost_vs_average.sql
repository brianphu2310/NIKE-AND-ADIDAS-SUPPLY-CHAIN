-- 05 Region cost and volume vs the global average (the "geography drives cost" claim).
-- Techniques: CTE, window AVG() OVER () for a benchmark, difference vs benchmark, RANK().
WITH region AS (
    SELECT region,
           COUNT(*)                               AS factories,
           SUM(monthly_output)                    AS total_output,
           AVG(production_cost_index)             AS avg_cost_index,
           1.0 * SUM(monthly_output) / SUM(workers) AS output_per_worker
    FROM vw_factory_flat
    GROUP BY region
)
SELECT region, factories, total_output,
       ROUND(avg_cost_index, 2)                                       AS avg_cost_index,
       ROUND(avg_cost_index - AVG(avg_cost_index) OVER (), 2)         AS cost_vs_mean_of_regions,
       ROUND(output_per_worker, 2)                                    AS output_per_worker,
       RANK() OVER (ORDER BY avg_cost_index)                          AS cheapest_rank
FROM region
ORDER BY cheapest_rank;
