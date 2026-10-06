# TouchDesigner AI Bridge — read-only analyzer

This first-stage bridge lets TouchDesigner describe an open `.toe` project as JSON. It cannot create, delete, connect, or modify operators, and it does not enable laser output.

## Install once in the base project

1. Make a backup copy of the base `.toe` file.
2. Open the copy in TouchDesigner and stay in Editor Mode.
3. Drag `bootstrap.py` from this folder into `/project1`.
4. Right-click the new Text DAT and select **Run Script**. If that menu item is unavailable, open **Dialogs → Textport and DATs → Textport** and run:

   ```python
   op('/project1/bootstrap').run()
   ```

5. Wait several seconds. `/project1/AI_BRIDGE` should appear.
6. Save the project copy.

The first analysis is requested automatically. Results are written under:

```text
bridge_io/results/
```

Expected files include `result_initial_snapshot.json` and `snapshot_initial_snapshot.json`.

## Request another analysis

Run `request_snapshot.py` from Windows, or place a JSON file like this in `bridge_io/commands/`:

```json
{"id":"manual_001","action":"snapshot","root":"/project1"}
```

## Safety model

- Only `ping` and `snapshot` commands are accepted.
- The bridge performs no network communication.
- The bridge performs no operator or parameter mutation.
- It does not arm or enable laser, DAC, DMX, Art-Net, OSC, MIDI, or other outputs.
- Use a copied `.toe` project and keep physical laser emission disabled while analyzing.

After the snapshot has been reviewed, a separate mutation layer can be added with path allow-lists, automatic backups, dry-run validation, and an explicit output interlock.
