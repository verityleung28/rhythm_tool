# rhythm-battery

`rhythm-battery` is a first-draft Python behavioral rhythm battery focused on:
- auditory-motor synchronization,
- internal timing,
- and cue dependence.

The core contrast is between:
1. Synchronizing to an external beat, and
2. Continuing a beat when the cue is removed.

## Current milestone
This repository currently implements:
- configuration in `config.py`,
- fixed expected-beat timeline generation in `task_logic.py`,
- first-draft real trial execution with cue playback and spacebar tap logging,
- and a single-trial demo in `main.py` with optional raw output saving.

Tap-to-beat matching and rhythm metrics are deferred to `analysis.py`.

## Trial design (first draft)
- BPM: `120`
- Beat interval: `0.5` seconds
- Countdown: configurable, not part of expected beat numbering
- Cue phase: `12` beats
- Fade phase: `4` beats
- Silent continuation phase: `16` beats

Expected beat time generation follows:
`expected_time = start_time + beat_index * interval`

## Conditions
- `synchronization`
- `metronome_continuation`
- `music_continuation`

## Project structure

```text
rhythm-battery/
├─ README.md
├─ requirements.txt
├─ .gitignore
├─ main.py
├─ task_logic.py
├─ analysis.py
├─ config.py
├─ data/
│  ├─ raw/
│  └─ processed/
└─ notes/
   └─ experiment_plan.md
```

## Quick start

```bash
python main.py
```

This runs one real-time trial, logs raw spacebar taps during the live trial window,
and saves raw outputs in `data/raw/` by default.
