from pathlib import Path
import importlib.util,json
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('review',HERE/'native-review.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
ledger=json.loads((HERE/'case-ledger.json').read_text()) if (HERE/'case-ledger.json').exists() else []
for width,state in [(393,'history'),(360,'history'),(320,'history'),(412,'history'),(320,'rpe')]:
    case={'width':width,'fontScale':1,'language':'nl','state':state}
    if case in ledger:continue
    r.run_case(width,1,'nl',state);ledger.append(case);(HERE/'case-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
print('Canonical/four-width heading preflight complete')
