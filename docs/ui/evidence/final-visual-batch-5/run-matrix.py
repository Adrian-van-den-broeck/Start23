from pathlib import Path
import json
from native_review_import import review
HERE = Path(__file__).resolve().parent
cases = [(width, font, language, state) for width in [320,360,393,412] for font in [1,2] for language in ['nl','en'] for state in ['week','selected']]
cases += [(393,1,'nl',state) for state in ['empty','month','moveEntry','cancelReturn','afterMove','calendarAfterMove','long','sparse','loading','failed','retained']]
cases += [(320,2,'en',state) for state in ['empty','moveEntry','long','sparse']]
ledger = json.loads((HERE/'case-ledger.json').read_text(encoding='utf-8')) if (HERE/'case-ledger.json').exists() else []
for width,font,language,state in cases:
 case = {'width':width,'fontScale':font,'language':language,'state':state}
 if case in ledger: continue
 print(f'Review {width}dp / {font*100}% / {language} / {state}',flush=True)
 review.run_case(width,font,language,state)
 ledger.append(case)
 (HERE/'case-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
print('Completed',len(ledger),'native cases.',flush=True)
