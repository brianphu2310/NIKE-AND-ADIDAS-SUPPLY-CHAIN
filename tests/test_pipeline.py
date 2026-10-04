"""Tests for the extract -> validate -> transform -> load pipeline."""
import pandas as pd
import pytest

from pipeline import docgen, extract, transform, validate

ROOT = extract.ROOT


@pytest.fixture()
def raw():
    return extract.extract_csv()


def _by_name(results):
    return {r.name: r for r in results}


def test_clean_source_passes_all_checks(raw):
    results = validate.run_checks(raw, extract.extract_sql_rows())
    assert len(results) >= 25
    assert [r.name for r in results if r.status != "PASS"] == []


def test_sql_script_rows_are_parsed_and_match_csv(raw):
    sql_df = extract.extract_sql_rows()
    assert len(sql_df) == len(raw) == 42


@pytest.mark.parametrize("mutate, check", [
    (lambda d: d.assign(workers=d["workers"].where(d.index != 0)), "No nulls/blanks in `workers`"),
    (lambda d: pd.concat([d, d.iloc[[0]]]), "Unique key (factory_code)"),
    (lambda d: d.assign(monthly_output=d["monthly_output"].where(d.index != 0, -5)), "`monthly_output` within [1, 10000000]"),
    (lambda d: d.assign(latitude=d["latitude"].where(d.index != 0, 123.0)), "`latitude` within [-90, 90]"),
    (lambda d: d.assign(country=d["country"].where(d.index != 0, "Atlantis")), "`country` exists in country reference"),
    (lambda d: d.assign(brand=d["brand"].where(d.index != 0, "Puma")), "`brand` in {Nike, Adidas}"),
    (lambda d: d.assign(factory_code=d["factory_code"].where(d.index != 0, "BAD")), "`factory_code` matches `AA-CC-NN`"),
])
def test_each_check_detects_injected_defect(raw, mutate, check):
    bad = mutate(raw.copy())
    results = _by_name(validate.run_checks(bad))
    assert results[check].status == "FAIL"


def test_reconciliation_detects_csv_sql_drift(raw):
    drifted = raw.copy()
    drifted.loc[0, "workers"] += 1
    results = _by_name(validate.run_checks(drifted, extract.extract_sql_rows()))
    assert results["CSV equals INSERT rows in SQL script"].status == "FAIL"


def test_outlier_check_warns_but_does_not_block(raw):
    odd = raw.copy()
    odd.loc[0, "workers"] = 100  # absurd output per worker
    results = validate.run_checks(odd)
    outlier = _by_name(results)["Output-per-worker outliers (1.5xIQR)"]
    assert outlier.status == "WARN"
    validate.raise_on_errors(results)  # warnings must not raise


def test_errors_block_the_load(raw):
    with pytest.raises(validate.DataQualityError):
        validate.raise_on_errors(validate.run_checks(raw.drop(columns=["workers"])))


def test_transform_keys_and_derived_features(raw):
    m = transform.build_model(raw)
    fact, fac = m["fact_factory_snapshot"], m["dim_factory"]
    assert len(fact) == len(fac) == 42
    assert fac["factory_key"].tolist() == list(range(1, 43))
    row = fact.merge(fac, on="factory_key").set_index("factory_code").loc["AD-ID-02"]
    assert row["output_per_worker"] == 80.0  # 2.8M units / 35k workers (README: Surabaya 80)
    assert row["cost_index_per_million_units"] == round(45.0 / 2_800_000 * 1e6, 2)
    assert row["size_tier"] == "Large" and row["cost_band"] == "Medium"


def test_transform_is_deterministic(raw):
    a, b = transform.build_model(raw), transform.build_model(raw.sample(frac=1, random_state=1))
    for name in a:
        pd.testing.assert_frame_equal(a[name], b[name])


def test_tier_boundaries():
    assert transform._tier(25_000, transform.SIZE_TIERS) == "Large"
    assert transform._tier(24_999, transform.SIZE_TIERS) == "Medium"
    assert transform._tier(9_999, transform.SIZE_TIERS) == "Small"
    assert transform._tier(50.0, transform.COST_BANDS) == "High"
    assert transform._tier(39.99, transform.COST_BANDS) == "Low"


def test_load_row_counts_and_constraints(con):
    counts = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in
              ["dim_brand", "dim_year", "dim_country", "dim_location", "dim_factory", "fact_factory_snapshot"]}
    assert counts == {"dim_brand": 2, "dim_year": 2, "dim_country": 11, "dim_location": 31,
                      "dim_factory": 42, "fact_factory_snapshot": 42}
    assert con.execute("PRAGMA foreign_key_check").fetchall() == []
    with pytest.raises(Exception):  # FK is enforced
        con.execute("INSERT INTO dim_factory VALUES (999, 999, 'ZZ', 99, 99)")


def test_fact_totals_match_source(con, raw):
    s = con.execute("SELECT SUM(workers), SUM(monthly_output) FROM fact_factory_snapshot").fetchone()
    assert s == (int(raw["workers"].sum()), int(raw["monthly_output"].sum()))


def test_indexes_exist(con):
    names = {r[1] for r in con.execute("SELECT * FROM sqlite_master WHERE type='index'")}
    assert {"ix_fact_brand", "ix_fact_country", "ix_fact_location", "ix_fact_year"} <= names


def test_data_quality_report_written(warehouse):
    text = (warehouse.parent / "DATA_QUALITY.md").read_text(encoding="utf-8")
    assert "# Data Quality Report" in text and "0 failures" in text


def test_committed_dictionary_matches_warehouse(warehouse):
    assert docgen.build(warehouse) == (ROOT / "docs" / "DATA_DICTIONARY.md").read_text(encoding="utf-8")


def test_committed_quality_report_is_current(warehouse):
    assert (warehouse.parent / "DATA_QUALITY.md").read_text(encoding="utf-8") == \
        (ROOT / "docs" / "DATA_QUALITY.md").read_text(encoding="utf-8")


def test_every_warehouse_column_is_documented(con):
    for table, cols in docgen.DESCRIPTIONS.items():
        actual = [r[1] for r in con.execute(f"PRAGMA table_info({table})")]
        assert sorted(actual) == sorted(cols)
