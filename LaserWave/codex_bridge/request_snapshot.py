"""Create a new read-only snapshot request from Windows/Python."""

import datetime
import json
from pathlib import Path


bridge_folder = Path(__file__).resolve().parent
command_folder = bridge_folder / "bridge_io" / "commands"
command_folder.mkdir(parents=True, exist_ok=True)
command_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
command_path = command_folder / (command_id + "_snapshot.json")
command_path.write_text(
    json.dumps(
        {"id": command_id, "action": "snapshot", "root": "/project1"},
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print(command_path)
