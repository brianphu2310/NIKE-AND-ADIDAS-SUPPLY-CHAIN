import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.__main__ import run  # noqa: E402


@pytest.fixture(scope="session")
def warehouse(tmp_path_factory):
    d = tmp_path_factory.mktemp("wh")
    db = run(d / "warehouse.db", d / "DATA_QUALITY.md")
    return db


@pytest.fixture()
def con(warehouse):
    c = sqlite3.connect(warehouse)
    c.execute("PRAGMA foreign_keys = ON")
    yield c
    c.close()
