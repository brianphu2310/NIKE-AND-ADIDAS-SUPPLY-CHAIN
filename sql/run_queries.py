"""Run every sql/analysis/*.sql against warehouse.db and write docs/query_results/<name>.csv.

Usage: python sql/run_queries.py   (builds the warehouse first if it does not exist)
"""
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.load import DB_PATH  # noqa: E402

ANALYSIS_DIR = ROOT / "sql" / "analysis"
RESULTS_DIR = ROOT / "docs" / "query_results"


def run_all(db_path: Path = DB_PATH, results_dir: Path = RESULTS_DIR) -> dict[str, pd.DataFrame]:
    if not Path(db_path).exists():
        from pipeline.__main__ import run
        run(db_path)
    results_dir.mkdir(parents=True, exist_ok=True)
    out = {}
    con = sqlite3.connect(db_path)
    try:
        for sql_file in sorted(ANALYSIS_DIR.glob("*.sql")):
            df = pd.read_sql_query(sql_file.read_text(encoding="utf-8"), con)
            df.to_csv(results_dir / f"{sql_file.stem}.csv", index=False)
            out[sql_file.stem] = df
            print(f"{sql_file.name}: {len(df)} rows")
    finally:
        con.close()
    return out


if __name__ == "__main__":
    run_all()
