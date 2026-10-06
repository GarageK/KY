# Interaction modes

## Modes

| Mode | Geometry route | Intended behavior |
|---|---|---|
| Traditional | Original `null6` output | Preserve the original LaserWave behavior and Test Mode selection. |
| Moses | `switch_shape` to `moses_only_gate` | Open a blank gate without Spring deformation. |
| Hybrid | `spring1` to `moses_gate` | Apply the original Spring response, then open the Moses gate. |

The final `interaction_mode_switch` feeds `interaction_out`, which is the only
geometry source assigned to `laser1` after this migration.

## Run UI

Each `LaserWave01..03` panel receives an `Interaction Mode` selector and Moses
controls for enable, virtual test, width, safety margin, trigger distance, open
time, close time, and hold time.

Virtual test parameters currently validate the Moses gate controller only. They
do not simulate the original camera point cloud entering the Spring network.
That limitation must remain visible until a calibrated virtual point-cloud
fixture is implemented and verified.

## Safety

Installation forces Brightness to zero, Test Mode off, Laser Device inactive,
and RGB device scales to zero. Selecting an interaction mode does not authorize
or enable physical laser output.

