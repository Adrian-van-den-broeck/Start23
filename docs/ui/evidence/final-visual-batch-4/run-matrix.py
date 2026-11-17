"""All mapped states plus the width/font/locale matrix on the dual-state composition."""
from pathlib import Path
import json
from native_review_import import review
HERE = Path(__file__).resolve().parent
states = ['noPlan', 'selection', 'placement', 'pending', 'active', 'activePending', 'warning', 'rest', 'next', 'siblings']
cases = [(393, 1, 'nl', state) for state in states] + [(320, 2, 'en', state) for state in states]
for width in [320, 360, 393, 412]:
    for font in [1, 2]:
        for language in ['nl', 'en']:
            case = (width, font, language, 'activePending')
            if case not in cases: cases.append(case)
cases += [(393, 1, 'en', 'reminder'), (320, 2, 'nl', 'reminder'), (320, 2, 'nl', 'siblings'),
          (393, 1, 'en', 'sparse'), (320, 2, 'nl', 'sparse'), (393, 1, 'en', 'attention'),
          (393, 1, 'en', 'loading'), (393, 1, 'en', 'failed')]
ledger = json.loads((HERE/'case-ledger.json').read_text()) if (HERE/'case-ledger.json').exists() else []
for width, font, language, state in cases:
    case = {'width': width, 'fontScale': font, 'language': language, 'state': state}
    if case in ledger: continue
    print(f'Review {width}dp / {font*100}% / {language} / {state}', flush=True)
    review.run_case(width, font, language, state)
    ledger.append(case)
    (HERE/'case-ledger.json').write_text(json.dumps(ledger, indent=2)+'\n')
print('Completed', len(ledger), 'native cases.', flush=True)
