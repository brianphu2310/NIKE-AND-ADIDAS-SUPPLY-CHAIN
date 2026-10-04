"""Load: create the SQLite warehouse from schema.sql and insert the model tables."""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "warehouse.db"
SCHEMA = Path(__file__).with_name("schema.sql")
LOAD_ORDER = ["dim_brand", "dim_year", "dim_country", "dim_location", "dim_factory", "fact_factory_snapshot"]


def load(model: dict[str, pd.DataFrame], db_path: Path = DB_PATH) -> Path:
    db_path = Path(db_path)
    if db_path.exists():
        db_path.unlink()  # full refresh: the warehouse is rebuilt from source on every run
    con = sqlite3.connect(db_path)
    try:
        con.executescript(SCHEMA.read_text(encoding="utf-8"))
        for table in LOAD_ORDER:
            model[table].to_sql(table, con, if_exists="append", index=False)
        bad = con.execute("PRAGMA foreign_key_check").fetchall()
        if bad:
            raise RuntimeError(f"Foreign key violations after load: {bad[:5]}")
        con.commit()
    finally:
        con.close()
    return db_path
