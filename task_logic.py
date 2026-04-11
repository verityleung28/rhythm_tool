"""
Task logic for rhythm-battery.

This module contains:
1. Fixed timeline generation (expected beats).
2. First-draft real-time trial execution (cue playback + raw tap logging).

Important design rule:
- Expected beats are generated mathematically from experiment settings.
- Raw taps are logged independently during runtime.
- We do NOT match taps to beats here; matching is deferred to analysis.py.
"""

import threading
import time
from typing import Any

from config import (
    BPM,
    CONDITIONS,
    COUNTDOWN_SECONDS,
    CUE_BEATS,
    CUE_DURATION_SECONDS,
    CUE_FREQUENCY_HZ,
    FADE_BEATS,
    SCHEDULER_SLEEP_SECONDS,
    SILENCE_BEATS,
)


def _phase_for_beat(beat_number: int, cue_beats: int, fade_beats: int) -> str:
    """
    Return the phase label for a 1-based beat index.

    Beat numbering starts at the first cue beat.
    Countdown beats are intentionally not represented here.
    """
    cue_end = cue_beats
    fade_end = cue_beats + fade_beats

    if beat_number <= cue_end:
        return "cue"
    if beat_number <= fade_end:
        return "fade"
    return "silence"


def generate_trial_timeline(
    condition: str,
    trial_id: str,
    start_time: float = 0.0,
    bpm: float = BPM,
    cue_beats: int = CUE_BEATS,
    fade_beats: int = FADE_BEATS,
    silence_beats: int = SILENCE_BEATS,
) -> list[dict[str, Any]]:
    """
    Generate expected beat times for one trial.

    Output rows are designed to align with your later matching table:
    - condition
    - trial_id
    - phase (cue / fade / silence)
    - beat_number (1-based, first cue beat = 1)
    - expected_time

    Notes:
    - `start_time` is the timestamp of the first cue beat.
    - Trial end is defined by the last expected silent beat.
    - This function does not include countdown beats.
    """
    if condition not in CONDITIONS:
        raise ValueError(f"Unknown condition: {condition!r}. Expected one of {CONDITIONS}.")
    if bpm <= 0:
        raise ValueError("bpm must be > 0.")
    if cue_beats < 0 or fade_beats < 0 or silence_beats < 0:
        raise ValueError("Beat counts must be >= 0.")

    total_beats = cue_beats + fade_beats + silence_beats
    if total_beats == 0:
        raise ValueError("At least one expected beat is required.")

    interval = 60.0 / bpm
    timeline: list[dict[str, Any]] = []

    # Generate mathematically expected beat times from the fixed experiment
    # timeline (not from tap behavior).
    for beat_index in range(total_beats):
        beat_number = beat_index + 1
        expected_time = start_time + beat_index * interval
        phase = _phase_for_beat(beat_number, cue_beats, fade_beats)

        timeline.append(
            {
                "condition": condition,
                "trial_id": trial_id,
                "phase": phase,
                "beat_number": beat_number,
                "expected_time": expected_time,
            }
        )

    return timeline


def should_play_cue(condition: str, phase: str) -> bool:
    """
    Decide whether to play a cue sound for a beat.

    Rules:
    - synchronization: cue on every expected beat
    - metronome_continuation: cue during cue/fade, silent during silence
    - music_continuation: first draft mirrors metronome_continuation
      (placeholder: later swap in real musical cueing)
    """
    if condition == "synchronization":
        return True

    if condition in {"metronome_continuation", "music_continuation"}:
        # First draft fade behavior: still use the same simple cue tone.
        # Placeholder for true fade envelope / audio mix changes later.
        return phase in {"cue", "fade"}

    raise ValueError(f"Unknown condition: {condition!r}. Expected one of {CONDITIONS}.")


def _sleep_until(target_time: float, poll_interval: float) -> None:
    """Sleep in short steps until `time.perf_counter()` reaches target_time."""
    while True:
        remaining = target_time - time.perf_counter()
        if remaining <= 0:
            return
        time.sleep(min(poll_interval, remaining))


def _play_cue_sound(frequency_hz: int, duration_seconds: float) -> None:
    """
    Play a short cue sound.

    Uses `winsound.Beep` on Windows (blocking for cue duration).
    Falls back to terminal bell on other systems.
    """
    duration_ms = max(0, int(duration_seconds * 1000))
    if duration_ms == 0:
        return

    try:
        import winsound  # Windows standard library module.

        winsound.Beep(int(frequency_hz), duration_ms)
        print(f"playing cue at {expected_time}")
    except Exception:
        # Fallback is intentionally simple for first draft.
        print("\a", end="", flush=True)


def run_trial(
    condition: str,
    trial_id: str,
    timeline: list[dict[str, Any]],
    countdown_seconds: int = COUNTDOWN_SECONDS,
    cue_frequency_hz: int = CUE_FREQUENCY_HZ,
    cue_duration_seconds: float = CUE_DURATION_SECONDS,
    scheduler_sleep_seconds: float = SCHEDULER_SLEEP_SECONDS,
    verbose: bool = True,
) -> dict[str, Any]:
    """
    Run one trial in real time and log raw tap events.

    Returns a dictionary with:
    - timeline_rows: expected beat rows (unchanged)
    - raw_tap_rows: raw taps recorded during live trial window only
    - trial_metadata: basic timing/summary metadata

    Why raw taps are separate:
    - The experimental timeline defines the trial objectively.
    - Participant taps are observed behavior and may have extra/missing taps.
    - Keeping them separate avoids accidental index-based matching at runtime.
    """
    if condition not in CONDITIONS:
        raise ValueError(f"Unknown condition: {condition!r}. Expected one of {CONDITIONS}.")
    if not timeline:
        raise ValueError("Timeline is empty; cannot run trial.")
    if countdown_seconds < 0:
        raise ValueError("countdown_seconds must be >= 0.")
    if scheduler_sleep_seconds <= 0:
        raise ValueError("scheduler_sleep_seconds must be > 0.")

    # Keep runtime aligned with timeline identity.
    for row in timeline:
        if row.get("condition") != condition:
            raise ValueError("Timeline condition does not match run_trial condition.")
        if row.get("trial_id") != trial_id:
            raise ValueError("Timeline trial_id does not match run_trial trial_id.")

    # Delayed import so timeline generation remains usable even if listener
    # dependency is missing on a machine not yet configured for runtime capture.
    try:
        from pynput import keyboard
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency `pynput` for keyboard capture. "
            "Install requirements and try again."
        ) from exc

    raw_tap_rows: list[dict[str, Any]] = []
    tap_lock = threading.Lock()
    trial_active = False
    trial_start_perf: float | None = None
    tap_counter = 0

    def on_press(key: Any) -> None:
        """
        Keyboard callback for tap capture.

        IMPORTANT: taps are only logged while `trial_active` is True.
        This is how countdown taps are ignored.
        """
        nonlocal tap_counter

        if key != keyboard.Key.space:
            return

        press_perf = time.perf_counter()
        press_unix = time.time()

        with tap_lock:
            if (not trial_active) or (trial_start_perf is None):
                return

            tap_counter += 1
            raw_tap_rows.append(
                {
                    "condition": condition,
                    "trial_id": trial_id,
                    "tap_index": tap_counter,
                    "tap_time": press_perf - trial_start_perf,
                    "tap_time_unix": press_unix,
                }
            )

    first_expected = float(timeline[0]["expected_time"])
    last_expected = float(timeline[-1]["expected_time"])
    if abs(first_expected) > 1e-9:
        raise ValueError(
            "run_trial expects expected_time to be relative to trial start "
            "(first cue beat must be at 0.0s)."
        )

    planned_duration = max(0.0, last_expected - first_expected)
    aborted = False

    # Start keyboard listener before countdown.
    # Listener boundary:
    # - BEGIN: before countdown so callback is ready.
    # - END: immediately after trial ends, then stop listener.
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    if verbose:
        print(f"\nStarting trial {trial_id} ({condition})")
        print("Press SPACE in time with the beat.")

    try:
        if countdown_seconds > 0 and verbose:
            print("\nCountdown:")
        for remaining in range(countdown_seconds, 0, -1):
            if verbose:
                print(f"{remaining}...")
            time.sleep(1.0)

        if verbose:
            print("GO")

        trial_start_perf = time.perf_counter()
        trial_start_unix = time.time()

        with tap_lock:
            trial_active = True

        # Drive the trial by expected beat times, not by user taps.
        for beat_row in timeline:
            beat_expected = float(beat_row["expected_time"])
            target_time = trial_start_perf + beat_expected
            _sleep_until(target_time, scheduler_sleep_seconds)

            if should_play_cue(condition, str(beat_row["phase"])):
                _play_cue_sound(cue_frequency_hz, cue_duration_seconds)

        trial_end_perf = time.perf_counter()
        trial_end_unix = time.time()

    except KeyboardInterrupt:
        # Allow manual interruption while still returning what was captured.
        aborted = True
        trial_end_perf = time.perf_counter()
        trial_end_unix = time.time()
        if verbose:
            print("\nTrial interrupted by user.")
    finally:
        # Stop logging taps at trial end.
        with tap_lock:
            trial_active = False

        listener.stop()
        listener.join(timeout=1.0)

    trial_metadata = {
        "condition": condition,
        "trial_id": trial_id,
        "countdown_seconds": countdown_seconds,
        "planned_duration_seconds": planned_duration,
        "trial_start_unix": trial_start_unix if "trial_start_unix" in locals() else None,
        "trial_end_unix": trial_end_unix,
        "actual_duration_seconds": (
            (trial_end_perf - trial_start_perf) if trial_start_perf is not None else None
        ),
        "expected_beat_count": len(timeline),
        "tap_count": len(raw_tap_rows),
        "aborted": aborted,
    }

    return {
        "timeline_rows": timeline,
        "raw_tap_rows": raw_tap_rows,
        "trial_metadata": trial_metadata,
    }
