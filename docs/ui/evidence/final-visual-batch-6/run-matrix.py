from pathlib import Path
import json
from native_review_import import review
HERE = Path(__file__).resolve().parent
cases = [(w,f,l,s) for w in [320,360,393,412] for f in [1,2] for l in ['nl','en'] for s in ['availability','selection']]
cases += [(393,1,'nl',s) for s in ['none','oneDay','reuse','restrictions','availabilityBusy','incomplete','loading','unavailable','exhausted','stale','busy','skipped','accepted','repeated','placement','warning','distance','sparse','long','rpe']]
cases += [(320,2,'en',s) for s in ['restrictions','repeated','long','distance','stale']]
ledger=json.loads((HERE/'case-ledger.json').read_text()) if (HERE/'case-ledger.json').exists() else []
for w,f,l,s in cases:
 case={'width':w,'fontScale':f,'language':l,'state':s}
 if case in ledger: continue
 print(f'Review {w}dp / {f*100}% / {l} / {s}',flush=True)
 review.run_case(w,f,l,s)
 ledger.append(case)
 (HERE/'case-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
print('Completed',len(ledger),'native cases.',flush=True)
