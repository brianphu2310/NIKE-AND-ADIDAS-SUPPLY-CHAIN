-- 06 Pareto of output: running total and cumulative share of each brand's output, largest factory first.
-- Techniques: running total SUM() OVER (ORDER BY ... ROWS), ROW_NUMBER(), cumulative percentage.
SELECT brand, factory_code, country, city, monthly_output,
       ROW_NUMBER() OVER w                                                AS factory_rank,
       SUM(monthly_output) OVER (PARTITION BY brand ORDER BY monthly_output DESC, factory_code
                                 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_output,
       ROUND(100.0 * SUM(monthly_output) OVER (PARTITION BY brand ORDER BY monthly_output DESC, factory_code
                                 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
             / SUM(monthly_output) OVER (PARTITION BY brand), 1)          AS cumulative_share_pct
FROM vw_factory_flat
WINDOW w AS (PARTITION BY brand ORDER BY monthly_output DESC, factory_code)
ORDER BY brand, factory_rank;
