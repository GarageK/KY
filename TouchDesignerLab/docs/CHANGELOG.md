# Change log

## Moses wave revision - virtual verification completed

- Changed Moses from a straight-line source to a dedicated wave Spring source.
- Kept the original person-avoidance attractor disconnected in Moses.
- Preserved Hybrid as original person avoidance followed by the Moses gate.
- Created `backups/TouchDesignerLab.pre_moses_wave.toe` before applying the
  network migration.
- Added `inspect_interaction_state`, a compact bridge diagnostic that reports
  mode routes, gate state, safety values, and targeted OP issues without a full
  network snapshot.
- Verified all three Moses wave routes have no person-attractor input.
- Verified LaserWave01 visually in closed and open virtual-gate states.
- Saved all three components in Moses mode with gates closed and laser output
  locked. Camera and physical laser behavior remain unverified.

## Context-efficient workflow - 2026-10-07

- Established a difference-first inspection policy.
- Restricted full network snapshots to baseline and exceptional diagnosis.
- Defined Markdown design documents as the primary restart state.
- Prioritized compact bridge queries, focused `toeexpand` diffs, and minimal
  visual captures.

## Baseline - 2026-10-07

- Preserved the original LaserWave projects.
- Preserved the pre-Moses development backup.
- Recorded the current development `.toe`, bridge scripts, snapshots, and
  virtual preview results as the version-control baseline.
- Physical laser output remains disabled. This baseline has not been verified
  with a live camera or laser device.

## Interaction modes - virtual verification completed

- Added a reviewed installer for Traditional, Moses, and Hybrid routes.
- Added Run UI controls for mode selection and Moses parameters.
- Kept the current Hybrid behavior as the migration default.
- Kept physical laser output locked independently of interaction mode.
- Applied the migration to all three LaserWave components and saved the
  development `.toe`.
- Verified Traditional, Moses, and Hybrid routing on LaserWave01 using captured
  monitor previews. Moses produced a straight line with a central gate; Hybrid
  retained Spring deformation with a central gate.
- Corrected Run UI parameter expressions and preserved UI values across
  installer reruns.
- Camera input and physical laser output remain unverified. The camera reported
  a connection error during this test, and the laser device stayed locked.

