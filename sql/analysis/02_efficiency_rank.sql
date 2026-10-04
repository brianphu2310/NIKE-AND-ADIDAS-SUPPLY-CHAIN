-- 02 Efficiency ranking: output per worker, ranked overall and within brand.
-- Techniques: RANK() with and without PARTITION BY, PERCENT_RANK().
SELECT factory_code, brand, country, city,
       output_per_worker,
       RANK() OVER (ORDER BY output_per_worker DESC)                       AS overall_rank,
       RANK() OVER (PARTITION BY brand ORDER BY output_per_worker DESC)    AS brand_rank,
       ROUND(PERCENT_RANK() OVER (ORDER BY output_per_worker), 3)          AS percentile_rank
FROM vw_factory_flat
ORDER BY overall_rank, factory_code;
