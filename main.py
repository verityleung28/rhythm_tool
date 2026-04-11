"""
Entry point for rhythm-battery runtime demo.

Current milestone:
- Run one real trial in real time.
- Keep expected beat timeline and raw tap logging separate.
- Optionally save raw trial outputs to data/raw/.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from config import (
    DEFAULT_CONDITION,
    RAW_DATA_DIR,
    SAVE_RAW_CSV_DEFAULT,
    validate_config,
)
from task_logic import generate_trial_timeline, run_trial


def _write_csv(
    path: Path,
    rows: list[dict[str, Any]],
    fieldnames: list[str] | None = None,
) -> None:
    """Write rows to CSV, including headers when field names are available."""
    path.parent.mkdir(parents=True, exist_ok=True)

    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []

    if not fieldnames:
        path.write_text("", encoding="utf-8")
        return

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save_trial_output(
    trial_id: str,
    condition: str,
    timeline_rows: list[dict[str, Any]],
    raw_tap_rows: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> dict[str, Path]:
    """
    Save raw trial outputs into `data/raw/`.

    Files saved:
    - expected beats CSV
    - raw taps CSV
    - metadata JSON
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    safe_condition = condition.replace(" ", "_")
    prefix = f"{trial_id}_{safe_condition}"

    timeline_path = RAW_DATA_DIR / f"{prefix}_expected_beats.csv"
    taps_path = RAW_DATA_DIR / f"{prefix}_raw_taps.csv"
    metadata_path = RAW_DATA_DIR / f"{prefix}_metadata.json"

    _write_csv(
        timeline_path,
        timeline_rows,
        fieldnames=["condition", "trial_id", "phase", "beat_number", "expected_time"],
    )
    _write_csv(
        taps_path,
        raw_tap_rows,
        fieldnames=["condition", "trial_id", "tap_index", "tap_time", "tap_time_unix"],
    )
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return {
        "timeline_csv": timeline_path,
        "raw_taps_csv": taps_path,
        "metadata_json": metadata_path,
    }


def run_single_trial_demo(save_raw_csv: bool = SAVE_RAW_CSV_DEFAULT) -> None:
    """
    Run one first-draft live trial.

    This keeps the flow intentionally simple so it is easy to read and test.
    """
    validate_config()

    condition = DEFAULT_CONDITION
    trial_id = f"trial_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Expected beat timeline is fixed mathematically and does not depend on taps.
    timeline = generate_trial_timeline(
        condition=condition,
        trial_id=trial_id,
        start_time=0.0,
    )

    print("rhythm-battery live trial demo")
    print("=" * 30)
    print(f"Condition: {condition}")
    print(f"Trial ID: {trial_id}")
    print("Tap SPACE during the trial window.\n")

    result = run_trial(
        condition=condition,
        trial_id=trial_id,
        timeline=timeline,
        verbose=True,
    )

    timeline_rows = result["timeline_rows"]
    raw_tap_rows = result["raw_tap_rows"]
    metadata = result["trial_metadata"]

    print("\nTrial complete.")
    print(f"Expected beats: {len(timeline_rows)}")
    print(f"Taps logged: {len(raw_tap_rows)}")

    preview_count = min(5, len(raw_tap_rows))
    if preview_count > 0:
        print("First tap times (s):")
        for row in raw_tap_rows[:preview_count]:
            print(f"  tap_index={row['tap_index']}, tap_time={row['tap_time']:.4f}")
    else:
        print("No taps were logged.")

    if save_raw_csv:
        saved_paths = save_trial_output(
            trial_id=trial_id,
            condition=condition,
            timeline_rows=timeline_rows,
            raw_tap_rows=raw_tap_rows,
            metadata=metadata,
        )
        print("\nSaved raw output files:")
        for label, path in saved_paths.items():
            print(f"  {label}: {path}")


if __name__ == "__main__":
    try:
        run_single_trial_demo()
    except Exception as exc:
        # Basic top-level error handling for first-draft runtime script.
        print(f"Runtime error: {exc}")
