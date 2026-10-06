"""Request a read-only export of DAT text from the LaserWave networks."""

import datetime
import json
from pathlib import Path


bridge_folder = Path(__file__).resolve().parent
command_folder = bridge_folder / "bridge_io" / "commands"
command_folder.mkdir(parents=True, exist_ok=True)
command_id = "laserwave_texts_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
command_path = command_folder / (command_id + ".json")
command_path.write_text(
    json.dumps({
        "id": command_id,
        "action": "snapshot_texts",
        "roots": [
            "/project1/LaserWave01",
            "/project1/LaserWave02",
            "/project1/LaserWave03",
        ],
    }, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(command_path)
