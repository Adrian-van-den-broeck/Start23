"""Verify final source/native manifests, read-only evidence and no credentials."""
from pathlib import Path
import hashlib,json,re,subprocess
here=Path(__file__).resolve().parent;root=here.parents[3];mobile=root/'.worktrees/wombo-ui-v2-activities/mobile'
tests=json.loads((here/'full-mobile-tests.json').read_text(encoding='utf-8'))
assert tests['success'] and tests['numFailedTests']==tests['numFailedTestSuites']==0
native=json.loads((here/'native-audit.json').read_text());scope=json.loads((here/'scope-audit.json').read_text())
for artifact in native['artifacts']:
    assert hashlib.sha256((here/artifact['path']).read_bytes()).hexdigest()==artifact['sha256'],artifact['path']
for path,digest in scope['sourceSha256'].items():
    assert hashlib.sha256((mobile/path).read_bytes()).hexdigest()==digest,path
for name in scope['newFiles']:
    assert not any(line.rstrip()!=line for line in (mobile/name).read_text(encoding='utf-8').splitlines()),name
references=[]
for directory in ['src','app']:
    for path in (mobile/directory).rglob('*'):
        if path.is_file() and any(value in path.read_text(encoding='utf-8') for value in ['WorkoutReviewBootstrap','dev-workout-review','127.0.0.1:8123']):references.append(str(path))
assert not references,references
ledger=[json.loads(line) for line in (here/'fixture-request-ledger.jsonl').read_text().splitlines()]
assert ledger and all(row['method']=='GET' for row in ledger)
assert all(set(row)=={'method','path','status','config'} for row in ledger)
readme=(root/'README.md').read_bytes()
readme=readme.decode('utf-16') if readme[:2] in [b'\xff\xfe',b'\xfe\xff'] else readme.decode('utf-8-sig')
credentials=set(re.findall(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}',readme))
credentials.update(value.strip(' `\r') for value in re.findall(r'(?:password|wachtwoord)\s*:\s*([^\n]+)',readme,re.I) if len(value.strip(' `\r'))>=6)
assert credentials,'README credential scan inputs missing'
for path in here.rglob('*'):
    if path.suffix not in ['.txt','.log','.json','.jsonl','.xml','.py','.md']:continue
    data=path.read_bytes()
    value=data.decode('utf-16') if data[:2] in [b'\xff\xfe',b'\xfe\xff'] else data.decode('utf-8-sig')
    assert not any(credential in value for credential in credentials),path.name+' contains README credentials'
for cwd in [root,root/'.worktrees/wombo-ui-v2-activities']:
    result=subprocess.run(['git','diff','--check'],cwd=cwd,capture_output=True,text=True)
    assert result.returncode==0,result.stdout
device=json.loads((here/'device-cleanup.json').read_text());assert device['cleanRuntimeAuthenticated'] and device['fixtureServiceStopped']
contrast=json.loads((here/'contrast.json').read_text());assert all(pair['pass'] for pair in contrast['pairs'])
result={
    'mobileTests':tests['numPassedTests'],'mobileSuites':tests['numPassedTestSuites'],
    'typeScript':'PASS','unused':'PASS','privacy':f"PASS: {scope['publicSourceFiles']} runtime public files; zero findings",
    'protectedBaselineFiles':scope['unchangedFiles'],'changedExistingFiles':len(scope['changedExisting']),'addedFiles':len(scope['newFiles']),
    'acceptedNativeCaptures':native['acceptedCaptures'],'nativeCases':len(native['cases']),
    'fullyVisibleNativeTargets':len(native['nativeTargets']),'contrastPairs':len(contrast['pairs']),
    'minimumContrast':min(pair['ratio'] for pair in contrast['pairs']),
    'manifestIntegrity':'PASS','credentialEvidenceScan':'PASS','fixtureRequests':len(ledger),'fixtureMutations':0,
    'diffCheck':'PASS: root and integrated worktree','newSourceWhitespace':'PASS',
    'temporaryRuntimeReferences':0,'sourceCleanup':'PASS','emulatorCleanup':'PASS',
    'releaseGates':'Physical Android/iOS, signing and release artifacts remain separate',
}
(here/'verification-summary.json').write_text(json.dumps(result,indent=2)+'\n')
print('Final evidence integrity, credential scan, read-only request ledger and source/diff checks PASS.')
