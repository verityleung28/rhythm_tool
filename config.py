"""
Central configuration for the rhythm-battery first draft.

This file intentionally keeps all experiment settings in one place so that:
1. Experiment design choices are easy to read.
2. Runtime code in main/task logic stays simple.
3. Future analysis code can import the same constants.
"""

from pathlib import Path

# Project paths are defined once here so other modules do not hardcode folders.
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Core timing settings.
BPM: float = 120.0
SECONDS_PER_BEAT: float = 60.0 / BPM

# Trial structure settings.
# Countdown is not part of expected beat numbering and should be ignored in
# matching/analysis, but we keep it configurable here for runtime use later.
COUNTDOWN_BEATS: int = 4
CUE_BEATS: int = 12
FADE_BEATS: int = 4
SILENCE_BEATS: int = 16

# Runtime settings for first-draft live trial execution.
# Countdown is a simple whole-second visual/text countdown before trial start.
COUNTDOWN_SECONDS: int = 3

# First-draft cue sound settings.
# For now this is a simple short beep; audio sophistication can come later.
CUE_FREQUENCY_HZ: int = 880
CUE_DURATION_SECONDS: float = 0.04

# Keyboard input settings.
TAP_KEY_NAME: str = "space"

# Scheduler settings.
# This controls how often we wake up while waiting for the next beat time.
SCHEDULER_SLEEP_SECONDS: float = 0.002

# Main script behavior.
SAVE_RAW_CSV_DEFAULT: bool = True

# Experimental conditions for the battery.
CONDITIONS = (
    "synchronization",
    "metronome_continuation",
    "music_continuation",
)
DEFAULT_CONDITION = "synchronization"


def total_trial_beats() -> int:
    """Return the number of expected beats from cue+fade+silence phases."""
    return CUE_BEATS + FADE_BEATS + SILENCE_BEATS


def validate_config() -> None:
    """
    Raise ValueError if critical settings are invalid.

    This is called by main.py as a lightweight safety check so timing bugs
    are caught early while iterating on the first draft.
    """
    if BPM <= 0:
        raise ValueError("BPM must be > 0.")

    beat_counts = {
        "COUNTDOWN_BEATS": COUNTDOWN_BEATS,
        "CUE_BEATS": CUE_BEATS,
        "FADE_BEATS": FADE_BEATS,
        "SILENCE_BEATS": SILENCE_BEATS,
    }
    for name, value in beat_counts.items():
        if value < 0:
            raise ValueError(f"{name} must be >= 0.")

    if total_trial_beats() <= 0:
        raise ValueError("Cue + fade + silence beats must be greater than zero.")

    if COUNTDOWN_SECONDS < 0:
        raise ValueError("COUNTDOWN_SECONDS must be >= 0.")

    if CUE_FREQUENCY_HZ <= 0:
        raise ValueError("CUE_FREQUENCY_HZ must be > 0.")

    if CUE_DURATION_SECONDS < 0:
        raise ValueError("CUE_DURATION_SECONDS must be >= 0.")

    if TAP_KEY_NAME.strip().lower() != "space":
        raise ValueError("First draft currently supports TAP_KEY_NAME='space' only.")

    if SCHEDULER_SLEEP_SECONDS <= 0:
        raise ValueError("SCHEDULER_SLEEP_SECONDS must be > 0.")
