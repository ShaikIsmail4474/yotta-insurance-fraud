
"""Build a SQLite database from generated insurance CSV files."""

import sqlite3
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "generated"
SCHEMA_PATH = ROOT / "docs" / "schema.sql"
DB_PATH = ROOT / "data" / "insurance_fraud.db"

TABLES = [
    "claimants",
    "providers",
    "policies",
    "incidents",
    "claims",
    "invoices",
    "payments",
    "relationship_edges",
]


def main() -> None:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema not found: {SCHEMA_PATH}")

    for table in TABLES:
        csv_path = DATA_DIR / f"{table}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(
                f"Missing {csv_path}. Run python src/export_data.py first."
            )

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Rebuild the database from scratch on each run.
    if DB_PATH.exists():
        DB_PATH.unlink()

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        connection.executescript(schema)

        # Import parent tables before dependent tables.
        for table in TABLES:
            csv_path = DATA_DIR / f"{table}.csv"
            dataframe = pd.read_csv(csv_path)

            # SQLite converts True/False to integer values.
            if table == "relationship_edges":
                dataframe["is_planted_suspicious"] = (
                    dataframe["is_planted_suspicious"].astype(int)
                )

            dataframe.to_sql(
                table,
                connection,
                if_exists="append",
                index=False,
            )
            print(f"Imported {table}: {len(dataframe)} rows")

        # Check database foreign-key integrity.
        foreign_key_errors = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if foreign_key_errors:
            raise RuntimeError(
                f"Foreign-key violations found: {foreign_key_errors[:10]}"
            )

        # Confirm each table's imported row count.
        print("\nDatabase row counts:")
        for table in TABLES:
            count = connection.execute(
                f'SELECT COUNT(*) FROM "{table}"'
            ).fetchone()[0]
            print(f"{table}: {count}")

        integrity = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]
        print(f"\nSQLite integrity check: {integrity}")

        if integrity != "ok":
            raise RuntimeError(f"Database integrity check failed: {integrity}")

    print(f"\nDatabase created successfully: {DB_PATH}")


if __name__ == "__main__":
    main()
