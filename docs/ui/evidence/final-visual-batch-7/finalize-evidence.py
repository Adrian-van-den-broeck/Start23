from pathlib import Path
import hashlib,json,re,subprocess
HERE=Path(__file__).resolve().parent
root=HERE.parents[3];work=root/'.worktrees/wombo-ui-v2-activities'
tests=json.loads((HERE/'full-mobile-tests.json').read_text())
assert tests['success'] and tests['numFailedTests']==0 and tests['numFailedTestSuites']==0
assert all(v==0 for v in json.loads((HERE/'command-checks.json').read_text()).values())
native=json.loads((HERE/'native-target-audit.json').read_text())
assert not native['failures'] and not native['developmentOverlays']
assert len(json.loads((HERE/'native-interactions.json').read_text())['results'])==20
assert all(v['pass'] for v in json.loads((HERE/'native-interactions.json').read_text())['results'])
assert json.loads((HERE/'confirmation-target-audit.json').read_text())['pass']
assert all(v['pass'] for v in json.loads((HERE/'contrast.json').read_text())['pairs'])
assert json.loads((HERE/'accessibility-cleanup.json').read_text())['settingsRestored']
assert json.loads((HERE/'device-cleanup.json').read_text())['galleryRemoved']
assert not (work/'mobile/app/dev-batch7-review.tsx').exists()
baseline=json.loads((HERE/'baseline.json').read_text())
actual={str(p.relative_to(work)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['mobile/app','mobile/src'] for p in (work/folder).rglob('*') if p.is_file()}
assert actual.keys()==baseline['sourceHashes'].keys()
changed=sorted(name for name,h in actual.items() if h!=baseline['sourceHashes'][name])
assert len(changed)==5
assert sorted(json.loads((HERE/'scope-audit.json').read_text())['changed'])==changed
refs=json.loads((HERE/'reference-hashes.json').read_text())
assert all(hashlib.sha256((root/'docs/ui'/name).read_bytes()).hexdigest()==h for name,h in refs.items())
report=root/'docs/ui/WOMBO_UI_V2_FINAL_VISUAL_BATCH_7_REPORT.md'
for link in re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8')):
    if link=='evidence/final-visual-batch-7/verification.json':continue
    assert (report.parent/link).exists(),link
subprocess.run(['git','diff','--check'],cwd=work,check=True)
files=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ['verification.json','commits.json']]
hashes={p.relative_to(HERE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
data={'result':'PASS','mobileTests':tests['numPassedTests'],'mobileSuites':tests['numPassedTestSuites'],
      'nativeCases':native['cases'],'fullyVisibleControls':native['fullyVisibleControls'],'exactCallbackChecks':20,
      'changedSources':changed,'protectedUnchanged':len(actual)-len(changed),'referenceFilesUnchanged':len(refs),
      'galleryRemoved':True,'whitespace':'PASS','reportLinks':'PASS','artifactHashes':hashes}
(HERE/'verification.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({k:v for k,v in data.items() if k!='artifactHashes'}))
