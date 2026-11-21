"""Read-only Railway status; print only an explicit metadata allowlist."""
import json
import subprocess
from pathlib import Path

CLI = r"C:/Users/Adria/AppData/Local/npm-cache/_npx/d991ede4b4a6395c/node_modules/@railway/cli/bin/railway.exe"
result = subprocess.run(
    [CLI, "status", "--environment", "production", "--json"],
    cwd=r"F:/Projecten Business/Start23/Code",
    capture_output=True, text=True, timeout=50,
)
output = {"command": "railway status --environment production --json", "exit_code": result.returncode}
if result.returncode:
    output["error"] = result.stderr[:700]
else:
    data = json.loads(result.stdout)
    allowed = {"id", "name", "status", "createdAt", "commitHash", "commitMessage", "branch", "repo", "deploymentId", "environmentId", "serviceId", "domain", "rootDirectory", "builder", "healthcheckPath", "autoDeploy", "waitForCI"}
    fields = {}
    def walk(value, path=""):
        if isinstance(value, dict):
            for key, item in value.items():
                if key.lower() in {"variables", "variablevalues", "secrets"}:
                    continue
                location = path + "/" + key
                if key in allowed and not isinstance(item, (dict, list)):
                    fields[location] = item
                walk(item, location)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, path + "/" + str(index))
    walk(data)
    output["fields"] = fields
target = Path(__file__).with_name("railway-release-metadata.json")
target.write_text(json.dumps(output, indent=2), encoding="utf-8")
print(target.read_text(encoding="utf-8"))
