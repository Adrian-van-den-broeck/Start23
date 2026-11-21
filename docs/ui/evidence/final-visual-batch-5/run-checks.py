"""Final mobile checks, with exact exit codes and UTF-8 evidence logs."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json, subprocess

here = Path(__file__).resolve().parent
mobile = here.parents[3] / '.worktrees/wombo-ui-v2-activities/mobile'
assert not (mobile / 'app/dev-calendar-review.tsx').exists()
commands = {
    'jest': ['npm.cmd', 'test', '--', '--watch=false', '--json', '--outputFile=' + str(here / 'full-mobile-tests.json')],
    'typecheck': ['npm.cmd', 'run', 'typecheck'],
    'unused': ['npm.cmd', 'run', 'check:unused'],
}

def run(name):
    result = subprocess.run(commands[name], cwd=mobile, capture_output=True, encoding='utf-8', errors='strict')
    (here / (name + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
    print(name, result.returncode, flush=True)
    return name, result.returncode

with ThreadPoolExecutor(max_workers=3) as pool:
    exits = dict(pool.map(run, commands))
(here / 'command-checks.json').write_text(json.dumps(exits, indent=2) + '\n', encoding='utf-8')
assert all(code == 0 for code in exits.values()), exits
