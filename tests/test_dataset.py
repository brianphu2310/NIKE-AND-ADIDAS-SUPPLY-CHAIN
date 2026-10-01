"""Data-quality checks: the CSV is clean, and the SQL script loads the same rows."""
import re
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "nike_adidas_factories.csv"
SQL = ROOT / "sql" / "nike_adidas_factories.sql"
COLUMNS = ["factory_id", "brand", "factory_code", "country", "city", "year",
           "workers", "monthly_output", "production_cost", "latitude", "longitude"]


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(CSV)


def test_schema_and_size(df):
    assert list(df.columns) == COLUMNS
    assert len(df) == 42
    assert df["country"].nunique() == 11


def test_no_missing_values_or_duplicate_keys(df):
    assert df.isna().sum().sum() == 0
    assert df["factory_id"].is_unique
    assert df["factory_code"].is_unique


def test_values_are_in_valid_ranges(df):
    assert set(df["brand"]) == {"Nike", "Adidas"}
    assert set(df["year"]) <= {2023, 2024}
    assert (df[["workers", "monthly_output", "production_cost"]] > 0).all().all()
    assert df["latitude"].between(-90, 90).all()
    assert df["longitude"].between(-180, 180).all()


def test_factory_code_matches_brand(df):
    prefix = df["brand"].map({"Nike": "NK", "Adidas": "AD"})
    assert (df["factory_code"].str[:2] == prefix).all()


def test_sql_script_has_same_row_count_as_csv(df):
    sql = SQL.read_text(encoding="utf-8")
    rows = re.findall(r"^\s*\('(?:Nike|Adidas)'", sql, flags=re.M)
    assert len(rows) == len(df)
