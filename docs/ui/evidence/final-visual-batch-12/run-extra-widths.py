from pathlib import Path
import importlib.util,json
spec=importlib.util.spec_from_file_location('review',str(Path(__file__).with_name('native-review.py')))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
completed={(x['state'],x['width'],x['fontScale']) for x in json.loads((r.HERE/'case-ledger.json').read_text())}
for state in ['entry','auth','sheet']:
 for width in [320,360,412]:
  if (state,width,1) not in completed:r.run_case(state,width,1)
print('Additional width review complete',flush=True)
