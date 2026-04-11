# Experiment Plan (Draft)

## Purpose
Measure individual differences in auditory-motor timing and cue dependence.

## Conditions
- Synchronization
- Metronome continuation
- Music continuation

## Planned next implementation steps
1. Add trial execution loop (countdown, cue, fade, silence).
2. Add spacebar tap capture during trial window.
3. Save raw trial/tap data to `data/raw/`.
4. Implement offline beat-tap matching in `analysis.py`.
5. Compute asynchrony and interval-based metrics.
