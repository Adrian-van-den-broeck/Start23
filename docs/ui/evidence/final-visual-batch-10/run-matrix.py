from pathlib import Path
import importlib.util
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('review',HERE/'native-review.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
cases=[]
for state in ['profile-editor','profile-blank','profile-filled','monitor','timezone','history','goal-triathlon','zones','review']:
    cases.extend([(state,393,1),(state,320,2)])
for state in ['goal-run','goal-bike','goal-swim','goal-duathlon']:
    cases.append((state,393,1))
for state in ['upgrade','resume','review-blocked']:
    cases.extend([(state,393,1),(state,320,2)])
for state in ['profile-editor-long','goal-triathlon-long','review-long']:
    cases.append((state,320,2))
for width in [320,360,412]:
    for state in ['profile-editor','goal-run']:cases.append((state,width,1))
for width in [360,393,412]:
    for state in ['profile-editor','goal-run']:cases.append((state,width,2))
cases.extend([('goal-choice',393,1),('review-pending',393,1),('review-pending',320,2),('goal-run-english',393,1),('goal-run-english',320,2)])
import json
done={(c['state'],c['width'],c['fontScale']) for c in json.loads((HERE/'case-ledger.json').read_text())}
for state,width,font in cases:
    if (state,width,font) not in done:r.run_case(state,width,font)
print('Native matrix complete: '+str(len(cases))+' cases',flush=True)
