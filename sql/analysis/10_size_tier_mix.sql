-- 10 Size-tier mix by brand with share of each brand's factories and average cost per tier.
-- Techniques: GROUP BY two keys, window SUM() OVER (PARTITION BY) for within-brand share, CASE ordering.
SELECT brand, size_tier,
       COUNT(*)                                                        AS factories,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY brand), 1) AS pct_of_brand_factories,
       ROUND(AVG(production_cost_index), 2)                           AS avg_cost_index,
       ROUND(AVG(output_per_worker), 2)                               AS avg_output_per_worker
FROM vw_factory_flat
GROUP BY brand, size_tier
ORDER BY brand, CASE size_tier WHEN 'Large' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END;
