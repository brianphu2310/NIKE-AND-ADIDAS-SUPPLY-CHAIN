"""Run the full pipeline: python -m pipeline"""
from pathlib import Path

from . import extract, load, transform, validate

ROOT = Path(__file__).resolve().parents[1]


def run(db_path: Path = load.DB_PATH, report_path: Path = ROOT / "docs" / "DATA_QUALITY.md") -> Path:
    raw = extract.extract_csv()
    results = validate.run_checks(raw, extract.extract_sql_rows())
    validate.write_report(results, report_path, len(raw), "data/nike_adidas_factories.csv")
    validate.raise_on_errors(results)
    model = transform.build_model(raw)
    out = load.load(model, db_path)
    print(f"Loaded {', '.join(f'{k}={len(v)}' for k, v in model.items())} -> {out.name}")
    return out


if __name__ == "__main__":
    run()
