"""Install selectable Traditional, Moses, and Hybrid interaction modes.

This script is intended to run inside the development copy of TouchDesigner.
It is idempotent, targets only LaserWave01..03, preserves the original output
nodes, and keeps every physical laser output disabled.
"""

from pathlib import Path
import shutil


TARGETS = ("/project1/LaserWave01", "/project1/LaserWave02", "/project1/LaserWave03")
TAG = "codex_interaction_modes_v1"


def _backup():
    source = Path(project.folder) / "TouchDesignerLab.toe"
    target = Path(project.folder) / "backups" / "TouchDesignerLab.pre_interaction_modes.toe"
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.exists() and not target.exists():
        shutil.copy2(str(source), str(target))
    return target


def _connect(target, index, source):
    if target is None or source is None:
        raise RuntimeError("Cannot connect a missing operator")
    connector = target.inputConnectors[index]
    try:
        connector.disconnect()
    except Exception:
        pass
    source.outputConnectors[0].connect(connector)


def _safe_constant(operator, name, value):
    parameter = operator.par[name] if operator is not None else None
    if parameter is None:
        return
    try:
        parameter.expr = ""
    except Exception:
        pass
    parameter.val = value


def _copy_widget(component, source_name, target_name, label, value):
    widget = component.op(target_name)
    created = widget is None
    if widget is None:
        source = component.op(source_name)
        if source is None:
            raise RuntimeError(component.path + " missing UI template " + source_name)
        widget = component.copy(source, name=target_name, includeDocked=True)
        widget.tags.add(TAG)
    elif TAG not in widget.tags:
        raise RuntimeError(widget.path + " already exists and is not installer-owned")
    widget.par.Widgetlabel = label
    if created:
        try:
            widget.par.Value0.expr = ""
        except Exception:
            pass
        widget.par.Value0 = value
    return widget


def _slider(component, name, label, value, minimum, maximum):
    existed = component.op(name) is not None
    widget = _copy_widget(component, "sliderHorz", name, label, value)
    parameter = widget.par.Value0
    parameter.min = minimum
    parameter.max = maximum
    parameter.clampMin = True
    parameter.clampMax = True
    if not existed:
        parameter.val = value
    return widget


def _bind(control, parameter_name, expression):
    parameter = control.par[parameter_name]
    if parameter is None:
        raise RuntimeError(control.path + " missing parameter " + parameter_name)
    parameter.expr = expression


def _install_ui(component, control):
    mode_exists = component.op("InteractionMode") is not None
    mode = _copy_widget(component, "Shape", "InteractionMode", "Interaction Mode", "Hybrid")
    mode.par.Menunames = "Traditional Moses Hybrid"
    mode.par.Menulabels = "Traditional Moses Hybrid"
    if not mode_exists:
        mode.par.Value0 = "Hybrid"

    _copy_widget(component, "TestMode", "MosesEnable", "Moses Gate", True)
    _copy_widget(component, "TestMode", "MosesVirtualMode", "Moses Virtual Test", True)
    _slider(component, "MosesGateWidth", "Moses Gate Width", 0.50, 0.05, 2.0)
    _slider(component, "MosesSafetyMargin", "Moses Safety Margin", 0.10, 0.0, 1.0)
    _slider(component, "MosesTriggerDistance", "Moses Trigger Distance", 0.35, 0.01, 5.0)
    _slider(component, "MosesOpenTime", "Moses Open Time", 0.75, 0.05, 10.0)
    _slider(component, "MosesCloseTime", "Moses Close Time", 1.20, 0.05, 10.0)
    _slider(component, "MosesHoldSeconds", "Moses Hold Time", 1.00, 0.0, 30.0)

    _bind(control, "Enable", "parent().op('MosesEnable').par.Value0")
    _bind(control, "Virtualmode", "parent().op('MosesVirtualMode').par.Value0")
    _bind(control, "Gatewidth", "parent().op('MosesGateWidth').par.Value0")
    _bind(control, "Safetymargin", "parent().op('MosesSafetyMargin').par.Value0")
    _bind(control, "Triggerdistance", "parent().op('MosesTriggerDistance').par.Value0")
    _bind(control, "Opentime", "parent().op('MosesOpenTime').par.Value0")
    _bind(control, "Closetime", "parent().op('MosesCloseTime').par.Value0")
    _bind(control, "Holdseconds", "parent().op('MosesHoldSeconds').par.Value0")

    # The existing panel is vertically aligned. Increase its height so the new
    # controls are visible in the same Run/Perform UI.
    component.par.h = max(int(component.par.h.eval()), 853)
    return mode


def _install_routes(component, mode_widget):
    original = component.op("null6")
    spring = component.op("spring1")
    shape = component.op("switch_shape")
    hybrid_gate = component.op("moses_gate")
    callbacks = component.op("moses_gate_callbacks")
    laser = component.op("laser1")
    monitor = component.op("InputMonitor")
    if None in (original, spring, shape, hybrid_gate, callbacks, laser, monitor):
        raise RuntimeError(component.path + " is missing a required original or Moses operator")

    # Hybrid is the already-tested route: spring deformation followed by gate.
    _connect(hybrid_gate, 0, spring)

    # Moses-only receives the original generated shape and intentionally
    # bypasses spring deformation.
    moses_only = component.op("moses_only_gate") or component.create(scriptSOP, "moses_only_gate")
    if TAG not in moses_only.tags:
        moses_only.tags.add(TAG)
    _connect(moses_only, 0, shape)
    moses_only.par.callbacks = callbacks
    moses_only.nodeX = 450
    moses_only.nodeY = 150
    moses_only.color = (0.72, 0.52, 0.16)

    mode_switch = component.op("interaction_mode_switch") or component.create(switchSOP, "interaction_mode_switch")
    if TAG not in mode_switch.tags:
        mode_switch.tags.add(TAG)
    _connect(mode_switch, 0, original)
    _connect(mode_switch, 1, moses_only)
    _connect(mode_switch, 2, hybrid_gate)
    mode_switch.par.input.expr = "op('InteractionMode').par.Value0.menuIndex"
    mode_switch.nodeX = 350
    mode_switch.nodeY = 50
    mode_switch.color = (0.55, 0.35, 0.78)

    output = component.op("interaction_out") or component.create(nullSOP, "interaction_out")
    if TAG not in output.tags:
        output.tags.add(TAG)
    _connect(output, 0, mode_switch)
    output.nodeX = 350
    output.nodeY = -50

    laser.par.sop = output
    _connect(monitor, 3, output)
    return output


def _lock_laser(component):
    component.op("Brightness").par["Value0"] = 0
    component.op("TestMode").par["Value0"] = False
    device = component.op("laserdevice1")
    _safe_constant(device, "active", False)
    for name in ("redscale", "greenscale", "bluescale"):
        _safe_constant(device, name, 0.0)


def install():
    backup = _backup()
    installed = []
    for path in TARGETS:
        component = op(path)
        if component is None:
            continue
        control = component.op("MosesGateControl")
        if control is None:
            raise RuntimeError(path + " requires the reviewed Moses Gate installation first")
        mode = _install_ui(component, control)
        output = _install_routes(component, mode)
        _lock_laser(component)
        installed.append({"component": path, "output": output.path, "defaultMode": "Hybrid"})
    if not installed:
        raise RuntimeError("No LaserWave01..03 components were found")
    status = op("/project1/AI_BRIDGE/status")
    if status is not None:
        status.text = "Interaction modes installed. Default HYBRID; laser output LOCKED."
    debug("Interaction mode installation complete", installed)
    debug("Backup:", backup)
    return installed


install()

