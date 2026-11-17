from pathlib import Path
import hashlib,json,os,subprocess
HERE=Path(__file__).resolve().parent
root=HERE.parents[3];work=root/'.worktrees/wombo-ui-v2-activities'
baseline=json.loads((HERE/'baseline.json').read_text())['baselineCommit']
verification=json.loads((HERE/'verification.json').read_text());assert verification['result']=='PASS'
ref='refs/heads/feat/wombo-ui-v2-final-batch-8'
assert subprocess.run(['git','show-ref','--verify','--quiet',ref],cwd=root).returncode==1
def protected_state(folder):
    def read_git(*args):
        return subprocess.check_output(['git',*args],cwd=folder,text=True).strip()
    index_path=Path(read_git('rev-parse','--git-path','index'))
    if not index_path.is_absolute():index_path=folder/index_path
    return {'branch':read_git('symbolic-ref','--short','HEAD'),'head':read_git('rev-parse','HEAD'),
        'indexHash':hashlib.sha256(index_path.read_bytes()).hexdigest(),
        'trackedStatus':read_git('status','--porcelain','--untracked-files=no')}
protected_before={str(folder.relative_to(root)) or '.':protected_state(folder) for folder in [root,work]}
scratch=root/'.tmp';scratch.mkdir(exist_ok=True)
index=scratch/'batch8-index';assert not index.exists()
env={**os.environ,'GIT_INDEX_FILE':str(index)}
def git(*args,input=None):
    # Binary stdin preserves Git's LF/NUL record separators on Windows.
    payload=None if input is None else input.encode('utf-8')
    return subprocess.check_output(['git','-c','core.safecrlf=false',*args],cwd=root,env=env,input=payload).decode('utf-8').strip()
try:
    git('read-tree',baseline)
    pairs=[(name.replace('\\','/'),work/name) for name in verification['changedSources']]
    report=root/'docs/ui/WOMBO_UI_V2_FINAL_VISUAL_BATCH_8_REPORT.md'
    pairs.append((report.relative_to(root).as_posix(),report))
    pairs.extend((p.relative_to(root).as_posix(),p) for p in sorted(HERE.rglob('*'))
      if p.is_file() and '__pycache__' not in p.parts and p.name!='commits.json')
    # Git quoted C-string paths, sent via stdin; no shell interpolation.
    hashes=git('hash-object','-w','--stdin-paths',input=''.join(json.dumps(p.as_posix())+'\n' for _,p in pairs)).splitlines()
    assert len(hashes)==len(pairs)
    git('update-index','--index-info',input=''.join(f'100644 {h}\t{name}\n' for (name,_),h in zip(pairs,hashes)))
    tree=git('write-tree')
    git('diff','--check',baseline,tree)
    changed=git('diff','--name-only',baseline,tree,'--','mobile').splitlines()
    assert sorted(changed)==sorted(name.replace('\\','/') for name in verification['changedSources'])
    assert git('ls-tree',tree,'--','docs/ui/WOMBO_UI_V2_FINAL_VISUAL_BATCH_8_REPORT.md')
    commit=git('commit-tree',tree,'-p',baseline,input='feat(ui): finalize batch 8 active workout movement\n')
    git('update-ref',ref,commit,'0'*40)
    protected_after={str(folder.relative_to(root)) or '.':protected_state(folder) for folder in [root,work]}
    assert protected_before==protected_after
    (HERE/'commits.json').write_text(json.dumps({'branch':ref.removeprefix('refs/heads/'),'baseline':baseline,'commit':commit,'sourceFiles':changed,'originalBranchAndIndexRetained':True,'protectedState':protected_after},indent=2)+'\n')
    print(commit)
finally:
    if index.exists():index.unlink()
