"""Install the LaserWave Moses-gate prototype into TouchDesignerLab.

Run this Text DAT once from /project1.  It only targets LaserWave01..03 in the
development copy and deliberately keeps all physical laser outputs disabled.
"""

from pathlib import Path
import shutil


TARGETS = ("/project1/LaserWave01", "/project1/LaserWave02", "/project1/LaserWave03")
CREATED_TAG = "codex_moses_gate_v1"


CONTROLLER_CODE = r'''import math

_last_time = None
_clear_since = None

def _par(name, default=0.0):
    p = parent().par[name]
    return p.eval() if p is not None else default

def _actual_measurement():
    cloud = parent().parent().op('popto1')
    if cloud is None:
        return False, 0.0, 999.0
    samples = []
    try:
        for point in cloud.points:
            x, y, _ = point.P
            if math.isfinite(x) and math.isfinite(y):
                samples.append((abs(float(y)), float(x)))
    except Exception:
        return False, 0.0, 999.0
    if len(samples) < max(1, int(_par('Minpoints', 3))):
        return False, 0.0, 999.0
    samples.sort(key=lambda item: item[0])
    count = min(len(samples), max(3, int(_par('Minpoints', 3))))
    near = samples[:count]
    return True, sum(item[1] for item in near) / count, sum(item[0] for item in near) / count

def onFrameStart(frame):
    global _last_time, _clear_since
    control = parent()
    now = absTime.seconds
    dt = max(0.0, min(0.1, now - _last_time)) if _last_time is not None else 1.0 / max(1.0, root.time.rate)
    _last_time = now

    if bool(_par('Virtualmode', True)):
        person_x = float(_par('Virtualx', 0.0))
        approach = float(_par('Virtualapproach', 0.0))
        present = bool(_par('Virtualpresent', True))
        near = present and approach >= float(_par('Triggerapproach', 0.60))
    else:
        present, person_x, distance = _actual_measurement()
        trigger = float(_par('Triggerdistance', 0.35))
        release = trigger + float(_par('Releasemargin', 0.10))
        was_open = float(_par('Gateamount', 0.0)) > 0.001
        near = present and distance <= (release if was_open else trigger)

    enabled = bool(_par('Enable', True))
    failsafe = bool(_par('Failsafeopen', True)) and not bool(_par('Virtualmode', True)) and not present
    request_open = enabled and (near or failsafe)
    amount = float(_par('Gateamount', 0.0))

    if request_open:
        _clear_since = None
        duration = max(0.01, float(_par('Opentime', 0.75)))
        amount = min(1.0, amount + dt / duration)
        state = 'OPEN' if amount >= 0.999 else ('FAILSAFE OPENING' if failsafe else 'OPENING')
    else:
        if _clear_since is None:
            _clear_since = now
        hold = max(0.0, float(_par('Holdseconds', 1.0)))
        if now - _clear_since >= hold:
            duration = max(0.01, float(_par('Closetime', 1.20)))
            amount = max(0.0, amount - dt / duration)
            state = 'CLOSED' if amount <= 0.001 else 'CLOSING'
        else:
            state = 'HOLD' if amount > 0.001 else 'CLOSED'

    control.par.Gateamount = amount
    control.par.Detected = near
    control.par.Personx = max(-1.0, min(1.0, person_x))
    control.par.State = state
    return
'''


SCRIPT_SOP_CODE = r'''def _smooth(value):
    value = max(0.0, min(1.0, float(value)))
    return value * value * (3.0 - 2.0 * value)

def onCook(scriptOp):
    scriptOp.clear()
    source = scriptOp.inputs[0] if scriptOp.inputs else None
    control = scriptOp.parent().op('MosesGateControl')
    if source is None:
        return
    if control is None or not bool(control.par.Enable.eval()):
        scriptOp.copy(source)
        return

    amount = _smooth(control.par.Gateamount.eval())
    if amount <= 0.0001:
        scriptOp.copy(source)
        return

    center = float(control.par.Personx.eval())
    half_gap = (float(control.par.Gatewidth.eval()) * 0.5 + float(control.par.Safetymargin.eval())) * amount

    for primitive in source.prims:
        run = []
        runs = []
        for vertex in primitive:
            point = vertex.point
            position = point.P
            if abs(float(position.x) - center) >= half_gap:
                run.append((float(position.x), float(position.y), float(position.z)))
            elif run:
                runs.append(run)
                run = []
        if run:
            runs.append(run)
        for points in runs:
            if len(points) < 2:
                continue
            output = scriptOp.appendPoly(len(points), closed=False, addPoints=True)
            for index, position in enumerate(points):
                output[index].point.P = position
    return
'''


def _source_folder():
    try:
        value = me.par.file.eval()
        if value:
            return Path(value).resolve().parent
    except Exception:
        pass
    return Path(project.folder).resolve() / "codex_bridge"


def _ensure_backup():
    project_file = Path(project.folder) / "TouchDesignerLab.toe"
    backup = Path(project.folder) / "backups" / "TouchDesignerLab.pre_moses_gate.toe"
    backup.parent.mkdir(parents=True, exist_ok=True)
    if project_file.exists() and not backup.exists():
        shutil.copy2(str(project_file), str(backup))
    return backup


def _parameter(owner, page, kind, name, label, value, minimum=None, maximum=None):
    existing = owner.par[name]
    if existing is None:
        created = getattr(page, "append" + kind)(name, label=label)
        par = created[0]
    else:
        par = existing
    par.val = value
    if minimum is not None:
        par.min = minimum
        par.clampMin = True
    if maximum is not None:
        par.max = maximum
        par.clampMax = True
    return par


def _safe_constant(operator, parameter_name, value):
    parameter = operator.par[parameter_name] if operator is not None else None
    if parameter is None:
        return
    try:
        parameter.expr = ""
    except Exception:
        pass
    parameter.val = value


def _connect(target, input_index, source):
    """Connect OPs using the connector API available in TouchDesigner 2025."""
    if target is None or source is None:
        raise RuntimeError("Cannot connect a missing operator")
    connector = target.inputConnectors[input_index]
    try:
        connector.disconnect()
    except Exception:
        pass
    source.outputConnectors[0].connect(connector)


def _install_target(component, index):
    required = ("spring1", "laser1", "laserdevice1", "Shape", "Brightness", "TestMode", "InputMonitor")
    missing = [name for name in required if component.op(name) is None]
    if missing:
        raise RuntimeError(component.path + " missing required operators: " + ", ".join(missing))

    control = component.op("MosesGateControl")
    if control is None:
        control = component.create(baseCOMP, "MosesGateControl")
        control.tags.add(CREATED_TAG)
    elif CREATED_TAG not in control.tags:
        raise RuntimeError(component.path + "/MosesGateControl already exists and is not owned by this installer")
    control.nodeX = 350
    control.nodeY = 450
    control.color = (0.15, 0.55, 0.80)
    page = control.appendCustomPage("Moses Gate") if not any(p.name == "Moses Gate" for p in control.customPages) else next(p for p in control.customPages if p.name == "Moses Gate")
    _parameter(control, page, "Toggle", "Enable", "Enable Gate", True)
    _parameter(control, page, "Toggle", "Virtualmode", "Virtual Test Mode", True)
    _parameter(control, page, "Toggle", "Virtualpresent", "Virtual Person Present", True)
    _parameter(control, page, "Float", "Virtualx", "Virtual Person X", 0.0, -1.0, 1.0)
    _parameter(control, page, "Float", "Virtualapproach", "Virtual Approach", 0.0, 0.0, 1.0)
    _parameter(control, page, "Float", "Triggerapproach", "Open Trigger", 0.60, 0.0, 1.0)
    _parameter(control, page, "Float", "Triggerdistance", "LiDAR Trigger Distance", 0.35, 0.01, 5.0)
    _parameter(control, page, "Float", "Releasemargin", "Release Hysteresis", 0.10, 0.0, 2.0)
    _parameter(control, page, "Int", "Minpoints", "Minimum Points", 3, 1, 1000)
    _parameter(control, page, "Float", "Gatewidth", "Gate Width", 0.50, 0.05, 2.0)
    _parameter(control, page, "Float", "Safetymargin", "Safety Margin", 0.10, 0.0, 1.0)
    _parameter(control, page, "Float", "Opentime", "Open Time", 0.75, 0.05, 10.0)
    _parameter(control, page, "Float", "Closetime", "Close Time", 1.20, 0.05, 10.0)
    _parameter(control, page, "Float", "Holdseconds", "Hold Before Close", 1.00, 0.0, 30.0)
    _parameter(control, page, "Toggle", "Failsafeopen", "Fail Safe Open", True)
    _parameter(control, page, "Float", "Gateamount", "Gate Amount", 0.0, 0.0, 1.0)
    _parameter(control, page, "Toggle", "Detected", "Detected", False)
    _parameter(control, page, "Float", "Personx", "Detected Person X", 0.0, -1.0, 1.0)
    _parameter(control, page, "Str", "State", "State", "CLOSED")

    execute = control.op("gate_state") or control.create(executeDAT, "gate_state")
    execute.text = CONTROLLER_CODE
    execute.par.framestart = True
    execute.par.active = True

    callback = component.op("moses_gate_callbacks") or component.create(textDAT, "moses_gate_callbacks")
    if CREATED_TAG not in callback.tags:
        callback.tags.add(CREATED_TAG)
    callback.text = SCRIPT_SOP_CODE
    callback.nodeX = 450
    callback.nodeY = 250

    gate = component.op("moses_gate") or component.create(scriptSOP, "moses_gate")
    if CREATED_TAG not in gate.tags:
        gate.tags.add(CREATED_TAG)
    _connect(gate, 0, component.op("spring1"))
    gate.par.callbacks = callback
    gate.nodeX = 250
    gate.nodeY = 150
    gate.color = (0.15, 0.70, 0.40)

    output = component.op("moses_gate_out") or component.create(nullSOP, "moses_gate_out")
    if CREATED_TAG not in output.tags:
        output.tags.add(CREATED_TAG)
    _connect(output, 0, gate)
    output.nodeX = 250
    output.nodeY = 50

    # LINE is input/menu index 0.  Keep the existing random Spring behavior and
    # insert the gate only after it.
    component.op("Shape").par["Value0"] = "Line"
    component.op("laser1").par.sop = output
    monitor = component.op("InputMonitor")
    _connect(monitor, 3, output)

    # Development safety interlock.  Physical output remains disabled even if
    # another UI parameter is accidentally raised.
    component.op("Brightness").par["Value0"] = 0
    component.op("TestMode").par["Value0"] = False
    _safe_constant(component.op("laserdevice1"), "active", False)
    for name in ("redscale", "greenscale", "bluescale"):
        _safe_constant(component.op("laserdevice1"), name, 0.0)

    return {
        "component": component.path,
        "controller": control.path,
        "output": output.path,
        "laserLocked": True,
        "virtualMode": True,
    }


def install():
    backup = _ensure_backup()
    results = []
    for index, path in enumerate(TARGETS, 1):
        component = op(path)
        if component is not None:
            results.append(_install_target(component, index))
    if not results:
        raise RuntimeError("No LaserWave01..03 components were found")
    status = op("/project1/AI_BRIDGE/status")
    if status is not None:
        status.text = "Moses Gate installed safely. Virtual mode ON; laser output LOCKED."
    debug("Moses Gate installation complete", results)
    debug("Backup:", backup)
    return results


install()
