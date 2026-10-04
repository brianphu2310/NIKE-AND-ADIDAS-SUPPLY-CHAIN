-- 04 Country x brand cross-tab with an asymmetry flag (conditional aggregation pivot).
-- Techniques: CASE pivot, LEFT-safe aggregation, derived classification.
SELECT country, region,
       SUM(CASE WHEN brand = 'Nike'   THEN 1 ELSE 0 END)                    AS nike_factories,
       SUM(CASE WHEN brand = 'Adidas' THEN 1 ELSE 0 END)                    AS adidas_factories,
       SUM(CASE WHEN brand = 'Nike'   THEN monthly_output ELSE 0 END)       AS nike_output,
       SUM(CASE WHEN brand = 'Adidas' THEN monthly_output ELSE 0 END)       AS adidas_output,
       CASE WHEN SUM(brand = 'Nike') = SUM(brand = 'Adidas') THEN 'Symmetric'
            WHEN SUM(brand = 'Nike') = 0 OR SUM(brand = 'Adidas') = 0 THEN 'Single-brand presence'
            ELSE 'Asymmetric' END                                           AS footprint_pattern
FROM vw_factory_flat
GROUP BY country, region
ORDER BY nike_factories + adidas_factories DESC, country;
