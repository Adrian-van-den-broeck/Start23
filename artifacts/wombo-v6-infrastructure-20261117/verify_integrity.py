"""Offline source, bundle, and refreshed read-only boundary comparison."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path('F:/Projecten Business/Start23/Code')
SOURCE = ROOT / '.worktrees/joren-v6-migration-blocker-resolution'
OUT = Path(__file__).parent
EVIDENCE = SOURCE/'docs/catalog/implementation/blocker-resolution-20261117'
BASE = SOURCE/'docs/catalog/implementation/migration-readiness-20261116'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

result={'candidate_sha':'1730a3f62deea3acee5267fa20d2f4ce135a6362','deployed_sha':'aff74558d0a6511286a4a84a44ea25a03ca57549','checks':{}}
manifest=read(OUT/'review-bundles/manifest.json')
result['checks']['review_manifest_exact']=manifest==read(EVIDENCE/'owner-bundle-manifest.json')
result['groups']=[]
for group in manifest['groups']:
    digest=hashlib.sha256((OUT/'review-bundles'/group['file']).read_bytes()).hexdigest()
    result['checks']['group_'+str(group['group'])+'_hash']=digest==group['sha256']
    result['groups'].append({k:group[k] for k in ('group','file','sha256','migrations')})
files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (SOURCE/'supabase/migrations').glob('*.sql')}
original=read(BASE/'hosted-before.json')['migration_comparison']['accepted_sha256']
corrections=read(EVIDENCE/'forward-migrations.json')
result['checks']['original_63_bytes_unchanged']=all(files.get(k)==v for k,v in original.items()) and len(original)==63
result['checks']['exact_65_files']=files==original|corrections and len(files)==65
fresh=read(OUT/'hosted-baseline-current.json')
previous=read(BASE/'hosted-detail-final.json')
for key in ('function_fingerprints','effective_execution','effective_table_privileges','default_privileges'):
    result['checks']['hosted_'+key+'_unchanged']=fresh['metadata'][key]==previous['metadata'][key]
preflight=read(OUT/'hosted-preflight-current.json')
result['checks']['hosted_47_versions_unchanged']=preflight['metadata']['migrations']==read(BASE/'hosted-before.json')['metadata']['migrations']
result['activity_consumer_source_hashes']={}
for name in ('schemas','service'):
    path='backend/app/modules/activities/'+name+'.py'
    hashes={sha:hashlib.sha256(subprocess.check_output(['git','show',sha+':'+path],cwd=SOURCE)).hexdigest() for sha in ('5d71c688deb610bf5ec79c0f6fac77c835be6b51',result['deployed_sha'])}
    result['activity_consumer_source_hashes'][path]=hashes
    result['checks']['deployed_'+name+'_equals_tested_consumer']=len(set(hashes.values()))==1
result['compatibility_limit']='C1 activity projection consumer byte identity only; complete deployed historical workflow and mobile compatibility still requires isolated hosted verification.'
result['checks']['release_worktree_clean']=not subprocess.check_output(['git','status','--porcelain'],cwd=SOURCE).strip()
(OUT/'integrity-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
if not all(result['checks'].values()):
    raise SystemExit('Integrity comparison failed; inspect sanitized JSON.')
print('PASS: all '+str(len(result['checks']))+' source/bundle/boundary comparisons; no test-suite rerun or hosted writes.')
