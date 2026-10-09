from pathlib import Path
import json,re,xml.etree.ElementTree as ET,hashlib
HERE=Path(__file__).resolve().parent
checks=[];failures=[];targets=[];cases=json.loads((HERE/'case-ledger.json').read_text())
def check(name,value):checks.append({'name':name,'pass':value});assert value,name
for case in { (x['state'],x['width'],x['fontScale']) for x in cases }:
    state,width,scale=case
    files=sorted(HERE.glob(f'{width}-font-{scale}-{state}-page-*.xml'))
    text=' '.join(n.get('text','')+' '+n.get('content-desc','') for p in files for n in ET.parse(p).iter('node'))
    check(f'{state} {width}/{scale} build marker',all('batch-10-build-final-7' in p.read_text() for p in files))
    check(f'{state} {width}/{scale} no development overlay','LogBox' not in text and 'configured linking' not in text)
    check(f'{state} {width}/{scale} private load absent',not re.search(r'\bTSS\b|private_load|planned_load|realized_load',text,re.I))
    if state.startswith('profile-editor'):
        check(f'{state} {width}/{scale} no onboarding progress',not re.search(r'Stap \d van',text))
        check(f'{state} {width}/{scale} destinations reachable',all(x in text for x in ['Pioneer toegang','Testen en kalibratie','Profiel opslaan']))
    else:
        step=1 if state in ['profile-blank','profile-filled'] else 2 if state in ['monitor','resume'] else 3 if state in ['timezone','upgrade'] else 4 if state=='history' else 5 if state.startswith('goal') else 6 if state=='zones' else 7
        check(f'{state} {width}/{scale} actual step of seven',f'Stap {step} van 7' in text)
    for p in files:
        t=ET.parse(p);meta=json.loads(p.with_suffix('.json').read_text());density=int(re.findall(r'-?\d+',meta['density'])[-1]);factor=density/160
        scrolls=[list(map(int,re.findall(r'-?\d+',n.get('bounds','')))) for n in t.iter('node') if n.get('class')=='android.widget.ScrollView' and n.get('scrollable')=='true']
        vp=max(scrolls,key=lambda b:b[3]-b[1]) if scrolls else [0,0,1080,2280]
        for n in t.iter('node'):
            if state=='zones' and n.get('content-desc') not in ['Afmelden','Testen']:continue
            if n.get('clickable')!='true' or n.get('class') in ['android.widget.ScrollView','android.widget.EditText'] or n.get('package')!='com.adrivdbs.wombo':continue
            b=list(map(int,re.findall(r'-?\d+',n.get('bounds',''))))
            # Native accessibility bounds are clipped at ScrollView edges; exclude those partial rectangles.
            if len(b)!=4 or b[2]<=b[0] or b[3]<=b[1] or b[1]<=vp[1]+1 or b[3]>=vp[3]-1:continue
            w=(b[2]-b[0])/factor;h=(b[3]-b[1])/factor
            facts={'file':p.name,'label':n.get('content-desc'),'widthDp':w,'heightDp':h}
            targets.append(facts)
            if w<47.5 or h<47.5:failures.append(facts)
(HERE/'native-target-audit.json').write_text(json.dumps({'scope':'Changed Batch 10 controls; unchanged ZoneSetupStep inner controls belong to Batch 11 and are excluded', 'minimumDp':48,'nativePixelToleranceDp':.5,'fullyVisibleControls':len(targets),'failures':failures,'targets':targets},indent=2)+'\n')
(HERE/'native-state-audit.json').write_text(json.dumps({'checks':checks,'caseCount':len(set((x['state'],x['width'],x['fontScale']) for x in cases))},indent=2)+'\n')
assert not failures,failures
print(len(checks),'native state checks;',len(targets),'fully visible controls PASS')
