from pathlib import Path
import importlib.util,json
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('review',HERE/'native-review.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
cases=[(w,f,l,s) for w in [320,360,393,412] for f in [1,2] for l in ['nl','en'] for s in ['empty','history','entry','rpe']]
extras=['noHR','pending','blocked','selected','after','reminderWeek','reminderDestination','reminderFeedback','entryEmpty','context','planned','external','swimEntry','bikeRpe','swimRpe','busyRpe','busyCreate','entryError','rpeError','timezoneMissing','distanceOnly','partialCoverage','match','multiple','longHistory','longContext','rpeHR','rpeNoHR']
cases += [(393,1,'nl',s) for s in extras]
cases += [(320,2,'en',s) for s in ['selected','pending','multiple','longHistory','longContext','swimEntry','swimRpe','bikeRpe']]
cases += [(320,2,'nl','longHistory')]
ledger=json.loads((HERE/'case-ledger.json').read_text()) if (HERE/'case-ledger.json').exists() else []
for w,f,l,s in cases:
    case={'width':w,'fontScale':f,'language':l,'state':s}
    if case in ledger:continue
    print('Review '+str(case),flush=True);r.run_case(w,f,l,s)
    ledger.append(case);(HERE/'case-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
print('Completed',len(ledger),'native cases',flush=True)
