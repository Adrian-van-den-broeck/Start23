import json
import os
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ADB = Path(os.environ["LOCALAPPDATA"]) / "Android/Sdk/platform-tools/adb.exe"
os.environ["ANDROID_USER_HOME"] = str(ROOT / ".runtime/android")


def adb(*args):
    return subprocess.check_output(
        [str(ADB), "-s", "emulator-5554", *args], text=True, stderr=subprocess.DEVNULL
    )


def nodes():
    adb("shell", "uiautomator", "dump", "/sdcard/a9benchmark.xml")
    raw = adb("exec-out", "cat", "/sdcard/a9benchmark.xml")
    return [
        node.attrib
        for node in ET.fromstring(raw).iter("node")
        if node.get("package") == "com.adrivdbs.wombo.a9benchmark"
    ]


def tap(node):
    x1, y1, x2, y2 = map(int, re.findall(r"\d+", node["bounds"]))
    adb("shell", "input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2))


if __name__ == "__main__":
    safe = {
        "Aanmelden",
        "Registreren",
        "Week",
        "Calendar",
        "Kalender",
        "Profiel",
        "Mijn profiel",
        "Testen en kalibratie",
        "Activiteiten",
        "Start check-in",
        "Check-in",
        "Volgende",
        "Terug",
    }
    found = nodes()
    print(
        json.dumps(
            [
                {
                    "class": n["class"],
                    "bounds": n["bounds"],
                    "label": n.get("text", "")
                    if n.get("text", "") in safe
                    else n.get("content-desc", "")
                    if n.get("content-desc", "") in safe
                    else "",
                }
                for n in found
                if n["class"] == "android.widget.EditText"
                or n.get("text", "") in safe
                or n.get("content-desc", "") in safe
            ]
        )
    )
