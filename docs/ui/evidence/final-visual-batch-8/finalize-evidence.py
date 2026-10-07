from pathlib import Path
import hashlib,json,re,subprocess
HERE=Path(__file__).resolve().parent
root=HERE.parents[3];work=root/'.worktrees/wombo-ui-v2-activities'
read=lambda name:json.loads((HERE/name).read_text(encoding='utf-8'))
tests=read('full-mobile-tests.json')
assert tests['success'] and tests['numFailedTests']==tests['numFailedTestSuites']==0
assert all(v==0 for v in read('command-checks.json').values())
native=read('native-target-audit.json')
assert native['cases']==83 and not native['failures'] and not native['developmentOverlays']
callbacks=read('native-interactions.json')['results']
assert len(callbacks)==25 and all(v['pass'] for v in callbacks)
assert read('native-occurrence-return-audit.json')['pass']
assert all(v['pass'] for v in read('contrast.json')['pairs'])
assert read('accessibility-cleanup.json')['settingsRestored']
assert read('accessibility-review.json')['result']=='PASS'
assert read('device-cleanup.json')['galleryRemoved']
assert not (work/'mobile/app/dev-batch8-review.tsx').exists()
baseline=read('baseline.json')
actual={str(p.relative_to(work)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['mobile/app','mobile/src'] for p in (work/folder).rglob('*') if p.is_file()}
assert actual.keys()==baseline['sourceHashes'].keys()
changed=sorted(name for name,h in actual.items() if h!=baseline['sourceHashes'][name])
assert len(changed)==5 and sorted(read('scope-audit.json')['changed'])==changed
assert read('functional-freeze.json')['result']=='PASS'
refs=read('reference-hashes.json')
assert all(hashlib.sha256((root/'docs/ui'/name).read_bytes()).hexdigest()==h for name,h in refs.items())
report=root/'docs/ui/WOMBO_UI_V2_FINAL_VISUAL_BATCH_8_REPORT.md'
for link in re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8')):
    if link=='evidence/final-visual-batch-8/verification.json':continue
    assert (report.parent/link).exists(),link
subprocess.run(['git','diff','--check'],cwd=work,check=True)
files=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ['verification.json','commits.json']]
hashes={p.relative_to(HERE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
data={'result':'PASS','mobileTests':tests['numPassedTests'],'mobileSuites':tests['numPassedTestSuites'],
 'nativeCases':native['cases'],'fullyVisibleControls':native['fullyVisibleControls'],'exactCallbackChecks':len(callbacks),
 'changedSources':changed,'protectedUnchanged':len(actual)-len(changed),'referenceFilesUnchanged':len(refs),
 'galleryRemoved':True,'whitespace':'PASS','reportLinks':'PASS','artifactHashes':hashes}
(HERE/'verification.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({k:v for k,v in data.items() if k!='artifactHashes'}))
