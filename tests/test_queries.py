"""Tests that every analysis query runs and returns correct, expected results."""
import importlib.util
from io import StringIO
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("run_queries", ROOT / "sql" / "run_queries.py")
run_queries = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_queries)


@pytest.fixture(scope="module")
def results(warehouse, tmp_path_factory):
    return run_queries.run_all(warehouse, tmp_path_factory.mktemp("qr"))


def test_between_6_and_10_queries_all_run(results):
    assert 6 <= len(results) <= 10
    assert all(len(df) > 0 for df in results.values())


def test_queries_use_window_functions_and_ctes():
    text = "\n".join(p.read_text().upper() for p in (ROOT / "sql" / "analysis").glob("*.sql"))
    for token in ["WITH ", "RANK()", "LAG(", "PERCENT_RANK()", "OVER (", "CASE", "JOIN"]:
        assert token in text, token


def test_brand_scorecard_matches_pandas(results):
    df = pd.read_csv(ROOT / "data" / "nike_adidas_factories.csv")
    sc = results["01_brand_scorecard"].set_index("brand")
    for brand, g in df.groupby("brand"):
        assert sc.loc[brand, "factories"] == len(g)
        assert sc.loc[brand, "total_monthly_output"] == g["monthly_output"].sum()
        assert sc.loc[brand, "output_per_worker"] == pytest.approx(g["monthly_output"].sum() / g["workers"].sum(), abs=0.01)
    assert sc["pct_of_combined_output"].sum() == pytest.approx(100, abs=0.1)


def test_hhi_matches_pandas(results):
    df = pd.read_csv(ROOT / "data" / "nike_adidas_factories.csv")
    hhi = results["03_country_concentration_hhi"].set_index("brand")["hhi"]
    for brand, g in df.groupby("brand"):
        share = g.groupby("country")["monthly_output"].sum() / g["monthly_output"].sum() * 100
        assert hhi[brand] == pytest.approx((share ** 2).sum(), abs=0.1)


def test_efficiency_rank_is_consistent(results):
    r = results["02_efficiency_rank"]
    assert r["overall_rank"].min() == 1 and r["percentile_rank"].between(0, 1).all()
    assert r.iloc[0]["factory_code"] == r.sort_values("output_per_worker", ascending=False).iloc[0]["factory_code"]
    assert (r.groupby("brand")["brand_rank"].min() == 1).all()


def test_pareto_running_total_reaches_100(results):
    r = results["06_output_pareto_running_total"]
    assert (r.groupby("brand")["cumulative_share_pct"].max() == 100.0).all()
    assert r.groupby("brand")["running_output"].apply(lambda s: s.is_monotonic_increasing).all()


def test_lag_first_row_per_brand_has_no_predecessor(results):
    r = results["07_cost_ladder_lag"]
    first = r.groupby("brand").head(1)
    assert first["next_cheaper_factory"].isna().all() and (first["step_up_vs_next_cheaper"] == 0).all()
    assert (r["step_up_vs_next_cheaper"] >= 0).all()


def test_crosstab_totals_and_germany_is_single_brand(results):
    r = results["04_country_brand_crosstab"].set_index("country")
    assert r["nike_factories"].sum() == 20 and r["adidas_factories"].sum() == 22
    assert r.loc["Germany", "footprint_pattern"] == "Single-brand presence"
    assert r.loc["Vietnam", "footprint_pattern"] == "Symmetric"


def test_frontier_has_no_dominated_factory(results):
    f = results["09_efficiency_frontier"]
    df = pd.read_csv(ROOT / "data" / "nike_adidas_factories.csv")
    df["opw"] = df["monthly_output"] / df["workers"]
    for _, a in f.iterrows():
        row = df[df["factory_code"] == a["factory_code"]].iloc[0]
        dom = df[(df["opw"] >= row["opw"]) & (df["production_cost"] <= row["production_cost"])
                 & ((df["opw"] > row["opw"]) | (df["production_cost"] < row["production_cost"]))]
        assert dom.empty


def test_head_to_head_pairs_only_shared_cities(results):
    r = results["08_head_to_head_same_city"]
    assert (r["nike_factory"].str[:2] == "NK").all() and (r["adidas_factory"].str[:2] == "AD").all()


def test_committed_csv_outputs_are_current(results):
    for name, df in results.items():
        committed = pd.read_csv(ROOT / "docs" / "query_results" / f"{name}.csv")
        pd.testing.assert_frame_equal(committed, pd.read_csv(StringIO(df.to_csv(index=False))))
