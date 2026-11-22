import json, subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[3]
result=subprocess.run(['npm.cmd','audit','--omit=dev','--json'],cwd=root/'mobile',capture_output=True,text=True,timeout=60)
x=json.loads(result.stdout)
Path(__file__).with_name('npm-audit-clean.json').write_text(json.dumps(x,indent=2),encoding='utf-8')
Path(__file__).with_name('npm-audit-stderr.log').write_text(result.stderr,encoding='utf-8')
print('npm_exit_code',result.returncode,'metadata',x.get('metadata'))
for name,v in x.get('vulnerabilities',{}).items():
 if v['severity'] in ('critical','high'):
  print(name,v['severity'],'direct=',v['isDirect'],'range=',v['range'],'fix=',v['fixAvailable'])
  for via in v['via']:
   if isinstance(via,dict):print(via['title'],via['url'],via.get('range'))
