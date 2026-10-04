-- 08 Head-to-head: Nike vs Adidas factories in the same city (self-join on the fact view).
-- Techniques: self-join, CTE, CASE to name the more efficient/cheaper brand.
WITH nike AS   (SELECT * FROM vw_factory_flat WHERE brand = 'Nike'),
     adidas AS (SELECT * FROM vw_factory_flat WHERE brand = 'Adidas')
SELECT n.country, n.city,
       n.factory_code AS nike_factory, a.factory_code AS adidas_factory,
       n.output_per_worker AS nike_output_per_worker, a.output_per_worker AS adidas_output_per_worker,
       n.production_cost_index AS nike_cost_index, a.production_cost_index AS adidas_cost_index,
       CASE WHEN n.output_per_worker > a.output_per_worker THEN 'Nike'
            WHEN n.output_per_worker < a.output_per_worker THEN 'Adidas' ELSE 'Tie' END AS more_efficient,
       CASE WHEN n.production_cost_index < a.production_cost_index THEN 'Nike'
            WHEN n.production_cost_index > a.production_cost_index THEN 'Adidas' ELSE 'Tie' END AS lower_cost
FROM nike n
JOIN adidas a ON a.country = n.country AND a.city = n.city
ORDER BY n.country, n.city;
