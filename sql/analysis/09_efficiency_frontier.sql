-- 09 Efficiency frontier: factories not dominated on (higher output_per_worker, lower cost index).
-- A factory is on the frontier if no other factory is at least as good on both and better on one.
-- Techniques: correlated NOT EXISTS anti-join, CTE, COUNT with window.
WITH f AS (SELECT factory_code, brand, country, city, output_per_worker, production_cost_index
           FROM vw_factory_flat)
SELECT a.factory_code, a.brand, a.country, a.city, a.output_per_worker, a.production_cost_index,
       COUNT(*) OVER (PARTITION BY a.brand) AS frontier_factories_for_brand
FROM f a
WHERE NOT EXISTS (
    SELECT 1 FROM f b
    WHERE b.output_per_worker      >= a.output_per_worker
      AND b.production_cost_index  <= a.production_cost_index
      AND (b.output_per_worker > a.output_per_worker OR b.production_cost_index < a.production_cost_index)
)
ORDER BY a.production_cost_index, a.output_per_worker DESC;
