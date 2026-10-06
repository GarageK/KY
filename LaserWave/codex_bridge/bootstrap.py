"""Install the read-only Codex bridge into the current TouchDesigner project.

Usage inside TouchDesigner:
1. Drag this file into /project1 (it becomes a Text DAT).
2. Right-click the DAT and choose "Run Script", or run op('bootstrap').run().
"""

from pathlib import Path


BRIDGE_NAME = "AI_BRIDGE"


def _source_folder():
    try:
        file_value = me.par.file.eval()
        if file_value:
            return Path(file_value).resolve().parent
    except Exception:
        pass
    return Path(project.folder).resolve()


def install():
    source_folder = _source_folder()
    runtime_file = source_folder / "bridge_runtime.py"
    if not runtime_file.exists():
        raise RuntimeError("bridge_runtime.py was not found beside bootstrap.py")

    root = op("/project1") or op("/")
    existing = root.op(BRIDGE_NAME)
    if existing is not None:
        existing.destroy()

    bridge = root.create(baseCOMP, BRIDGE_NAME)
    bridge.nodeX = -900
    bridge.nodeY = 700
    bridge.color = (0.12, 0.45, 0.75)

    execute_dat = bridge.create(executeDAT, "bridge_execute")
    execute_dat.par.file = str(runtime_file).replace("\\", "/")
    execute_dat.par.syncfile = True
    execute_dat.par.loadonstart = True
    execute_dat.par.framestart = True
    execute_dat.par.active = True

    status = bridge.create(textDAT, "status")
    status.text = (
        "Codex bridge installed. Read-only mode is active.\n"
        "Waiting for commands in bridge_io/commands."
    )
    # Base COMPs do not expose a `display` custom parameter.  Keep setup
    # compatible across TouchDesigner builds by only touching parameters that
    # actually exist on this COMP type.
    if getattr(bridge.par, "cloneimmune", None) is not None:
        bridge.par.cloneimmune = True

    # Trigger a first scan without requiring an external command.
    io_folder = source_folder / "bridge_io"
    commands = io_folder / "commands"
    commands.mkdir(parents=True, exist_ok=True)
    initial = commands / "000_initial_snapshot.json"
    if not initial.exists():
        initial.write_text(
            '{"id":"initial_snapshot","action":"snapshot","root":"/project1"}',
            encoding="utf-8",
        )

    debug("Codex bridge installed at", bridge.path)
    debug("Bridge folder:", source_folder)
    return bridge


install()
