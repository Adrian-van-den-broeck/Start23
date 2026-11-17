"""Read-only, local baseline provenance audit; never reads credentials."""
import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RUNTIME = ROOT / ".worktrees/wombo-ui-v2-activities"
MOBILE = RUNTIME / "mobile"


def git(*args: str, cwd: Path = RUNTIME) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


lock = json.loads((MOBILE / "package-lock.json").read_text(encoding="utf-8"))
package = json.loads((MOBILE / "package.json").read_text(encoding="utf-8"))
versions = {}
for name, declared in (package["dependencies"] | package["devDependencies"]).items():
    installed = json.loads((MOBILE / "node_modules" / name / "package.json").read_text(encoding="utf-8"))["version"]
    locked = lock["packages"][f"node_modules/{name}"]["version"]
    versions[name] = {"declared": declared, "locked": locked, "installed": installed}
    assert installed == locked, name

source_files = sorted([*(MOBILE / "src").rglob("*.ts"), *(MOBILE / "src").rglob("*.tsx"), *(MOBILE / "app").rglob("*.ts"), *(MOBILE / "app").rglob("*.tsx")])
runtime_files = [p for p in source_files if ".test." not in p.name]
patterns = [r"\btss\b", r"planned[_ -]?load", r"realized[_ -]?load", r"private[_ -]?load", r"service_role", r"SUPABASE_SECRET", r"OPENAI_API_KEY", r"DATABASE_PASSWORD"]
privacy_matches = [{"file": p.relative_to(MOBILE).as_posix(), "pattern": pattern} for p in runtime_files for pattern in patterns if re.search(pattern, p.read_text(encoding="utf-8"), re.IGNORECASE)]
assert not privacy_matches, privacy_matches

manifest = json.loads((ROOT / "docs/ui/reference-screenshots/manifest.json").read_text(encoding="utf-8-sig"))
for item in manifest:
    assert digest(ROOT / "docs/ui/reference-screenshots" / item["screenshot"]) == item["sha256"], item["screenshot"]

protected = [ROOT / "AGENTS.md", ROOT / "mobile/AGENTS.md", ROOT / "docs/implementation/mvp-roadmap.md", *sorted((ROOT / "docs/ui").glob("WOMBO_UI_V2_FINAL_*.md")), ROOT / "docs/ui/WOMBO_UI_SCREENSHOT_REFERENCE_INDEX.md", *sorted((ROOT / "docs/ui/mockups-final").rglob("*")), *sorted((ROOT / "docs/ui/reference-screenshots").rglob("*"))]
protected = [p for p in protected if p.is_file() and p.name != "WOMBO_UI_V2_FINAL_VISUAL_BATCH_0_REPORT.md"]
mobile_files = source_files + [MOBILE / name for name in ("package.json", "package-lock.json", "metro.config.js", "tsconfig.json", "jest.config.js", "app.json")]
preexisting = [ROOT / name for name in (".vscode/tasks.json", "backend/app/modules/coach/weekly_plan.py", "docs/deployment-tasks.md")]
result = {
    "recorded_at": datetime.now(ZoneInfo("Europe/Amsterdam")).isoformat(),
    "local_feature_sha": git("rev-parse", "refs/heads/feat/wombo-ui-v2"),
    "runtime_sha": git("rev-parse", "HEAD"),
    "runtime_branch": git("branch", "--show-current"),
    "runtime_path": str(RUNTIME),
    "runtime_status": git("status", "--porcelain=v1", "--untracked-files=all"),
    "documentation_branch": git("branch", "--show-current", cwd=ROOT),
    "documentation_sha": git("rev-parse", "HEAD", cwd=ROOT),
    "versions": versions,
    "lockfile_version": lock["lockfileVersion"],
    "privacy": {"source_file_count": len(runtime_files), "scope": "mobile/src and mobile/app, excluding .test. files", "patterns": patterns, "matches": privacy_matches},
    "reference_manifest_hashes_verified": len(manifest),
    "protected_hashes": {p.relative_to(ROOT).as_posix(): digest(p) for p in protected + mobile_files + preexisting if p.is_file()},
}
output = HERE / "baseline-audit.json"
if output.exists():
    previous = json.loads(output.read_text(encoding="utf-8"))
    assert result["protected_hashes"] == previous["protected_hashes"], "Protected file bytes changed"
    assert result["local_feature_sha"] == previous["local_feature_sha"]
    assert result["runtime_sha"] == previous["runtime_sha"]
    assert result["runtime_status"] == previous["runtime_status"] == ""
    print("PASS: protected file fingerprints, refs and clean runtime unchanged")
else:
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: result[key] for key in ("recorded_at", "local_feature_sha", "runtime_sha", "runtime_branch", "runtime_status", "lockfile_version", "privacy", "reference_manifest_hashes_verified")}, indent=2))
