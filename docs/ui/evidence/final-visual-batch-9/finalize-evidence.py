from pathlib import Path
import hashlib,json,re,subprocess
HERE=Path(__file__).resolve().parent
root=HERE.parents[3];work=root/'.worktrees/wombo-ui-v2-activities'
read=lambda name:json.loads((HERE/name).read_text(encoding='utf-8'))
tests=read('full-mobile-tests.json');assert tests['success'] and tests['numFailedTests']==tests['numFailedTestSuites']==0
assert tests['numPassedTests']==562 and tests['numPassedTestSuites']==62
assert all(v==0 for v in read('command-checks.json').values())
assert read('post-cleanup-checks.json')=={'typecheck':0,'unused':0}
native=read('native-target-audit.json');assert native['cases']==101 and not native['failures'] and not native['developmentOverlays']
callbacks=read('native-interactions.json')['results'];assert len(callbacks)==25 and all(v['pass'] for v in callbacks)
assert read('native-state-audit.json')['result']=='PASS' and read('native-state-audit.json')['cases']==101
assert all(v['pass'] for v in read('contrast.json')['pairs'])
assert read('keyboard-review.json')['pass'] and read('keyboard-cleanup.json')['softKeyboardReviewOverrideRestored'] and read('accessibility-cleanup.json')['settingsRestored']
assert read('native-navigation-audit.json')['result']=='PASS' and read('native-navigation-audit.json')['cases']==101
assert read('accessibility-review.json')['result']=='PASS'
assert read('device-cleanup.json')['galleryRemoved'] and read('host-cleanup.json')['owned8084Stopped']
assert not (work/'mobile/app/dev-batch9-review.tsx').exists()
baseline=read('baseline.json')
actual={str(p.relative_to(work)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['mobile/app','mobile/src'] for p in (work/folder).rglob('*') if p.is_file()}
assert actual.keys()==baseline['sourceHashes'].keys()
changed=sorted(name for name,h in actual.items() if h!=baseline['sourceHashes'][name]);assert len(changed)==8 and sorted(read('scope-audit.json')['changed'])==changed
assert read('functional-freeze.json')['result']=='PASS'
assert actual==read('final-source-hashes.json')['sources']
refs=read('reference-hashes.json');assert len(refs)==24 and all(hashlib.sha256((root/'docs/ui'/name).read_bytes()).hexdigest()==h for name,h in refs.items())
assert read('visual-review.json')['result']=='PASS'
report=root/'docs/ui/WOMBO_UI_V2_FINAL_VISUAL_BATCH_9_REPORT.md'
for link in re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8')):
    if link=='evidence/final-visual-batch-9/verification.json':continue
    assert (report.parent/link).exists(),link
subprocess.run(['git','diff','--check'],cwd=work,check=True)
files=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ['verification.json','commits.json'] and not p.name.startswith('emulator-recovery')]
hashes={p.relative_to(HERE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
data={'result':'PASS','mobileTests':562,'mobileSuites':62,'clock':'Scoped external fixture date only for two unchanged proposal tests; default-clock full pass is not claimed','nativeCases':101,'fullyVisibleControls':native['fullyVisibleControls'],'exactCallbackChecks':len(callbacks),'changedSources':changed,'protectedUnchanged':200,'referenceFilesUnchanged':24,'galleryRemoved':True,'whitespace':'PASS','reportLinks':'PASS','physicalTalkBackReleaseGate':'Outside this Android visual batch; emulator focus/activation limitations explicitly documented','artifactHashes':hashes}
(HERE/'verification.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps({k:v for k,v in data.items() if k!='artifactHashes'}))
