
"""Check the SQLite database structure and relationships."""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "insurance_fraud.db"


def main():
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        print("DATABASE VALIDATION")
        print("-" * 40)

        # Check database integrity
        integrity = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]
        print(f"Integrity check: {integrity}")

        # Check foreign-key violations
        violations = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()
        print(f"Foreign-key violations: {len(violations)}")

        # Show table counts
        tables = [
            "claimants",
            "providers",
            "policies",
            "incidents",
            "claims",
            "invoices",
            "payments",
            "relationship_edges",
        ]

        print("\nTABLE COUNTS")
        for table in tables:
            count = connection.execute(
                f'SELECT COUNT(*) FROM "{table}"'
            ).fetchone()[0]
            print(f"{table}: {count}")

        if integrity != "ok" or violations:
            raise RuntimeError("Database validation failed.")

        print("\nDatabase checks passed.")


if __name__ == "__main__":
    main()
