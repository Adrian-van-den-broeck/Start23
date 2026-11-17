"""Index the final source and explicitly accepted native review evidence."""
from pathlib import Path
import hashlib, json, subprocess

here = Path(__file__).resolve().parent
root = here.parents[3]
runtime = root / '.worktrees/wombo-ui-v2-activities'
scope = json.loads((here / 'scope-audit.json').read_text())
matrix = json.loads((here / 'matrix-ledger.json').read_text())
flow = json.loads((here / 'native-flow-audit.json').read_text())
names = {Path(row['png']).stem for row in matrix}
names.update(row['capture'] for row in flow['checks'])
names.update(f'{width}-font-2-{language}-long-lower-{part}'
             for width in [320, 360, 393, 412]
             for language in ['nl', 'en'] for part in [1, 2])
names.update(['pending-rpe-feedback', 'activity-task-entry',
              'activity-task-320-font-2-entry', 'reduced-motion-week'])
accessibility = json.loads((here / 'accessibility-review.json').read_text())
names.update(accessibility['acceptedCaptures'])
artifacts = []
for name in sorted(names):
    for suffix in ['.png', '.json']:
        path = here / (name + suffix)
        assert path.is_file(), path
        artifacts.append({'path': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    path = here / (name + '.xml')
    if path.exists():
        artifacts.append({'path': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
source = {name: hashlib.sha256((runtime / 'mobile' / name).read_bytes()).hexdigest()
          for name in scope['changedExisting'] + scope['newFiles']}
manifest = {
    'runtime': str(runtime.relative_to(root)).replace('\\', '/'),
    'branch': subprocess.check_output(['git', 'branch', '--show-current'], cwd=runtime, text=True).strip(),
    'baseHead': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=runtime, text=True).strip(),
    'sourceSha256': source,
    'acceptedNativeCaptures': len(names),
    'artifacts': artifacts,
    'diagnosticAndTransientFramesExcluded': True,
}
(here / 'accepted-evidence.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(f'Accepted evidence: {len(names)} native captures; {len(source)} source files fingerprinted.')
