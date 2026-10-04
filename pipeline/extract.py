"""Extract: read the source CSV and (for reconciliation) the rows in the PostgreSQL script."""
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "nike_adidas_factories.csv"
SQL_PATH = ROOT / "sql" / "nike_adidas_factories.sql"

SQL_COLUMNS = ["brand", "factory_code", "country", "city", "year", "workers",
               "monthly_output", "production_cost", "latitude", "longitude"]

_ROW = re.compile(
    r"^\s*\('(?P<brand>Nike|Adidas)',\s*'(?P<factory_code>[^']+)',\s*'(?P<country>[^']+)',"
    r"\s*'(?P<city>[^']+)',\s*(?P<year>\d{4}),\s*(?P<workers>\d+),\s*(?P<monthly_output>\d+),"
    r"\s*(?P<production_cost>[\d.]+),\s*(?P<latitude>-?[\d.]+),\s*(?P<longitude>-?[\d.]+)\)",
    re.M,
)


def extract_csv(path: Path = CSV_PATH) -> pd.DataFrame:
    """Read the raw CSV exactly as stored (no cleaning)."""
    return pd.read_csv(path)


def extract_sql_rows(path: Path = SQL_PATH) -> pd.DataFrame:
    """Parse the INSERT rows of the PostgreSQL script so they can be reconciled with the CSV."""
    rows = [m.groupdict() for m in _ROW.finditer(Path(path).read_text(encoding="utf-8"))]
    df = pd.DataFrame(rows, columns=SQL_COLUMNS)
    for col in ["year", "workers", "monthly_output"]:
        df[col] = df[col].astype(int)
    for col in ["production_cost", "latitude", "longitude"]:
        df[col] = df[col].astype(float)
    return df
