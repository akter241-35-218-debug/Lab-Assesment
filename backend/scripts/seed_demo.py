"""Load data/sample_*.csv into the configured database.

    python -m backend.scripts.seed_demo
"""
from pathlib import Path

from ..app import models  # noqa: F401
from ..app.database import Base, SessionLocal, engine
from ..app.services import csv_import

DATA = Path(__file__).resolve().parents[2] / "data"


def main():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for label, fn, fname in (
            ("companies", csv_import.import_companies, "sample_companies.csv"),
            ("medicines", csv_import.import_medicines, "sample_medicines.csv"),
            ("sales", csv_import.import_sales, "sample_sales.csv"),
        ):
            r = fn(db, fname, (DATA / fname).read_bytes())
            print(f"{label}: created={r.created} updated={r.updated} failed={r.failed}")
            for e in r.errors[:5]:
                print("   row", e.row, e.error)


if __name__ == "__main__":
    main()
