"""Review seven reference-state roles across widths, text sizes and NL/EN."""
from pathlib import Path
import json, subprocess, sys
here=Path(__file__).resolve().parent
cases=[]
for language in ['nl','en']:
    for width,font in [(393,1),(320,2)]:
        for state in ['run','bike','swim','distance']:
            cases.append((width,font,language,state))
    for width,font in [(320,1),(393,2)]:cases.append((width,font,language,'run'))
    cases.append((393 if language=='nl' else 320,1 if language=='nl' else 2,language,'candidate'))
ledger=[]
for width,font,language,state in cases:
    print(f'Review {width} dp / {font*100}% / {language} / {state}',flush=True)
    subprocess.run([sys.executable,str(here/'native-review.py'),'case',str(width),str(font),language,state],check=True)
    ledger.append({'width':width,'fontScale':font,'language':language,'state':state})
    (here/'case-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
print('Completed',len(ledger),'native cases.',flush=True)
