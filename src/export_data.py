
"""Generate and export synthetic insurance data to CSV and JSON."""

import json
from pathlib import Path

import pandas as pd

from generator import GeneratorConfig, generate_master_records


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "generated"


def export_records(records: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for entity_name, rows in records.items():
        # Write CSV
        csv_path = OUTPUT_DIR / f"{entity_name}.csv"
        pd.DataFrame(rows).to_csv(csv_path, index=False)

        # Write JSON
        json_path = OUTPUT_DIR / f"{entity_name}.json"
        with json_path.open("w", encoding="utf-8") as file:
            json.dump(rows, file, indent=2, ensure_ascii=False)

        print(f"Exported {entity_name}: {len(rows)} records")


def main() -> None:
    config = GeneratorConfig(seed=42)
    records = generate_master_records(config)

    export_records(records)

    print(f"\nAll CSV and JSON files saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
