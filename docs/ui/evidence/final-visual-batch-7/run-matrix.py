from pathlib import Path
import importlib.util,json
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('review',HERE/'native-review.py')
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
cases=[(w,f,l,s) for w in [320,360,393,412] for f in [1,2] for l in ['nl','en'] for s in ['manual','review','alternatives']]
cases += [(393,1,'nl',s) for s in ['automatic','incomplete','multiple','sameDay','placementBusy','placementStale','activePending','reviewBusy','stale','selected','remove','noRemove','loading','retry','emptyAlternatives','staleAlternatives','distance','sparse','long','replacement','emptyReview']]
cases += [(320,2,'en',s) for s in ['incomplete','sameDay','stale','selected','remove','distance','long']]
ledger=json.loads((HERE/'case-ledger.json').read_text()) if (HERE/'case-ledger.json').exists() else []
for w,f,l,s in cases:
    case={'width':w,'fontScale':f,'language':l,'state':s}
    if case in ledger:continue
    print('Review '+str(case),flush=True)
    review.run_case(w,f,l,s)
    ledger.append(case);(HERE/'case-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
print('Completed '+str(len(ledger))+' native cases',flush=True)
