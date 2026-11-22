import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
observations=[]
for base in ('https://start23-production.up.railway.app','https://r6-api-r6-staging.up.railway.app'):
 for path in ('/ready','/openapi.json'):
  row={'base':base,'path':path,'observed_at':datetime.now(timezone.utc).isoformat()}
  try:
   with urllib.request.urlopen(base+path, timeout=15) as response:
    body=json.load(response); row['status']=response.status
    if path=='/ready': row['body']=body
    else:
     row['info']=body.get('info'); row['paths']=sorted(body.get('paths',{}))
     serialized=json.dumps(body)
     if len(serialized)<2*1024*1024:
      filename='production-openapi.json' if 'start23-production' in base else 'staging-openapi.json'
      Path(__file__).with_name(filename).write_text(serialized,encoding='utf-8')
  except urllib.error.HTTPError as error: row['status']=error.code
  except Exception as error: row['error']=type(error).__name__+': '+str(error)[:180]
  observations.append(row)
target=Path(__file__).with_name('public-health.json')
target.write_text(json.dumps(observations,indent=2),encoding='utf-8')
for row in observations: print({key:value if key!='paths' else len(value) for key,value in row.items()})
