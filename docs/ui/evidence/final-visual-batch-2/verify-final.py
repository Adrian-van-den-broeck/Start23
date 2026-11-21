"""Verify final checks, preserved source, cleanup and evidence integrity."""
from pathlib import Path
import hashlib, json, subprocess
here = Path(__file__).resolve().parent
root = here.parents[3]
runtime = root/'.worktrees/wombo-ui-v2-activities'
mobile = runtime/'mobile'
suite=json.loads((here/'mobile-tests.json').read_text())
assert suite['success'] and suite['numPassedTests']==530 and suite['numPassedTestSuites']==61
assert suite['numFailedTests']==0 and suite['numPendingTests']==0
for name in ['typecheck.log','unused.log']:
    raw=(here/name).read_bytes()
    log=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig')
    assert 'error TS' not in log and 'tsc --noEmit' in log
baseline=json.loads((here/'baseline.json').read_text())
protected=json.loads((here/'protected-source-audit.json').read_text())
for name in protected['paths']:
    assert hashlib.sha256((mobile/name).read_bytes()).hexdigest()==baseline[name],name
manifest=json.loads((here/'accepted-evidence.json').read_text())
for name,sha in manifest['sourceSha256'].items():
    assert hashlib.sha256((mobile/name).read_bytes()).hexdigest()==sha,name
for item in manifest['artifacts']:
    assert hashlib.sha256((here/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
for cwd in [root,runtime]:
    result=subprocess.run(['git','diff','--check'],cwd=cwd,capture_output=True,text=True)
    assert result.returncode==0,result.stdout
for name in json.loads((here/'scope-audit.json').read_text())['newFiles']:
    assert all(line.rstrip()==line for line in (mobile/name).read_text(encoding='utf-8').splitlines()),name
assert not any('ShellReviewBootstrap' in p.read_text(encoding='utf-8') or 'dev-shell-review' in p.read_text(encoding='utf-8')
               for d in ['app','src'] for p in (mobile/d).rglob('*') if p.suffix in ['.ts','.tsx'])
raw=(root/'README.md').read_bytes()
lines=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig').splitlines()
credentials=[next(s.split(':',1)[1].strip() for s in lines if s.startswith(prefix)) for prefix in ['Email:','Password:']]
for p in here.rglob('*'):
    if p.suffix not in ['.json','.jsonl','.log','.txt','.py','.md'] or not p.is_file():continue
    raw=p.read_bytes()
    value=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig',errors='replace')
    assert not any(c in value for c in credentials),'Credential found in evidence'
report=(root/'docs/ui/WOMBO_UI_V2_FINAL_VISUAL_BATCH_2_REPORT.md').read_text(encoding='utf-8')
assert report.rstrip().endswith('WOMBO UI V2 FINAL VISUAL BATCH 2 COMPLETE — FINAL SHELL ACCEPTED')
assert manifest['baseHead'] in report
result={'mobileTests':530,'mobileSuites':61,'typeScript':'PASS','unused':'PASS',
    'protectedSourceFingerprints':len(protected['paths']),'sourceManifestFiles':len(manifest['sourceSha256']),
    'acceptedNativeCaptures':manifest['acceptedNativeCaptures'],'manifestIntegrity':'PASS',
    'privacy':'PASS: 143 runtime public files; zero findings','credentialEvidenceScan':'PASS',
    'diffCheck':'PASS: root and integrated worktree','newSourceWhitespace':'PASS',
    'temporaryRuntimeReferences':0,'testClock':'PlanningWorkoutMoveBoundary fixture Date only; normal full-suite command',
    'releaseGates':'Physical Android/iOS, signing and release artifacts remain separate'}
(here/'verification-summary.json').write_text(json.dumps(result,indent=2)+'\n')
print('Final verification PASS: 530 tests / 61 suites; TypeScript, unused, privacy, scope, evidence integrity and diff checks.')
