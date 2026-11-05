"""Validate immutable paired BUILD evidence and render its private report."""

import json
from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Any

DIRECTORY = Path(__file__).resolve().parents[2] / "docs/catalog/implementation"
EVIDENCE = DIRECTORY / "build-search"


def seconds(value: dict[str, Any], key: str) -> str:
    return f"{value[key]:.6f}" if key in value else "TIMEOUT (8s)"


def outcome(value: dict[str, Any]) -> str:
    result = value["result"]
    return str(result.get("code", result["outcome"]))


def table_row(*values: object) -> str:
    return "| " + " | ".join(str(value) for value in values) + " |"


def main() -> None:
    data = {
        (variant, mode): json.loads((EVIDENCE / f"{variant}_{mode}.json").read_text())
        for variant in ("accepted", "optimized")
        for mode in ("cold", "preloaded", "profile")
    }
    cases = set(data["accepted", "cold"]["cases"])
    assert len(cases) == 40
    parity = {}
    for mode in ("cold", "preloaded", "profile"):
        before = data["accepted", mode]["cases"]
        after = data["optimized", mode]["cases"]
        assert set(before) == set(after) == cases
        matched = 0
        for key, row in before.items():
            new = after[key]
            fingerprint = data["accepted", "cold"]["cases"][key]["ready"][
                "input_sha256"
            ]
            assert (
                row["ready"]["input_sha256"]
                == new["ready"]["input_sha256"]
                == fingerprint
            ), key
            if row["result"]["outcome"] != "DIAGNOSTIC_TIMEOUT":
                assert row["result"] == new["result"], (mode, key)
                assert row["output_sha256"] == new["output_sha256"], (mode, key)
                matched += 1
            for variant, entry in (("accepted", row), ("optimized", new)):
                if entry.get("independent_checks"):
                    assert (
                        entry["independent_checks"]["legacy_independent_constraints"]
                        == "PASS"
                    ), (mode, key)
                if entry["result"]["outcome"] != "DIAGNOSTIC_TIMEOUT":
                    assert (
                        entry["result"] == data[variant, "cold"]["cases"][key]["result"]
                    ), (variant, mode, key)
        parity[mode] = matched
    lines = [
        "# Joren V6 BUILD search benchmarks",
        "",
        "2026-11-05, Europe/Amsterdam. Private synthetic diagnostics; no activation.",
        "",
        "Start: `12fde3bd542b42e8259b130be797f673a8c2ded6`. "
        "Implementation/delivery lineage: [optimization "
        "report](JOREN_V6_BUILD_SEARCH_OPTIMIZATION.md).",
        "",
        "All six matrices use the complete unchanged 40-case corpus and "
        "digest-pinned accepted Phase 1 oracle. "
        "Every input fingerprint matches. Completed comparisons use full "
        "canonical result dictionaries and "
        "output hashes (all fields, errors/messages, ordered snapshots, "
        "dates, warnings, and identities). "
        "Every returned plan passes the independent legacy checks. A "
        "timeout supplies no expected plan.",
        "",
        "Runs were serial, with no concurrent benchmark variants or "
        "test/typecheck load. "
        "Cold wall time starts before process creation and retains the "
        "eight-second total deadline. "
        "Preloaded runs separately bound setup, then give the planner "
        "call eight seconds; their wall column "
        "excludes setup. They do not replace a cold timeout. Profile "
        "timing includes observer overhead "
        "and is never used as uninstrumented speed evidence. Host load is"
        " uncontrolled and these are local "
        "single samples, not an SLA.",
        "",
        "| Mode | Accepted timeouts | Optimized timeouts | Exact accepted"
        " completions |",
        "| --- | --- | --- | --- |",
    ]
    for mode in ("cold", "preloaded", "profile"):
        counts = [
            Counter(r["result"]["outcome"] for r in data[v, mode]["cases"].values())
            for v in ("accepted", "optimized")
        ]
        lines.append(
            table_row(
                mode,
                counts[0]["DIAGNOSTIC_TIMEOUT"],
                counts[1]["DIAGNOSTIC_TIMEOUT"],
                parity[mode],
            )
        )
    for mode in ("cold", "preloaded"):
        lines += [
            "",
            f"## All 40 {mode} outcomes",
            "",
            "| Case | Accepted outcome | Wall / planner sec | Optimized "
            "outcome | Wall / planner sec | Check |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for key in sorted(cases):
            before = data["accepted", mode]["cases"][key]
            after = data["optimized", mode]["cases"][key]
            check = (
                "EXACT"
                if before["result"]["outcome"] != "DIAGNOSTIC_TIMEOUT"
                else "independent legacy PASS"
                if after.get("independent_checks")
                else "unreturned"
            )
            lines.append(
                table_row(
                    key,
                    outcome(before),
                    seconds(before, "wall_seconds")
                    + " / "
                    + seconds(before, "planner_seconds"),
                    outcome(after),
                    seconds(after, "wall_seconds")
                    + " / "
                    + seconds(after, "planner_seconds"),
                    check,
                )
            )
    lines += [
        "",
        "## Instrumented work and memory",
        "",
        "DP transitions and exact half construction/join attempts are "
        "separate operations, not interchangeable "
        "timings. Expanded/evaluated counts refer to DP states; exact "
        "representatives evaluated are separate. "
        "Repeated counts distinguish DP destination collisions from exact"
        " representative collisions. "
        "Peak DP residency includes the current and next dictionaries; "
        "exact residency is the representative "
        "dictionary plus separately reported constructed half entries. "
        "RSS is the process lifetime peak "
        "working set, including imports, catalog, observer, and helper "
        "tables, measured through Windows "
        "GetProcessMemoryInfo. It is not incremental planner-only "
        "allocation. Timeout checkpoints are "
        "partial lower bounds, including resident peaks; elapsed active "
        "search is an open-stage observation.",
        "",
        "| Variant / case | Outcome | Search sec | DP transitions | "
        "Halves / joins | Expanded / evaluated DP | Evaluated exact | "
        "Repeated DP / exact | Peak DP / exact states | Peak RSS MiB | "
        "Scheduling calls |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for variant in ("accepted", "optimized"):
        for key in sorted(cases):
            row = data[variant, "profile"]["cases"][key]
            profile = row.get("profile") or {}
            c = profile.get("counts", {})
            stages = profile.get("stages", {})
            search = stages.get("combination_search", {}).get(
                "inclusive_seconds",
                profile.get("active_stages", {}).get("combination_search"),
            )
            timing = f"{search:.6f}" if search is not None else "n/a"
            if row["result"]["outcome"] == "DIAGNOSTIC_TIMEOUT":
                timing += " partial"
            rss = profile.get("peak_resident_bytes", 0) / 1048576

            def pair(first: str, second: str) -> str:
                return f"{c.get(first, 0)} / {c.get(second, 0)}"

            lines.append(
                table_row(
                    f"{variant} / {key}",
                    outcome(row),
                    timing,
                    c.get("candidate_transitions", 0),
                    pair("exact_half_entries", "exact_join_attempts"),
                    pair("states_expanded", "states_evaluated"),
                    c.get("exact_states_evaluated", 0),
                    pair("repeated_states", "exact_repeated_states"),
                    pair("peak_dp_resident_states", "peak_exact_resident_states"),
                    f"{rss:.2f}",
                    stages.get("schedule_workouts", {}).get("calls", 0),
                )
            )
    lines += [
        "",
        "## Remaining timeout",
        "",
        "`current:build_4` remains a timeout, not a proof of "
        "infeasibility. Its profile shows the short "
        "exact join reaching its work ceiling followed by ongoing DP "
        "combination expansion. "
        "The unchanged required swimming template has high load 54.9, all"
        " other eligible loads are integers, "
        "and the high budget is 110. A valid plan can contain one or two "
        "swims; its fractional total is "
        "therefore .9 or .8, so exact 550 is unavailable. The exact "
        "shortcut correctly falls back. "
        "The larger week-four high/Z5 option space then requires a "
        "nonexact optimum across the original "
        "count bound. No new nonexact lattice-bound strategy is claimed or activated. "
        "Counters above bound the actual remaining expansion; scheduling "
        "calls remain a small fraction "
        "of elapsed search. No timeout or rule was relaxed.",
        "",
        "All four V6 BUILD cases now return. Previous61 and historical61 "
        "BUILD 1-3 now return; "
        "their already-completed BUILD 4 outcomes remain exact. Current "
        "BUILD 1-3 now return. "
        "Beginner, zero-history, recovery, taper, restriction, "
        "capability, explicit-repeat, and "
        "availability cases remain regression checks with full-output "
        "equality where the accepted "
        "engine returned.",
        "",
        "The prospective budget/sport-time/suitability diagnostics are "
        "separate from legacy validity. "
        "In particular a returned legacy plan can fail the prospective "
        "per-sport active-time policy; "
        "missing swim time remains UNVERIFIED. See [policy "
        "gap](JOREN_V6_BUDGET_POLICY_GAP.md).",
        "",
        "## Reproduction and custody",
        "",
        "From backend, run each command to completion before the next, "
        "using new output paths:",
        "",
        "```text",
        "python -B -m benchmarks.v6_planner_performance --variant "
        "accepted --output NEW_ACCEPTED_COLD",
        "python -B -m benchmarks.v6_planner_performance --variant "
        "optimized --output NEW_OPTIMIZED_COLD",
        "python -B -m benchmarks.v6_planner_performance --variant "
        "accepted --preloaded --output NEW_ACCEPTED_PRELOADED",
        "python -B -m benchmarks.v6_planner_performance --variant "
        "optimized --preloaded --output NEW_OPTIMIZED_PRELOADED",
        "python -B -m benchmarks.v6_planner_performance --variant "
        "accepted --instrument --output NEW_ACCEPTED_PROFILE",
        "python -B -m benchmarks.v6_planner_performance --variant "
        "optimized --instrument --output NEW_OPTIMIZED_PROFILE",
        "python -B -m benchmarks.build_search_report",
        "```",
        "",
        "Exploratory attempts are preserved under "
        "`build-search/exploratory/`; they are excluded from "
        "all delivered timing comparisons. Some early exploratory runs "
        "overlapped briefly and are "
        "not performance evidence. Historical Phase 1 files were not "
        "overwritten. The report generator "
        "asserts parity/fingerprints and observer transparency before "
        "rendering these tables.",
        "",
        "| Verified evidence | SHA-256 |",
        "| --- | --- |",
    ]
    for path in sorted(EVIDENCE.glob("*.json")):
        if "checkpoint" not in path.name:
            lines.append(f"| {path.name} | {sha256(path.read_bytes()).hexdigest()} |")
    (DIRECTORY / "JOREN_V6_BUILD_SEARCH_BENCHMARKS.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps({"parity": parity, "inputs": 40}, sort_keys=True))


if __name__ == "__main__":
    main()
