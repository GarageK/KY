"""One-click continuation: reinstall the bridge, then install Moses Gate."""

from pathlib import Path


def _folder():
    value = me.par.file.eval()
    return Path(value).resolve().parent if value else Path(project.folder) / "codex_bridge"


folder = _folder()
for filename in ("bootstrap.py", "install_moses_gate.py"):
    path = folder / filename
    if not path.exists():
        raise RuntimeError("Missing required file: " + str(path))
    # Use one shared namespace for definitions and execution.  TouchDesigner
    # callbacks otherwise resolve helpers (such as _source_folder) in the
    # caller's globals instead of beside the loaded install() function.
    namespace = dict(globals())
    namespace.update({"__name__": "codex_continue_" + path.stem, "__file__": str(path)})
    exec(compile(path.read_text(encoding="utf-8-sig"), str(path), "exec"), namespace, namespace)

debug("Codex bridge, Moses Gate, and interaction modes are ready. Save TouchDesignerLab.toe and keep it open.")
