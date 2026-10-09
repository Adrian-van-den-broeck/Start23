from pathlib import Path
import json,subprocess
HERE=Path(__file__).resolve().parent;MOBILE=HERE.parents[3]/'mobile';NODE='C:/Program Files/nodejs/node.exe'
commands={
'focused':[NODE,'node_modules/jest/bin/jest.js','--runInBand','--watch=false','src/screens/ProfileScreen.test.tsx','src/screens/OnboardingScreen.test.tsx','src/screens/OnboardingScreen.resume.test.tsx','src/components/DurationPicker.test.tsx','src/ui-v2/primitives/FinalPrimitives.test.tsx','--json','--outputFile='+str(HERE/'focused-tests.json')],
'typecheckFocused':[NODE,'node_modules/typescript/bin/tsc','--noEmit','--noUnusedLocals','--noUnusedParameters']}
result={}
for name,cmd in commands.items():
    with (HERE/(name+'.log')).open('w',encoding='utf-8') as log:p=subprocess.run(cmd,cwd=MOBILE,stdout=log,stderr=subprocess.STDOUT,timeout=120)
    result[name]=p.returncode;print(name,p.returncode,flush=True)
(HERE/'focused-command-checks.json').write_text(json.dumps(result,indent=2)+'\n');assert all(x==0 for x in result.values())
