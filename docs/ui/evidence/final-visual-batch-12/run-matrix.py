from pathlib import Path
import json,importlib.util
spec=importlib.util.spec_from_file_location('review',str(Path(__file__).with_name('native-review.py')))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
cases=[(state,w,f) for state in ['entry','questions','selected','candidate','saved','confirmed','error','auth','auth-register','auth-error','unlinked','connected','history','reconnect','pioneer','pioneer-error','sheet','profile','configuration','session-loading','advice'] for w,f in [(393,1),(320,2)]]
completed={(x['state'],x['width'],x['fontScale']) for x in json.loads((r.HERE/'case-ledger.json').read_text())} if (r.HERE/'case-ledger.json').exists() else set()
for state,width,font in cases:
 if (state,width,font) not in completed:r.run_case(state,width,font)
print('Matrix complete: '+str(len(cases))+' cases',flush=True)
