"""Release-emulator public UI marker comparisons. No raw UI/data is logged."""

import argparse
import json
import re
import statistics
import subprocess
import time
import urllib.request

from native_ui import ROOT, adb, nodes, tap

PACKAGE = "com.adrivdbs.wombo.a9benchmark"
pixels = subprocess.Popen(
    ["node", str(ROOT / "mobile/performance/native/pixels.cjs")],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
)


def pixel_command(command):
    pixels.stdin.write(json.dumps(command) + "\n")
    pixels.stdin.flush()
    return json.loads(pixels.stdout.readline())


def http(route):
    with urllib.request.urlopen("http://127.0.0.1:18749/" + route) as response:
        return json.load(response)


def capture(points):
    return pixel_command({"action": "capture", "key": points})


def bounds(node):
    return tuple(map(int, re.findall(r"\d+", node["bounds"])))


def reference(node):
    return pixel_command({"action": "reference", "bounds": bounds(node)})["key"]


def public_text(predicate):
    matches = [n for n in nodes() if predicate(n.get("text", ""))]
    assert matches, "Public content marker unavailable"
    return matches[-1]


def measure(operation, trigger, points, required):
    time.sleep(0.5)
    http("__reset")
    start = time.perf_counter()
    receipt = trigger()
    first_marker = None
    capture_costs = []
    rows = []
    for _ in range(120):
        frame = capture(points)
        elapsed = (time.perf_counter() - start) * 1000
        capture_costs.append(frame["capture_ms"])
        rows = http("__metrics")
        authoritative = required is None or any(
            required(row) and "completed" in row for row in rows
        )
        if frame["difference"] < 12 and authoritative:
            first_marker = elapsed
            break
    assert first_marker is not None, "Content deadline reached in synthetic benchmark"
    launch = re.search(r"TotalTime: (\d+)", receipt or "")
    result = {
        "operation": operation,
        "data_confirmed_marker_ms": first_marker,
        "screen_capture_median_ms": statistics.median(capture_costs),
        "screen_capture_max_ms": max(capture_costs),
        "samples": len(capture_costs),
        "api_requests": len(rows),
        "route_counts": {
            route: sum(row["route"] == route for row in rows)
            for route in sorted({row["route"] for row in rows})
        },
        "network_ms": [
            row["completed"] - row["started"] for row in rows if "completed" in row
        ],
    }
    if launch:
        result["android_first_draw_ms"] = int(launch.group(1))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--runs", type=int, default=5)
    args = parser.parse_args()
    # References contain only public headings/form labels, kept in memory.
    week = reference(public_text(lambda text: text.startswith("Week van ")))
    current = nodes()
    calendar_tab = next(
        n
        for n in current
        if n.get("content-desc") == "Calendar" and n.get("clickable") == "true"
    )
    tab_bounds = bounds(calendar_tab)
    tap(calendar_tab)
    time.sleep(0.8)
    calendar = reference(public_text(lambda text: text == "Calendar"))
    # Week tab coordinates are stable across this unchanged V1 design.
    week_tab = next(
        n
        for n in nodes()
        if n.get("content-desc") == "Week" and n.get("clickable") == "true"
    )
    week_bounds = bounds(week_tab)
    tap(week_tab)
    time.sleep(0.5)
    profile_menu = next(
        n
        for n in nodes()
        if n.get("content-desc") == "Profielmenu" and n.get("clickable") == "true"
    )
    profile_menu_bounds = bounds(profile_menu)
    tap(profile_menu)
    time.sleep(0.6)
    profile_item = next(
        n
        for n in nodes()
        if n.get("content-desc") == "Intakeprofiel" and n.get("clickable") == "true"
    )
    profile_item_bounds = bounds(profile_item)
    tap(profile_item)
    time.sleep(0.8)
    profile = reference(public_text(lambda text: text == "Voornaam (optioneel)"))
    adb("shell", "input", "keyevent", "4")
    time.sleep(0.5)

    def coordinate_tap(rect):
        x1, y1, x2, y2 = rect
        return adb("shell", "input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2))

    results = []
    for run in range(args.runs):
        adb("shell", "am", "force-stop", PACKAGE)
        row = measure(
            "authenticated-startup",
            lambda: adb("shell", "am", "start", "-W", "-n", PACKAGE + "/.MainActivity"),
            week,
            lambda row: row["route"].startswith("/api/v1/weekly-plans/"),
        )
        row["run"] = run
        results.append(row)
        row = measure(
            "week-calendar-cold",
            lambda: coordinate_tap(tab_bounds),
            calendar,
            lambda row: row["route"] == "/api/v1/calendar",
        )
        row["run"] = run
        results.append(row)
        row = measure(
            "calendar-week-warm", lambda: coordinate_tap(week_bounds), week, None
        )
        row["run"] = run
        results.append(row)
        row = measure(
            "week-calendar-warm", lambda: coordinate_tap(tab_bounds), calendar, None
        )
        row["run"] = run
        results.append(row)
        coordinate_tap(week_bounds)
        time.sleep(0.6)
        for visit in ("cold", "warm"):
            coordinate_tap(profile_menu_bounds)
            time.sleep(0.6)
            row = measure(
                "profile-" + visit,
                lambda: coordinate_tap(profile_item_bounds),
                profile,
                lambda row: row["route"] == "/api/v1/onboarding",
            )
            row["run"] = run
            results.append(row)
            adb("shell", "input", "keyevent", "4")
            time.sleep(0.5)
        print(
            json.dumps({"run": run, "completed_operations": len(results)}), flush=True
        )
    (ROOT / args.output).write_text(
        json.dumps(
            {
                "environment": (
                    "Pixel 4 Android 15 API35 x86_64 emulator; isolated Hermes "
                    "release APK; synthetic localhost 40ms, auxiliary intake "
                    "reads 240ms; host screenshot sampling overhead included. "
                    "Marker is fully readable public heading/form label after "
                    "authoritative response, not physical-device or production latency."
                ),
                "measurements": results,
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    try:
        main()
    finally:
        pixels.terminate()
