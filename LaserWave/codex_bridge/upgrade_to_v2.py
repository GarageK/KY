"""Switch an installed AI_BRIDGE Execute DAT to bridge_runtime_v2.py."""

from pathlib import Path


def _source_folder():
    value = me.par.file.eval()
    if value:
        return Path(value).resolve().parent
    return Path(project.folder).resolve() / "codex_bridge"


bridge_execute = op("/project1/AI_BRIDGE/bridge_execute")
if bridge_execute is None:
    raise RuntimeError("AI_BRIDGE is not installed. Run bootstrap.py first.")

runtime_file = _source_folder() / "bridge_runtime_v2.py"
if not runtime_file.exists():
    raise RuntimeError("bridge_runtime_v2.py was not found beside upgrade_to_v2.py")

bridge_execute.par.syncfile = False
bridge_execute.par.file = str(runtime_file).replace("\\", "/")
bridge_execute.par.syncfile = True
bridge_execute.par.loadonstartpulse.pulse()
debug("AI_BRIDGE upgraded to", runtime_file)
