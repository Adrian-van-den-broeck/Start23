from pathlib import Path
import json,time
import importlib.util
spec=importlib.util.spec_from_file_location('review',str(Path(__file__).with_name('native-review.py')))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
cases=[]
for state in ['overview','pending','history','hidden','result','incomplete','feedback','onboarding']:
 for width,font in [(393,1),(320,2)]:cases.append((state,width,font))
for state in ['known','choice','empty']:
 for width in [320,360,393,412]:
  for font in [1,2]:cases.append((state,width,font))
for width in [360,412]:cases.append(('overview',width,1))
completed={(x['state'],x['width'],x['fontScale']) for x in json.loads((r.HERE/'case-ledger.json').read_text())} if (r.HERE/'case-ledger.json').exists() else set()
for state,width,font in cases:
 if (state,width,font) not in completed:r.run_case(state,width,font)
print('Matrix complete: '+str(len(cases))+' cases',flush=True)
