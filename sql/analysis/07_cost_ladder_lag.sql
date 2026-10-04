-- 07 Cost ladder: within each brand, order factories by cost index and compare with the next-cheaper one.
-- Techniques: LAG() with PARTITION BY, NULL handling with COALESCE, step-change calculation.
SELECT brand, factory_code, country, city, production_cost_index,
       LAG(factory_code)          OVER w AS next_cheaper_factory,
       LAG(production_cost_index) OVER w AS next_cheaper_cost,
       ROUND(production_cost_index - COALESCE(LAG(production_cost_index) OVER w, production_cost_index), 2)
                                         AS step_up_vs_next_cheaper
FROM vw_factory_flat
WINDOW w AS (PARTITION BY brand ORDER BY production_cost_index, factory_code)
ORDER BY brand, production_cost_index, factory_code;
