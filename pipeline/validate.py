"""Validate: data-quality checks that run before anything is loaded.

Each check returns a CheckResult. ERROR failures stop the load; WARN failures are reported only.
"""
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = ["factory_id", "brand", "factory_code", "country", "city", "year", "workers",
                    "monthly_output", "production_cost", "latitude", "longitude"]
BRAND_PREFIX = {"Nike": "NK", "Adidas": "AD"}
# Reference data: ISO-3166 alpha-2 code used inside factory_code -> (country, region).
# The region grouping is an analyst-defined classification, not a field of the source data.
COUNTRY_REF = {
    "VN": ("Vietnam", "Southeast Asia"), "ID": ("Indonesia", "Southeast Asia"),
    "TH": ("Thailand", "Southeast Asia"), "CN": ("China", "East Asia"),
    "JP": ("Japan", "East Asia"), "KR": ("South Korea", "East Asia"),
    "IN": ("India", "South Asia"), "US": ("USA", "North America"),
    "MX": ("Mexico", "Latin America"), "BR": ("Brazil", "Latin America"),
    "DE": ("Germany", "Europe"),
}
RANGES = {  # column: (min, max) inclusive plausibility ranges
    "workers": (1, 200_000), "monthly_output": (1, 10_000_000),
    "production_cost": (0.01, 200.0), "latitude": (-90, 90), "longitude": (-180, 180),
    "year": (2023, 2024),
}
CODE_PATTERN = r"^(NK|AD)-[A-Z]{2}-\d{2}$"


class DataQualityError(RuntimeError):
    pass


@dataclass
class CheckResult:
    name: str
    category: str
    passed: bool
    detail: str
    severity: str = "ERROR"  # ERROR blocks the load, WARN does not

    @property
    def status(self) -> str:
        return "PASS" if self.passed else ("FAIL" if self.severity == "ERROR" else "WARN")


def _fmt(x) -> str:
    return f"{x:,.2f}".rstrip("0").rstrip(".")


def _res(name, category, bad, ok_detail, severity="ERROR"):
    """bad: list of offending descriptions (empty = pass)."""
    detail = ok_detail if not bad else f"{len(bad)} issue(s): " + "; ".join(map(str, bad[:5]))
    return CheckResult(name, category, not bad, detail, severity)


def run_checks(df: pd.DataFrame, sql_df: pd.DataFrame | None = None) -> list[CheckResult]:
    results: list[CheckResult] = []
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    results.append(_res("Required columns present", "schema", missing, f"{len(REQUIRED_COLUMNS)} columns found"))
    if missing:  # nothing else can run
        return results
    results.append(_res("Table is not empty", "schema", [] if len(df) else ["0 rows"], f"{len(df)} rows"))

    for col in REQUIRED_COLUMNS:  # completeness
        n = int(df[col].isna().sum() + (df[col].astype(str).str.strip() == "").sum())
        results.append(_res(f"No nulls/blanks in `{col}`", "completeness", [f"{n} null/blank"] if n else [], "0 nulls"))

    for keys in (["factory_id"], ["factory_code"], ["brand", "country", "city"]):  # uniqueness
        dups = df[df.duplicated(keys, keep=False)]
        results.append(_res(f"Unique key ({', '.join(keys)})", "uniqueness",
                            sorted(dups[keys[-1]].astype(str).unique()), "no duplicates"))

    for col, (lo, hi) in RANGES.items():  # ranges
        vals = pd.to_numeric(df[col], errors="coerce")
        bad = df.loc[~vals.between(lo, hi), "factory_code"].tolist()
        results.append(_res(f"`{col}` within [{lo}, {hi}]", "range", bad,
                            f"observed {_fmt(vals.min())} to {_fmt(vals.max())}"))

    bad = df.loc[~df["brand"].isin(BRAND_PREFIX), "factory_code"].tolist()
    results.append(_res("`brand` in {Nike, Adidas}", "domain", bad, "all brands valid"))
    bad = df.loc[~df["factory_code"].astype(str).str.match(CODE_PATTERN), "factory_code"].tolist()
    results.append(_res("`factory_code` matches `AA-CC-NN`", "domain", bad, "all codes well-formed"))

    # referential checks against the reference table COUNTRY_REF
    iso = df["factory_code"].astype(str).str.split("-").str[1]
    bad = df.loc[~iso.isin(COUNTRY_REF), "factory_code"].tolist()
    results.append(_res("Country code in code exists in country reference", "referential", bad, "all ISO codes known"))
    bad = df.loc[~df["country"].isin([v[0] for v in COUNTRY_REF.values()]), "country"].unique().tolist()
    results.append(_res("`country` exists in country reference", "referential", bad, "all countries known"))
    expected = iso.map(lambda c: COUNTRY_REF.get(c, (None,))[0])
    bad = df.loc[expected != df["country"], "factory_code"].tolist()
    results.append(_res("Country in `factory_code` agrees with `country`", "consistency", bad, "consistent"))
    prefix = df["brand"].map(BRAND_PREFIX)
    bad = df.loc[df["factory_code"].astype(str).str[:2] != prefix, "factory_code"].tolist()
    results.append(_res("Brand prefix in `factory_code` agrees with `brand`", "consistency", bad, "consistent"))
    spread = df.groupby(["country", "city"])[["latitude", "longitude"]].nunique().max(axis=1)
    results.append(_res("Same city has one coordinate pair", "consistency",
                        spread[spread > 1].index.tolist(), "one pair per city"))

    # statistical outlier screen (WARN only): output per worker by IQR rule
    opw = df["monthly_output"] / df["workers"]
    q1, q3 = opw.quantile([.25, .75])
    lo, hi = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
    bad = df.loc[(opw < lo) | (opw > hi), "factory_code"].tolist()
    results.append(_res("Output-per-worker outliers (1.5xIQR)", "outlier", bad,
                        f"none outside [{lo:.1f}, {hi:.1f}]", severity="WARN"))

    if sql_df is not None:  # cross-source reconciliation CSV vs SQL INSERTs
        cols = [c for c in sql_df.columns]
        a = df[cols].sort_values("factory_code").reset_index(drop=True)
        b = sql_df[cols].sort_values("factory_code").reset_index(drop=True)
        same = len(a) == len(b) and a.round(4).equals(b.round(4))
        results.append(CheckResult("CSV equals INSERT rows in SQL script", "reconciliation", same,
                                   f"{len(a)} CSV rows vs {len(b)} SQL rows"
                                   + ("" if same else " - values differ")))
    return results


def raise_on_errors(results: list[CheckResult]) -> None:
    failed = [r for r in results if r.status == "FAIL"]
    if failed:
        raise DataQualityError("; ".join(f"{r.name}: {r.detail}" for r in failed))


def write_report(results: list[CheckResult], path: Path, n_rows: int, source: str) -> None:
    passed = sum(r.status == "PASS" for r in results)
    warns = sum(r.status == "WARN" for r in results)
    fails = sum(r.status == "FAIL" for r in results)
    lines = ["# Data Quality Report", "",
             "_Generated by `python -m pipeline` (`pipeline/validate.py`). Re-run to refresh._", "",
             f"- Source: `{source}` ({n_rows} rows)",
             f"- Checks: {len(results)} total, **{passed} passed**, {warns} warnings, {fails} failures", "",
             "| Status | Category | Check | Detail |", "|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r.status} | {r.category} | {r.name} | {r.detail} |")
    lines += ["", "ERROR-severity failures stop the load into the warehouse; WARN items are informational.", ""]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")
