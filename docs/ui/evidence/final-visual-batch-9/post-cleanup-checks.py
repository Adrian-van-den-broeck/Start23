from pathlib import Path
import json,subprocess
HERE=Path(__file__).resolve().parent
mobile=HERE.parents[3]/'.worktrees/wombo-ui-v2-activities/mobile'
assert not (mobile/'app/dev-batch9-review.tsx').exists()
results={}
for key,args in [('typecheck',['npx.cmd','tsc','--noEmit']),('unused',['npx.cmd','tsc','--noEmit','--noUnusedLocals','--noUnusedParameters'])]:
    p=subprocess.run(args,cwd=mobile,capture_output=True,text=True,encoding='utf-8');results[key]=p.returncode
    (HERE/('post-cleanup-'+key+'.log')).write_text('\n'.join(line.rstrip() for line in (p.stdout+p.stderr).splitlines())+'\n',encoding='utf-8')
(HERE/'post-cleanup-checks.json').write_text(json.dumps(results,indent=2)+'\n');assert all(v==0 for v in results.values());print('Post-cleanup strict TypeScript/unused PASS')
