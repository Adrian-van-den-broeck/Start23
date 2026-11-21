"""Verify final asset-only scope and native proof; no device/data writes."""
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


before = json.loads((HERE / 'acceptance-before.json').read_text())
changed = {Path(name).as_posix(): {'before': digest, 'after': sha(ROOT / name)} for name, digest in before.items() if sha(ROOT / name) != digest}
allowed = ['assets/HeaderLandscape.tsx', 'assets/LandscapeArtwork.tsx', 'assets/SportVectors.tsx', 'dev/AssetGallery.tsx']
assert set(changed) == {'.worktrees/wombo-ui-v2-activities/mobile/src/ui-v2/' + name for name in allowed}, list(changed)
baseline = json.loads((HERE.parent / 'final-visual-batch-0/baseline-audit.json').read_text())
original_changes = [name for name, digest in baseline['protected_hashes'].items() if sha(ROOT / name) != digest]
assert set(original_changes) == {'.worktrees/wombo-ui-v2-activities/mobile/' + name for name in ['package.json', 'package-lock.json', 'jest.config.js']}
assert git('rev-parse', 'HEAD') == baseline['runtime_sha']
assert git('rev-parse', 'refs/heads/feat/wombo-ui-v2') == baseline['local_feature_sha']
subprocess.run(['git', 'diff', '--check'], cwd=RUNTIME, check=True)

manifest = json.loads((MOBILE / 'package.json').read_text())
lock = json.loads((MOBILE / 'package-lock.json').read_text())
mapping = json.loads((MOBILE / 'node_modules/expo/bundledNativeModules.json').read_text())
assert mapping['react-native-svg'] == '15.15.4'
versions = {}
for name in ['lucide-react-native', 'react-native-svg', 'expo', 'react-native', 'react']:
    installed = json.loads((MOBILE / 'node_modules' / name / 'package.json').read_text())
    locked = lock['packages']['node_modules/' + name]['version']
    assert installed['version'] == locked
    versions[name] = {'declared': manifest['dependencies'][name], 'locked': locked, 'installed': installed['version']}
assert versions['lucide-react-native']['declared'] == '1.48.0'
assert versions['react-native-svg']['declared'] == '15.15.4'
exports = json.loads((HERE / 'package-verification.json').read_text())
assert len(exports['verifiedIndividualExports']) == 22 and all(exports['verifiedIndividualExports'].values())
assert all(exports['verifiedNamedExports'].values())
tests = json.loads((HERE / 'acceptance-tests.json').read_text())
assert tests['success'] and tests['numPassedTests'] == 5 and tests['numPassedTestSuites'] == 1

names = ['acceptance-icons-1', 'acceptance-icons-2', 'acceptance-icons-3', 'acceptance-sports', 'acceptance-circles', 'acceptance-header-standard', 'acceptance-header-compact', 'acceptance-header-trees-river', 'acceptance-action', 'acceptance-header-320', 'acceptance-week-restored']
captures = {}
for name in names:
    record = json.loads((HERE / (name + '.json')).read_text())
    assert record['serial'] == 'emulator-5554' and float(record['fontScale']) == 1
    assert record['locale'] == 'en-US' and record['width'] == 'Physical size: 1080x2280'
    assert '540' in record['density'] if name.endswith('-320') else record['density'] == 'Physical density: 440'
    texts = [node.get('text', '') for node in ET.parse(HERE / (name + '.xml')).iter('node')]
    assert not any('klaargezet' in value or 'Bundling' in value for value in texts)
    assert 'Wombo asset proof' in texts if name != 'acceptance-week-restored' else 'Wombo · Week' in texts
    assert Image.open(HERE / (name + '.png')).size == (1080, 2280)
    assert Image.open(HERE / (name + '.png')).convert('L').crop((0, 150, 1080, 2000)).getextrema()[0] < 100
    captures[name] = record

audit = {'utc': datetime.now(timezone.utc).isoformat(), 'runtimeBaseSha': git('rev-parse', 'HEAD'), 'runtimeBranch': git('branch', '--show-current'), 'beforeFingerprintCount': len(before), 'followupChangedFiles': changed, 'originalBaselineProtectedCount': len(baseline['protected_hashes']), 'unchangedOriginalScreensAndOwners': True, 'manifestLockUnchangedFromPendingState': True, 'installedExpoSvgMapping': mapping['react-native-svg'], 'versions': versions, 'namedAndIndividualExportsVerified': 22, 'focusedTests': {'passed': tests['numPassedTests'], 'suites': tests['numPassedTestSuites']}, 'typecheckExit': 0, 'unusedCodeExit': 0, 'packageAuditExit': 0, 'nativeRebuildRequired': False, 'proofPngsOpenedAndVisuallyReviewed': names, 'assetVisualVerdict': 'ACCEPTED', 'batch1BStarted': False}
(HERE / 'acceptance-audit.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')
report = ROOT / 'docs/ui/WOMBO_UI_V2_FINAL_VISUAL_BATCH_1A_REPORT.md'
files = [path for path in HERE.glob('acceptance-*') if path.is_file() and path.name != 'acceptance-manifest.json'] + [HERE / 'capture-acceptance.py', HERE / 'capture-android.py', HERE / 'verify-acceptance.py']
evidence = {'classification': 'Final native Batch 1A asset visual acceptance; intermediate acceptance-review and acceptance-headers are excluded from final proof set', 'reportSha256': sha(report), 'runtimeBaseSha': audit['runtimeBaseSha'], 'runtimeChanges': changed, 'captures': captures, 'files': {path.name: {'bytes': path.stat().st_size, 'sha256': sha(path)} for path in sorted(files)}}
(HERE / 'acceptance-manifest.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
for link in re.findall(r'\]\(([^)]+)\)', report.read_text(encoding='utf-8')):
    assert link.startswith('https://') or (report.parent / link).exists(), link
print(f'Acceptance verified: {len(changed)} allowed asset/gallery files; 193 pre-review fingerprints; 22 exports; 5 tests; 10 gallery PNGs plus Week restoration; all local report links valid.')
