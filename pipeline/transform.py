"""Transform: normalise, derive features and build dimension/fact tables with surrogate keys."""
import pandas as pd

from .validate import BRAND_PREFIX, COUNTRY_REF

SIZE_TIERS = [(25_000, "Large"), (10_000, "Medium"), (0, "Small")]  # analyst-defined, by workers
COST_BANDS = [(50.0, "High"), (40.0, "Medium"), (0.0, "Low")]       # analyst-defined, by cost index


def _tier(value: float, bands) -> str:
    return next(label for floor, label in bands if value >= floor)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["brand", "factory_code", "country", "city"]:
        out[col] = out[col].astype(str).str.strip()
    out["factory_code"] = out["factory_code"].str.upper()
    out["brand"] = out["brand"].str.title()
    for col in ["factory_id", "year", "workers", "monthly_output"]:
        out[col] = out[col].astype(int)
    for col in ["production_cost", "latitude", "longitude"]:
        out[col] = out[col].astype(float)
    return out.drop_duplicates("factory_code").sort_values("factory_code").reset_index(drop=True)


def build_model(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    df = clean(df)
    iso_of = {v[0]: k for k, v in COUNTRY_REF.items()}

    dim_brand = pd.DataFrame({"brand_name": sorted(df["brand"].unique())})
    dim_brand.insert(0, "brand_key", range(1, len(dim_brand) + 1))
    dim_brand["code_prefix"] = dim_brand["brand_name"].map(BRAND_PREFIX)

    dim_year = pd.DataFrame({"year_key": sorted(df["year"].unique())})

    dim_country = pd.DataFrame({"country_name": sorted(df["country"].unique())})
    dim_country.insert(0, "country_key", range(1, len(dim_country) + 1))
    dim_country["iso2"] = dim_country["country_name"].map(iso_of)
    dim_country["region"] = dim_country["iso2"].map(lambda i: COUNTRY_REF[i][1])

    loc = df.groupby(["country", "city"], as_index=False)[["latitude", "longitude"]].first()
    loc = loc.merge(dim_country[["country_key", "country_name"]], left_on="country", right_on="country_name")
    dim_location = loc.sort_values(["country", "city"]).reset_index(drop=True)
    dim_location.insert(0, "location_key", range(1, len(dim_location) + 1))
    dim_location = dim_location[["location_key", "country_key", "city", "latitude", "longitude"]]

    m = (df.merge(dim_brand[["brand_key", "brand_name"]], left_on="brand", right_on="brand_name")
           .merge(dim_country[["country_key", "country_name"]], left_on="country", right_on="country_name")
           .merge(dim_location[["location_key", "country_key", "city"]], on=["country_key", "city"]))
    m = m.sort_values("factory_code").reset_index(drop=True)
    m.insert(0, "factory_key", range(1, len(m) + 1))

    dim_factory = m[["factory_key", "factory_id", "factory_code", "brand_key", "location_key"]].rename(
        columns={"factory_id": "source_factory_id"})
    fact = m[["factory_key", "brand_key", "location_key", "country_key"]].copy()
    fact["year_key"] = m["year"]
    fact["workers"] = m["workers"]
    fact["monthly_output"] = m["monthly_output"]
    fact["production_cost_index"] = m["production_cost"]
    fact["output_per_worker"] = (m["monthly_output"] / m["workers"]).round(2)
    fact["cost_index_per_million_units"] = (m["production_cost"] / m["monthly_output"] * 1_000_000).round(2)
    fact["size_tier"] = m["workers"].map(lambda v: _tier(v, SIZE_TIERS))
    fact["cost_band"] = m["production_cost"].map(lambda v: _tier(v, COST_BANDS))
    return {"dim_brand": dim_brand, "dim_year": dim_year, "dim_country": dim_country,
            "dim_location": dim_location, "dim_factory": dim_factory, "fact_factory_snapshot": fact}
