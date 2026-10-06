# Context-efficient development workflow

## Purpose

Keep TouchDesigner development reviewable while avoiding repeated ingestion of
large network snapshots, images, and historical logs.

## Default evidence order

Use the smallest sufficient source of evidence, in this order:

1. Current design and decision documents under `TouchDesignerLab/docs/`.
2. `git status`, recent commits, and a focused `git diff`.
3. The relevant installer, callback, or bridge source file.
4. A small bridge query returning only named OPs and parameters.
5. A focused `toeexpand` diff for the affected component or project revision.
6. A targeted monitor capture when visual behavior must be checked.
7. A full network snapshot only when the preceding evidence cannot answer the
   question or when establishing a new baseline.

## Snapshot policy

- Do not create a full project or full LaserWave snapshot for routine parameter
  checks.
- Prefer a named root such as `MosesGateControl` or an explicit allowlist of OP
  paths.
- Filter large JSON files locally and return only the required fields to the
  review conversation.
- Store retained large snapshots with Git LFS and state why each snapshot was
  necessary in the change log.
- Do not recapture an unchanged state.

## Bridge design

New bridge actions should return compact structured results such as:

- selected interaction mode;
- gate state, amount, and detection state;
- UI parameter values;
- final SOP route;
- laser safety-lock values;
- errors and warnings for an explicit OP allowlist.

Mutation actions must remain narrowly allowlisted and return the values read
back after mutation. Prefer one action that applies and verifies a coherent
change over many single-parameter round trips.

## Documentation as restart state

For each material feature, maintain a short Markdown document containing:

- intended behavior and mode boundaries;
- important OP paths and data flow;
- parameters and safe defaults;
- implementation and rollback entry points;
- completed verification;
- unverified hardware behavior and remaining risks.

Update the document when the implementation changes. A future task should be
able to resume from the document and Git history without rereading full bridge
logs or snapshots.

## Verification levels

- `static`: focused source, diff, or expanded-network inspection.
- `virtual`: compact state queries plus only the necessary monitor captures.
- `hardware`: camera and laser checks performed under the safety checklist.

Use the lowest level that can answer the question, and never report a higher
level than was actually completed.

