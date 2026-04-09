This project is a rhythm consistency tester in three phases:
1. Can the user synchronize beat tapping with an isochronous beat playing in the background?
2. Can the user maintain a beat even after there is no backing metronome track?
3. Can the user maintain a beat after a musical (groove-based) cue fades out? (cue comparison)

For each experiment, you will hear 4 bars of 4/4 time (16 beats total). 
Data from each trial is saved and the final output is a graph showing deviation from expected values. It is saved in the following columns: 

- condition (metronome, silenced_metronome, music)
- trial_id
- phase (cue / fade / silence)
- beat_number
- expected_time
- tap_time
- asyncrhony (tap_time - expected_time)
- matched (yes/no)