from pathlib import Path
import json,subprocess
HERE=Path(__file__).resolve().parent
MOBILE=HERE.parents[3]/'mobile'
NODE='C:/Program Files/nodejs/node.exe'
commands={
 'fullJest':[NODE,'node_modules/jest/bin/jest.js','--runInBand','--watch=false','--setupFilesAfterEnv','./jest.setup.ts',str(HERE/'deterministic-proposal-fixture-date.cjs'),'--json','--outputFile='+str(HERE/'full-mobile-tests.json')],
 'typecheck':[NODE,'node_modules/typescript/bin/tsc','--noEmit','--noUnusedLocals','--noUnusedParameters'],
}
results={}
for name,cmd in commands.items():
    with (HERE/(name+'.log')).open('w',encoding='utf-8') as log:
        p=subprocess.run(cmd,cwd=MOBILE,stdout=log,stderr=subprocess.STDOUT,timeout=600)
    results[name]=p.returncode; print(name,p.returncode,flush=True)
(HERE/'command-checks.json').write_text(json.dumps(results,indent=2)+'\n')
assert all(v==0 for v in results.values())
