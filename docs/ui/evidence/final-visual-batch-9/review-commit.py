from pathlib import Path
import hashlib,json,os,subprocess
HERE=Path(__file__).resolve().parent
root=HERE.parents[3];work=root/'.worktrees/wombo-ui-v2-activities'
baseline=json.loads((HERE/'baseline.json').read_text())['baselineCommit']
verification=json.loads((HERE/'verification.json').read_text());assert verification['result']=='PASS'
ref='refs/heads/feat/wombo-ui-v2-final-batch-9'
assert subprocess.run(['git','show-ref','--verify','--quiet',ref],cwd=root).returncode==1
A=['mobile/src/ui-v2/screens/ActivitiesScreen.tsx','mobile/src/ui-v2/components/ActivitySummary.tsx','mobile/src/ui-v2/primitives/Notice.tsx']
B=['mobile/src/ui-v2/screens/ActivityEntryScreen.tsx','mobile/src/ui-v2/screens/ActivityFeedbackScreen.tsx','mobile/src/ui-v2/components/RpeChoices.tsx','mobile/src/ui-v2/primitives/ChoiceRow.tsx','mobile/src/ui-v2/screens/ActivitiesScreens.test.tsx']
assert sorted(A+B)==sorted(n.replace('\\','/') for n in verification['changedSources'])
def protected_state(folder):
    def read_git(*args):return subprocess.check_output(['git',*args],cwd=folder).decode('utf-8').strip()
    p=Path(read_git('rev-parse','--git-path','index'))
    if not p.is_absolute():p=folder/p
    return {'branch':read_git('symbolic-ref','--short','HEAD'),'head':read_git('rev-parse','HEAD'),'indexHash':hashlib.sha256(p.read_bytes()).hexdigest(),'trackedStatus':read_git('status','--porcelain','--untracked-files=no')}
protected_before={str(folder.relative_to(root)) or '.':protected_state(folder) for folder in [root,work]}
scratch=root/'.tmp';scratch.mkdir(exist_ok=True);index=scratch/'batch9-index';assert not index.exists()
env={**os.environ,'GIT_INDEX_FILE':str(index)}
def git(*args,input=None):
    payload=None if input is None else input.encode('utf-8')
    return subprocess.check_output(['git','-c','core.safecrlf=false',*args],cwd=root,env=env,input=payload).decode('utf-8').strip()
def stage(pairs):
    hashes=git('hash-object','-w','--stdin-paths',input=''.join(json.dumps(p.as_posix())+'\n' for _,p in pairs)).splitlines();assert len(hashes)==len(pairs)
    git('update-index','--index-info',input=''.join(f'100644 {h}\t{name}\n' for (name,_),h in zip(pairs,hashes)))
try:
    git('read-tree',baseline);stage([(name,work/name) for name in A]);tree_a=git('write-tree');git('diff','--check',baseline,tree_a)
    assert sorted(git('diff','--name-only',baseline,tree_a).splitlines())==sorted(A)
    commit_a=git('commit-tree',tree_a,'-p',baseline,input='feat(ui): finalize batch 9 Activities history\n')
    pairs=[(name,work/name) for name in B]
    report=root/'docs/ui/WOMBO_UI_V2_FINAL_VISUAL_BATCH_9_REPORT.md';pairs.append((report.relative_to(root).as_posix(),report))
    pairs.extend((p.relative_to(root).as_posix(),p) for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='commits.json' and not p.name.startswith('emulator-recovery'))
    stage(pairs);tree_b=git('write-tree');git('diff','--check',tree_a,tree_b);git('diff','--check',baseline,tree_b)
    assert sorted(git('diff','--name-only',tree_a,tree_b,'--','mobile').splitlines())==sorted(B)
    assert sorted(git('diff','--name-only',baseline,tree_b,'--','mobile').splitlines())==sorted(A+B)
    manifest=json.loads((HERE/'final-source-hashes.json').read_text())['sources'];names=sorted(n.replace('\\','/') for n in manifest)
    hashes=git('hash-object','--stdin-paths',input=''.join(json.dumps((work/n).as_posix())+'\n' for n in names)).splitlines()
    stored={record.split('\t')[1]:record.split(' ')[2].split('\t')[0] for record in git('ls-tree','-r','-z',tree_b,'--','mobile/app','mobile/src').split('\0') if record}
    assert stored==dict(zip(names,hashes)),'Review tree must match every runtime source'
    assert git('show',tree_b+':docs/ui/WOMBO_UI_V2_FINAL_VISUAL_BATCH_9_REPORT.md')==report.read_text(encoding='utf-8').strip()
    commit_b=git('commit-tree',tree_b,'-p',commit_a,input='feat(ui): finalize batch 9 activity entry and RPE\n')
    git('update-ref',ref,commit_b,'0'*40)
    protected_after={str(folder.relative_to(root)) or '.':protected_state(folder) for folder in [root,work]};assert protected_before==protected_after
    data={'branch':ref.removeprefix('refs/heads/'),'baseline':baseline,'commits':[{'phase':'A. Activities history','commit':commit_a,'sourceFiles':A},{'phase':'B. Activity entry and RPE','commit':commit_b,'sourceFiles':B}],'allRuntimeSourcesMatchReviewTree':len(names),'originalBranchAndIndexRetained':True,'protectedState':protected_after}
    (HERE/'commits.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps({k:v for k,v in data.items() if k!='protectedState'}))
finally:
    if index.exists():index.unlink()
