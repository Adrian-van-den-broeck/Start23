"""Read-only final verification; writes only this batch's evidence ledger."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RUNTIME = ROOT / '.worktrees/wombo-ui-v2-activities'
MOBILE = RUNTIME / 'mobile'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=RUNTIME, text=True).strip()


baseline = json.loads((HERE.parent / 'final-visual-batch-0/baseline-audit.json').read_text())
changed = [name for name, digest in baseline['protected_hashes'].items() if sha(ROOT / name) != digest]
assert set(changed) == {'.worktrees/wombo-ui-v2-activities/mobile/' + name for name in ['package.json', 'package-lock.json', 'jest.config.js']}, changed
assert git('rev-parse', 'HEAD') == baseline['runtime_sha']
assert git('rev-parse', 'refs/heads/feat/wombo-ui-v2') == baseline['local_feature_sha']
subprocess.run(['git', 'diff', '--check'], cwd=RUNTIME, check=True)
source = [path for folder in ['src', 'app'] for path in (MOBILE / folder).rglob('*') if path.suffix in ['.ts', '.tsx'] and '.test.' not in path.name]
patterns = [r'\btss\b', r'planned[_ -]?load', r'realized[_ -]?load', r'private[_ -]?load', r'service_role', r'SUPABASE_SECRET', r'OPENAI_API_KEY', r'DATABASE_PASSWORD']
hits = [(str(path.relative_to(MOBILE)), pattern) for path in source for pattern in patterns if re.search(pattern, path.read_text(encoding='utf-8'), re.I)]
assert not hits, hits
tests = json.loads((HERE / 'mobile-tests.json').read_text(encoding='utf-8'))
assert tests['success'] and tests['numPassedTests'] == 515 and tests['numPassedTestSuites'] == 59
proof = ['gallery-path', 'gallery-icons-middle', 'gallery-icons-bottom', 'gallery-sports', 'gallery-circles', 'gallery-headers-final', 'gallery-action-final']
headers = [f'headers-{width}-font-{font}' for width in [320, 360, 393, 412] for font in [1, 2]]
for name in headers:
    nodes = list(ET.parse(HERE / (name + '.xml')).iter('node'))
    assert any(node.get('text', '').startswith('HeaderLandscape') for node in nodes), name
    assert Image.open(HERE / (name + '.png')).convert('L').crop((0, 150, 1080, 2000)).getextrema()[0] < 100, f'Blank native capture: {name}'
proof += headers + ['week-after']
ledger = {'recordedUtc': datetime.now(timezone.utc).isoformat(), 'runtimeBaseSha': git('rev-parse', 'HEAD'), 'runtimeBranch': git('branch', '--show-current'), 'productionScreenChanges': False, 'classification': 'Live native asset proof; week-after is unchanged production V2 restoration. Other PNGs are diagnostic/intermediate only.', 'captures': {name: json.loads((HERE / (name + '.json')).read_text()) for name in proof}}
(HERE / 'capture-ledger.json').write_text(json.dumps(ledger, indent=2) + '\n', encoding='utf-8')
summary = json.loads((HERE / 'verification-summary.json').read_text())
summary.update({'finalUtc': ledger['recordedUtc'], 'changedProtectedFiles': changed, 'privacySourceCount': len(source), 'privacyHits': hits, 'finalRuntimeStatus': git('status', '--porcelain=v1', '--untracked-files=all'), 'fullMobileTestsPassed': tests['numPassedTests'], 'fullMobileSuitesPassed': tests['numPassedTestSuites']})
(HERE / 'verification-summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
report = ROOT / 'docs/ui/WOMBO_UI_V2_FINAL_VISUAL_BATCH_1A_REPORT.md'
links = re.findall(r'\]\(([^)]+)\)', report.read_text(encoding='utf-8'))
assert all((report.parent / link).exists() for link in links if not link.startswith('https://')), 'Broken report link'
paths = [path for path in HERE.iterdir() if path.is_file() and path.name != 'evidence-manifest.json']
runtime_names = git('diff', '--name-only').splitlines() + git('ls-files', '--others', '--exclude-standard', 'mobile').splitlines()
manifest = {'runtimeBaseSha': ledger['runtimeBaseSha'], 'reportSha256': sha(report), 'files': {path.name: {'bytes': path.stat().st_size, 'sha256': sha(path)} for path in sorted(paths)}, 'runtimeChanges': {name: sha(RUNTIME / name) for name in sorted(runtime_names)}}
(HERE / 'evidence-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print(f'Final evidence: {len(proof)} accepted captures; {len(source)} privacy-scanned files; {len(changed)} authorized existing-file changes; all local report links valid.')
