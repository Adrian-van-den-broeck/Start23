"""One-off metadata inspection; fixed read-only calls, sanitized outputs only."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import io
import zipfile
from datetime import datetime, timezone
from urllib.parse import urlsplit

ROOT = Path('F:/Projecten Business/Start23/Code')
SOURCE = ROOT / '.worktrees/joren-v6-migration-blocker-resolution'
OUT = Path(__file__).parent
sys.path.insert(0, str(SOURCE / 'backend'))
import httpx
from scripts.verify_v6_hosted_auth import cli_management_token

RAILWAY = 'C:/Users/Adria/AppData/Local/npm-cache/_npx/79fa66f96c8fdacf/node_modules/.bin/railway.cmd'
EAS = 'C:/Users/Adria/AppData/Local/npm-cache/_npx/6bc7bae5c2059953/node_modules/.bin/eas.cmd'
PROJECT = 'c0cf7bc7-abe8-4db5-857a-85cc39850640'
os.environ['RAILWAY_CALLER'] = 'skill:use-railway@1.7.0'
os.environ['RAILWAY_AGENT_SESSION'] = 'wombo-v6-infra-20261117'

def cli(exe, args, cwd=SOURCE, stdin=None):
    result = subprocess.run([exe, *args], cwd=cwd, input=stdin, capture_output=True, text=True, encoding='utf-8')
    if result.returncode:
        raise RuntimeError('Read-only CLI failed: ' + args[0])
    return json.loads(result.stdout)

def write(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

SAFE = {'APP_ENV','ENVIRONMENT','SUPABASE_URL','SUPABASE_JWT_ISSUER','SUPABASE_JWT_AUDIENCE','SUPABASE_JWKS_URL','POLAR_RETRY_JOB_ENABLED','POLAR_RETRY_JOB_INTERVAL_SECONDS','POLAR_RETRY_JOB_BATCH_SIZE','REALIZED_V2_ENABLED','REALIZED_V2_PROCESSING_ENABLED','REALIZED_V2_RECONCILIATION_ENABLED','PORT','RAILWAY_GIT_COMMIT_SHA','RAILWAY_PUBLIC_DOMAIN','EXPO_PUBLIC_API_BASE_URL'}
SAFE.update('START23_'+name for name in ('ENVIRONMENT','API_V1_PREFIX','LOG_LEVEL','SUPABASE_URL','SUPABASE_JWT_AUDIENCE','REALIZED_V2_STORAGE_READY','REALIZED_V2_SELECTION_ENABLED','OPENAI_MODEL','POLAR_LEGAL_APPROVED','POLAR_PRIVACY_APPROVED','POLAR_PROVIDER_TERMS_APPROVED','POLAR_API_TIMEOUT_SECONDS','POLAR_MAX_ACTIVITY_FILE_BYTES','POLAR_OAUTH_REDIRECT_URL'))

def sanitize_vars(values):
    return {k: (v if k.upper() in SAFE else {'configured': v is not None and v != ''}) for k,v in sorted(values.items())}

def railway():
    record = {'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'mutations': 0, 'project_id': PROJECT, 'environments': []}
    for env in ('production', 'r6-staging'):
        status = cli(RAILWAY, ['status','--project',PROJECT,'--environment',env,'--json'])
        for edge in status['environments']['edges']:
            node = edge['node']
            target = {'id':node['id'], 'name':node['name'], 'services':[]}
            for service_edge in node['serviceInstances']['edges']:
                service = service_edge['node']
                item = {k:service.get(k) for k in ('serviceId','serviceName','cronSchedule','nextCronRunAt','domains','source','startCommand','tracingEnabled','autoInstrumentationEnabled')}
                variables = cli(RAILWAY, ['variables','--project',PROJECT,'--environment',node['id'],'--service',service['serviceId'],'--json'])
                item['configured_variables'] = sanitize_vars(variables)
                item['active_deployments'] = []
                for deployment in service['activeDeployments']:
                    meta = deployment.get('meta') or {}
                    deployed = {k:deployment.get(k) for k in ('id','status','createdAt','deploymentStopped','instances')}
                    deployed['meta'] = {k:meta.get(k) for k in ('commitHash','branch','repo','rootDirectory','imageDigest','runtime','configFile','serviceManifest')}
                    snapshot = cli(RAILWAY, ['api'], stdin='query { deploymentSnapshot(deploymentId: "'+deployment['id']+'") { id variablesRedacted variables } }')
                    snap = snapshot.get('data',{}).get('deploymentSnapshot')
                    deployed['snapshot'] = None if snap is None else {'id':snap['id'],'variablesRedacted':snap['variablesRedacted'],'variables':sanitize_vars(snap['variables'])}
                    item['active_deployments'].append(deployed)
                target['services'].append(item)
            record['environments'].append(target)
    write('railway-current.json', record)
    print('Saved sanitized Railway active artifact and settings metadata.')

def account():
    result = {'observed_at_utc':datetime.now(timezone.utc).isoformat(),'mutations':0}
    with httpx.Client(base_url='https://api.supabase.com',headers={'Authorization':'Bearer '+cli_management_token()},timeout=30) as client:
        for key,path in [('organizations','/v1/organizations'),('projects','/v1/projects')]:
            response = client.get(path)
            result[key+'_status'] = response.status_code
            if response.is_success:
                result[key] = [{k:row.get(k) for k in ('id','ref','name','organization_id','slug','status','region','plan')} for row in response.json()]
        result['organization_plans'] = []
        for org in result.get('organizations',[]):
            response=client.get('/v1/organizations/'+org['id'])
            result['organization_plans'].append({'id':org['id'],'http_status':response.status_code,'plan':response.json().get('plan') if response.is_success else None})
    write('account-capacity-current.json',result)
    print('Saved visible account-wide organization and project capacity metadata.')

def mobile():
    result = {'observed_at_utc':datetime.now(timezone.utc).isoformat(),'mutations':0,'platforms':{}}
    for platform in ('android','ios'):
        builds = cli(EAS,['build:list','--platform',platform,'--limit','10','--json','--non-interactive'],SOURCE/'mobile')
        result['platforms'][platform] = [{k:b.get(k) for k in ('id','platform','status','distribution','buildProfile','appVersion','appBuildVersion','gitCommitHash','createdAt','completedAt','channel','runtimeVersion')} for b in builds]
    write('eas-current.json', result)
    print('Saved sanitized EAS build metadata; no release claim.')

def public():
    result = {'observed_at_utc':datetime.now(timezone.utc).isoformat(),'endpoints':{}}
    with httpx.Client(timeout=30,follow_redirects=False) as client:
        for base in ('https://start23-production.up.railway.app','https://r6-api-r6-staging.up.railway.app'):
            item={}
            for route in ('/health','/ready','/openapi.json'):
                response=client.get(base+route)
                value={'http_status':response.status_code}
                if response.is_success:
                    body=response.json()
                    if route=='/openapi.json':
                        value.update({'path_count':len(body['paths']),'sha256':hashlib.sha256(response.content).hexdigest(),'paths':sorted(body['paths'])})
                    else:
                        value['body']=body
                item[route]=value
            result['endpoints'][base]=item
    write('public-endpoints-current.json',result)
    print('Saved public health and contract metadata.')

def binaries():
    result={'observed_at_utc':datetime.now(timezone.utc).isoformat(),'binaries':[],'installed_device_count':0}
    def examine(label, archive, identity):
        digest=hashlib.sha256(archive).hexdigest()
        entry={'label':label,'artifact_sha256':digest,'bytes':len(archive),'identity':identity,'bundles':[]}
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            for name in z.namelist():
                if name.endswith(('index.android.bundle','index.ios.bundle','app.manifest','expo-updates.json')):
                    body=z.read(name)
                    hosts=[h for h in ('start23-production.up.railway.app','r6-api-r6-staging.up.railway.app','isfumhgqphieoayqahjv.supabase.co','127.0.0.1:8000','localhost:8000','10.0.2.2:8000') if h.encode() in body]
                    entry['bundles'].append({'entry':name,'sha256':hashlib.sha256(body).hexdigest(),'recognized_hosts':hosts})
        result['binaries'].append(entry)
    builds=cli(EAS,['build:list','--platform','android','--limit','1','--status','finished','--json','--non-interactive'],SOURCE/'mobile')
    b=builds[0]
    url=b.get('artifacts',{}).get('buildUrl') or b.get('artifacts',{}).get('applicationArchiveUrl')
    if url:
        with httpx.Client(timeout=60,follow_redirects=True) as client:
            response=client.get(url)
            if not response.is_success:
                result['eas_artifact_fetch']={'http_status':response.status_code,'artifact_id':b['id'],'compiled_endpoint_verified':False}
            elif len(response.content)>250_000_000:
                raise RuntimeError('Artifact exceeds intended in-memory scope')
            else:
                examine('EAS latest finished Android',response.content,{k:b.get(k) for k in ('id','appVersion','appBuildVersion','gitCommitHash')})
    for variant in ('release','debug'):
        path=ROOT/f'mobile/android/app/build/outputs/apk/{variant}/app-{variant}.apk'
        if path.exists():
            examine('Local '+variant+' APK',path.read_bytes(),{'path':str(path),'installed_or_released':False})
    write('mobile-binaries-current.json',result)
    print('Inspected mobile binaries in memory; wrote hashes/known endpoints only, no artifact downloaded to disk.')

if __name__=='__main__':
    {'railway':railway,'account':account,'mobile':mobile,'public':public,'binaries':binaries}[sys.argv[1]]()
