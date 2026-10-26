
"""Check that a fixed seed produces identical synthetic data."""

import hashlib
import json

from generator import GeneratorConfig, generate_master_records


def calculate_checksum(rows: list) -> str:
    """Return a stable SHA-256 checksum for a list of records."""
    content = json.dumps(
        rows,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def main() -> None:
    config = GeneratorConfig(seed=42)

    first_run = generate_master_records(config)
    second_run = generate_master_records(config)

    print("Reproducibility check (seed=42)")
    print("-" * 45)

    all_match = True

    for entity_name in first_run:
        first_rows = first_run[entity_name]
        second_rows = second_run[entity_name]

        first_checksum = calculate_checksum(first_rows)
        second_checksum = calculate_checksum(second_rows)

        same_count = len(first_rows) == len(second_rows)
        same_checksum = first_checksum == second_checksum
        passed = same_count and same_checksum

        print(
            f"{entity_name}: "
            f"count={len(first_rows)}, "
            f"checksum_match={same_checksum}, "
            f"{'PASS' if passed else 'FAIL'}"
        )

        if not passed:
            all_match = False

    print("-" * 45)
    print(
        "RESULT: "
        + ("PASS - output is reproducible" if all_match
           else "FAIL - output differs between runs")
    )

    if not all_match:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
