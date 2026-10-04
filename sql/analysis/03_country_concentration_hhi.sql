-- 03 Geographic concentration: Herfindahl-Hirschman Index of monthly output by country, per brand.
-- HHI = sum of squared output shares (in %); 10,000 = single-country, lower = more diversified.
-- Techniques: two-step CTE, window SUM() OVER (PARTITION BY), CASE banding.
WITH country_output AS (
    SELECT brand, country, SUM(monthly_output) AS output
    FROM vw_factory_flat
    GROUP BY brand, country
),
shares AS (
    SELECT brand, country, output,
           100.0 * output / SUM(output) OVER (PARTITION BY brand) AS share_pct
    FROM country_output
),
hhi AS (
    SELECT brand,
           ROUND(SUM(share_pct * share_pct), 1) AS hhi,
           COUNT(*)                             AS countries,
           MAX(share_pct)                       AS top_country_share_pct
    FROM shares
    GROUP BY brand
)
SELECT brand, countries, ROUND(top_country_share_pct, 1) AS top_country_share_pct, hhi,
       CASE WHEN hhi < 1500 THEN 'Unconcentrated'
            WHEN hhi < 2500 THEN 'Moderately concentrated'
            ELSE 'Highly concentrated' END AS concentration_band
FROM hhi
ORDER BY brand;
