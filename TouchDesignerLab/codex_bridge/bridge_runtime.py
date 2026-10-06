"""TouchDesigner Execute DAT callbacks for the read-only project bridge."""

import datetime
import json
import os
import traceback
from pathlib import Path


POLL_EVERY_FRAMES = 15
MAX_OPERATORS = 20000
MAX_PARAMETER_TEXT = 4000
MAX_DAT_TEXT = 1000000
_last_poll_frame = -1


def _bridge_folder():
    try:
        value = me.par.file.eval()
        if value:
            return Path(value).resolve().parent
    except Exception:
        pass
    return Path(project.folder).resolve()


def _folders():
    root = _bridge_folder() / "bridge_io"
    paths = {
        "root": root,
        "commands": root / "commands",
        "processing": root / "processing",
        "processed": root / "processed",
        "results": root / "results",
        "errors": root / "errors",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def _json_value(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    text = str(value)
    if len(text) > MAX_PARAMETER_TEXT:
        text = text[:MAX_PARAMETER_TEXT] + "..."
    return text


def _safe_attr(obj, name, default=None):
    try:
        return getattr(obj, name)
    except Exception:
        return default


def _call_messages(operator, method_name):
    method = _safe_attr(operator, method_name)
    if not callable(method):
        return []
    try:
        value = method(recurse=False)
    except TypeError:
        try:
            value = method()
        except Exception:
            return []
    except Exception:
        return []
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    return [_json_value(item) for item in value]


def _parameter_record(parameter):
    record = {
        "name": _safe_attr(parameter, "name", ""),
        "label": _safe_attr(parameter, "label", ""),
        "page": str(_safe_attr(parameter, "page", "")),
        "mode": str(_safe_attr(parameter, "mode", "")),
        "isCustom": bool(_safe_attr(parameter, "isCustom", False)),
        "enable": bool(_safe_attr(parameter, "enable", True)),
    }
    try:
        record["value"] = _json_value(parameter.eval())
    except Exception as exc:
        record["valueError"] = str(exc)
    expression = _safe_attr(parameter, "expr", None)
    if expression:
        record["expression"] = str(expression)
    bind_expression = _safe_attr(parameter, "bindExpr", None)
    if bind_expression:
        record["bindExpression"] = str(bind_expression)
    return record


def _operator_record(operator):
    inputs = []
    try:
        inputs = [item.path if item is not None else None for item in operator.inputs]
    except Exception:
        pass

    parameters = []
    try:
        parameters = [_parameter_record(item) for item in operator.pars()]
    except Exception as exc:
        parameters = [{"readError": str(exc)}]

    return {
        "path": operator.path,
        "name": operator.name,
        "type": str(_safe_attr(operator, "OPType", _safe_attr(operator, "type", ""))),
        "family": str(_safe_attr(operator, "family", "")),
        "parent": operator.parent().path if operator.parent() is not None else None,
        "inputs": inputs,
        "tags": sorted(list(_safe_attr(operator, "tags", []))),
        "activeViewer": bool(_safe_attr(operator, "viewer", False)),
        "bypass": bool(_safe_attr(operator, "bypass", False)),
        "display": bool(_safe_attr(operator, "display", False)),
        "render": bool(_safe_attr(operator, "render", False)),
        "cook": bool(_safe_attr(operator, "allowCooking", True)),
        "errors": _call_messages(operator, "errors"),
        "warnings": _call_messages(operator, "warnings"),
        "parameters": parameters,
    }


def _snapshot(root_path):
    root_operator = op(root_path)
    if root_operator is None:
        raise ValueError("Operator does not exist: " + root_path)

    operators = [root_operator]
    try:
        operators.extend(root_operator.findChildren(maxDepth=999, includeUtility=True))
    except TypeError:
        operators.extend(root_operator.findChildren(maxDepth=999))

    operators = operators[:MAX_OPERATORS]
    now = datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()
    return {
        "schema": 1,
        "capturedAt": now,
        "readOnly": True,
        "project": {
            "name": str(_safe_attr(project, "name", "")),
            "folder": str(_safe_attr(project, "folder", "")),
            "saveVersion": _json_value(_safe_attr(project, "saveVersion", None)),
        },
        "application": {
            "version": str(_safe_attr(app, "version", "")),
            "build": str(_safe_attr(app, "build", "")),
            "product": str(_safe_attr(app, "product", "")),
            "osName": str(_safe_attr(app, "osName", "")),
        },
        "root": root_operator.path,
        "operatorCount": len(operators),
        "truncated": len(operators) >= MAX_OPERATORS,
        "operators": [_operator_record(item) for item in operators],
    }


def _text_snapshot(root_paths):
    records = []
    seen = set()
    for root_path in root_paths:
        root_operator = op(root_path)
        if root_operator is None:
            raise ValueError("Operator does not exist: " + root_path)
        candidates = [root_operator]
        try:
            candidates.extend(root_operator.findChildren(maxDepth=999, includeUtility=True))
        except TypeError:
            candidates.extend(root_operator.findChildren(maxDepth=999))
        for operator in candidates:
            if operator.path in seen or str(_safe_attr(operator, "family", "")) != "DAT":
                continue
            seen.add(operator.path)
            try:
                content = str(operator.text)
            except Exception:
                continue
            truncated = len(content) > MAX_DAT_TEXT
            if truncated:
                content = content[:MAX_DAT_TEXT]
            records.append({
                "path": operator.path,
                "type": str(_safe_attr(operator, "OPType", _safe_attr(operator, "type", ""))),
                "truncated": truncated,
                "text": content,
            })
    return {
        "schema": 1,
        "capturedAt": datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(),
        "readOnly": True,
        "roots": root_paths,
        "datCount": len(records),
        "dats": records,
    }


def _write_json(path, payload):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    os.replace(str(temporary), str(path))


def _process_command(command_path, folders):
    processing_path = folders["processing"] / command_path.name
    os.replace(str(command_path), str(processing_path))
    command = json.loads(processing_path.read_text(encoding="utf-8-sig"))
    command_id = str(command.get("id") or processing_path.stem)
    action = command.get("action")

    if action == "ping":
        result = {"id": command_id, "ok": True, "action": action, "readOnly": True}
    elif action == "snapshot":
        snapshot = _snapshot(str(command.get("root") or "/project1"))
        snapshot_name = "snapshot_{}.json".format(command_id)
        _write_json(folders["results"] / snapshot_name, snapshot)
        result = {
            "id": command_id,
            "ok": True,
            "action": action,
            "snapshot": snapshot_name,
            "operatorCount": snapshot["operatorCount"],
        }
    elif action == "snapshot_texts":
        roots = command.get("roots") or ["/project1/LaserWave01"]
        if not isinstance(roots, list) or not all(isinstance(item, str) for item in roots):
            raise ValueError("roots must be a list of operator path strings")
        snapshot = _text_snapshot(roots)
        snapshot_name = "texts_{}.json".format(command_id)
        _write_json(folders["results"] / snapshot_name, snapshot)
        result = {
            "id": command_id,
            "ok": True,
            "action": action,
            "snapshot": snapshot_name,
            "datCount": snapshot["datCount"],
        }
    elif action == "install_moses_gate":
        # Narrowly allowlisted development mutation.  No arbitrary script path
        # is accepted from a command; only the reviewed sibling installer runs.
        installer = _bridge_folder() / "install_moses_gate.py"
        if not installer.exists():
            raise ValueError("Reviewed Moses Gate installer was not found")
        namespace = dict(globals())
        namespace.update({"__name__": "codex_moses_gate_installer", "__file__": str(installer)})
        exec(compile(installer.read_text(encoding="utf-8-sig"), str(installer), "exec"), namespace, namespace)
        installed = []
        for path in ("/project1/LaserWave01", "/project1/LaserWave02", "/project1/LaserWave03"):
            control = op(path + "/MosesGateControl")
            output = op(path + "/moses_gate_out")
            if control is not None and output is not None:
                installed.append(path)
        result = {
            "id": command_id,
            "ok": len(installed) > 0,
            "action": action,
            "installed": installed,
            "laserOutputLocked": True,
        }
    elif action == "set_gate_preview":
        component_path = str(command.get("component") or "/project1/LaserWave01")
        allowed_components = {
            "/project1/LaserWave01", "/project1/LaserWave02", "/project1/LaserWave03"
        }
        if component_path not in allowed_components:
            raise ValueError("component is outside the Moses Gate allowlist")
        control = op(component_path + "/MosesGateControl")
        if control is None:
            raise ValueError("MosesGateControl is not installed")
        values = command.get("values") or {}
        allowed_parameters = {
            "Virtualmode", "Virtualpresent", "Virtualx", "Virtualapproach",
            "Triggerapproach", "Gatewidth", "Safetymargin", "Opentime",
            "Closetime", "Holdseconds", "Enable"
        }
        rejected = sorted(set(values.keys()) - allowed_parameters)
        if rejected:
            raise ValueError("parameters outside preview allowlist: " + ", ".join(rejected))
        applied = {}
        for name, value in values.items():
            parameter = control.par[name]
            if parameter is None:
                raise ValueError("missing gate parameter: " + name)
            parameter.val = value
            applied[name] = _json_value(parameter.eval())
        result = {"id": command_id, "ok": True, "action": action, "component": component_path, "applied": applied}
    elif action == "capture_gate_preview":
        component_path = str(command.get("component") or "/project1/LaserWave01")
        allowed_components = {
            "/project1/LaserWave01", "/project1/LaserWave02", "/project1/LaserWave03"
        }
        if component_path not in allowed_components:
            raise ValueError("component is outside the preview allowlist")
        source = op(component_path + "/InputMonitor/out1")
        if source is None:
            raise ValueError("InputMonitor/out1 was not found")
        preview_folder = folders["results"] / "previews"
        preview_folder.mkdir(parents=True, exist_ok=True)
        filename = "preview_{}.png".format(command_id)
        destination = preview_folder / filename
        source.save(str(destination))
        result = {"id": command_id, "ok": True, "action": action, "preview": str(destination)}
    elif action == "save_development_project":
        project_folder = Path(project.folder).resolve()
        expected = Path(r"C:\Work\TouchDesigner\TouchDesignerLab").resolve()
        if project_folder != expected:
            raise ValueError("Refusing to save outside the TouchDesignerLab development folder")
        project.save()
        result = {"id": command_id, "ok": True, "action": action, "folder": str(project_folder)}
    else:
        raise ValueError(
            "Unsupported action: {!r}. Allowed: ping, snapshot, snapshot_texts, install_moses_gate, set_gate_preview, capture_gate_preview, save_development_project".format(action)
        )

    _write_json(folders["results"] / ("result_" + command_id + ".json"), result)
    os.replace(str(processing_path), str(folders["processed"] / processing_path.name))


def _poll():
    folders = _folders()
    command_files = sorted(folders["commands"].glob("*.json"))
    if not command_files:
        return
    command_path = command_files[0]
    try:
        _process_command(command_path, folders)
        status = op("../status")
        if status is not None:
            status.text = "Processed: " + command_path.name
    except Exception as exc:
        error_payload = {
            "ok": False,
            "command": command_path.name,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
        _write_json(folders["errors"] / (command_path.stem + ".error.json"), error_payload)
        for candidate in (folders["processing"] / command_path.name, command_path):
            if candidate.exists():
                os.replace(str(candidate), str(folders["processed"] / command_path.name))
                break
        status = op("../status")
        if status is not None:
            status.text = "Error: " + str(exc)


def onFrameStart(frame):
    global _last_poll_frame
    frame_number = int(absTime.frame)
    if _last_poll_frame < 0 or frame_number - _last_poll_frame >= POLL_EVERY_FRAMES:
        _last_poll_frame = frame_number
        _poll()
    return


def onStart():
    _folders()
    return


def onCreate():
    _folders()
    return


def onFrameEnd(frame):
    return


def onPlayStateChange(state):
    return


def onDeviceChange():
    return


def onProjectPreSave():
    return


def onProjectPostSave():
    return


def onExit():
    return
