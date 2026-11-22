import json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[3]
p=subprocess.run(['node',r'C:/Users/Adria/AppData/Local/npm-cache/_npx/fa34aabbbbeefe22/node_modules/eas-cli/bin/run','build:list','--platform','android','--limit','3','--json','--non-interactive'],cwd=root/'mobile',capture_output=True,text=True,timeout=50)
result={'exit_code':p.returncode}
if p.returncode:
 result['error']=p.stderr[-1000:]
else:
 data=json.loads(p.stdout)
 allowed=['id','status','platform','buildProfile','distribution','gitCommitHash','gitCommitMessage','appVersion','appBuildVersion','sdkVersion','runtimeVersion','channel','createdAt','updatedAt','applicationIdentifier','appIdentifier']
 result['builds']=[{key:item.get(key) for key in allowed if key in item} for item in data]
Path(__file__).with_name('eas-build-metadata.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
