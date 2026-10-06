# Version-control policy

## Protected assets

- `LaserWave/LaserWave.toe` is the immutable source asset. Do not overwrite it.
- Development takes place in `TouchDesignerLab/TouchDesignerLab.toe`.
- Before automated `.toe` edits, create a recoverable copy under
  `TouchDesignerLab/backups/`.

## Git strategy

- Store `.toe`, `.tox`, large bridge snapshots, and PDFs with Git LFS.
- Commit the script that performs a TouchDesigner network change together with
  its result record and documentation.
- Treat `.toe` files as binary checkpoints: they can be restored, but not
  meaningfully line-merged.
- Create a commit before each TouchDesigner network migration and another after
  verification.

## Verification labels

- `static`: source and captured network snapshots were inspected.
- `virtual`: behavior was exercised with virtual sensor parameters.
- `hardware`: camera and laser hardware were connected and tested under the
  laser-safety checklist.

Never describe a lower verification level as a higher one.

