from pathlib import Path
import json,re,xml.etree.ElementTree as ET,hashlib
HERE=Path(__file__).resolve().parent
checks=[];failures=[];targets=[];cases=json.loads((HERE/'case-ledger.json').read_text())
def check(name,value):checks.append({'name':name,'pass':value});assert value,name
for case in { (x['state'],x['width'],x['fontScale']) for x in cases }:
    state,width,scale=case
    files=sorted(HERE.glob(f'{width}-font-{scale}-{state}-page-*.xml'))
    text=' '.join(n.get('text','')+' '+n.get('content-desc','') for p in files for n in ET.parse(p).iter('node'))
    check(f'{state} {width}/{scale} build marker',all(('batch-11-build-final-5' in p.read_text() or 'batch-11-build-final-6' in p.read_text()) for p in files))
    check(f'{state} {width}/{scale} no development overlay','LogBox' not in text and 'configured linking' not in text)
    check(f'{state} {width}/{scale} private load absent',not re.search(r'\bTSS\b|private_load|planned_load|realized_load',text,re.I))
    if state in ['overview','pending','history','hidden']:
        check(f'{state} {width}/{scale} discipline controls reachable',text.count('Waarden of route wijzigen')>=3)
        check(f'{state} {width}/{scale} actual discipline count','Disciplines' in text and 'Plan gekoppeld' in text)
    if state=='pending':
        check(f'{state} {width}/{scale} active and pending separate',all(x in text for x in ['Actief profiel','Nieuw voorstel','Zones goedkeuren','Afwijzen']))
    if state=='history':check(f'{state} {width}/{scale} superseded retained','superseded' in text and 'Eerdere waarden' in text)
    if state=='hidden':check(f'{state} {width}/{scale} numeric values absent',not re.search(r'172 bpm|146 bpm|155 bpm|163 bpm|177 bpm|Z[1-5]',text))
    if state=='known':check(f'{state} {width}/{scale} known fields and save reachable',all(x in text for x in ['LTHR','Drempeltempo','min/km','bpm','Bekende waarden bewaren','Ik ken ook vijf zonegrenzen']))
    if state=='choice':check(f'{state} {width}/{scale} only current routes','Maximale veldtest' not in text and 'Week-1-kalibratie kiezen' in text)
    if state=='empty':check(f'{state} {width}/{scale} no execution or false success','Geen protocol gekozen' in text and 'Opslaan en deterministisch evalueren' not in text and 'Zones bevestigen' not in text)
    if state=='feedback':check(f'{state} {width}/{scale} explicit observation submit',all(x in text for x in ['Opslaan en deterministisch evalueren','Hoe voelde de volledige sessie?','Hoe voelde dit blok?','Gemiddelde hartslag','Voltooid','Onderbroken']))
    if state=='result':check(f'{state} {width}/{scale} threshold decision only','Drempel bevestigen' in text and 'Drempel afwijzen' in text and 'Zones bevestigen' not in text)
    if state=='incomplete':check(f'{state} {width}/{scale} incomplete never confirms','Meer of betere gegevens nodig' in text and 'Drempel bevestigen' not in text)
    if state=='boundaries':check(f'{state} {width}/{scale} five explicit overrides and both fields',all(x in text for x in ['Z1','Z2','Z3','Z4','Z5','Onder','Boven','Bekende waarden bewaren']))
    if state.startswith('protocol-'):
        check(f'{state} {width}/{scale} actual source protocol and observation form',all(x in text for x in ['start23_week1_','Beoordeeld v1','Opslaan en deterministisch evalueren','Voltooid','Onderbroken']))
        check(f'{state} {width}/{scale} no manufactured result','Drempel bevestigen' not in text and 'Zones bevestigen' not in text)
        if state=='protocol-swim':check(f'{state} {width}/{scale} swim source repetition fields',all(x in text for x in ['25 m-bad','Gemeten totale tijd van dit blok','Vier herhalingstijden','Vier rusttijden']))
        else:check(f'{state} {width}/{scale} approved optional block retained','Optioneel blok uitgevoerd' in text and 'Gemiddelde hartslag' in text)
    if state=='onboarding':check(f'{state} {width}/{scale} distinct pending confirmation','Zones run bevestigen' in text and 'Zonevoorstel run afwijzen' in text)
    for p in files:
        t=ET.parse(p);meta=json.loads(p.with_suffix('.json').read_text());density=int(re.findall(r'-?\d+',meta['density'])[-1]);factor=density/160
        scrolls=[list(map(int,re.findall(r'-?\d+',n.get('bounds','')))) for n in t.iter('node') if n.get('class')=='android.widget.ScrollView' and n.get('scrollable')=='true']
        vp=max(scrolls,key=lambda b:b[3]-b[1]) if scrolls else [0,0,1080,2280]
        for n in t.iter('node'):
            if n.get('clickable')!='true' or n.get('class') in ['android.widget.ScrollView','android.widget.EditText'] or n.get('package')!='com.adrivdbs.wombo':continue
            b=list(map(int,re.findall(r'-?\d+',n.get('bounds',''))))
            # Native accessibility bounds are clipped at ScrollView edges; exclude those partial rectangles.
            if len(b)!=4 or b[2]<=b[0] or b[3]<=b[1] or b[1]<=vp[1]+1 or b[3]>=vp[3]-1:continue
            w=(b[2]-b[0])/factor;h=(b[3]-b[1])/factor
            facts={'file':p.name,'label':n.get('content-desc'),'widthDp':w,'heightDp':h}
            targets.append(facts)
            if w<47.5 or h<47.5:failures.append(facts)
(HERE/'native-target-audit.json').write_text(json.dumps({'scope':'Batch 11 Zones/calibration controls and shared header', 'minimumDp':48,'nativePixelToleranceDp':.5,'fullyVisibleControls':len(targets),'failures':failures,'targets':targets},indent=2)+'\n')
(HERE/'native-state-audit.json').write_text(json.dumps({'checks':checks,'caseCount':len(set((x['state'],x['width'],x['fontScale']) for x in cases))},indent=2)+'\n')
assert not failures,failures
print(len(checks),'native state checks;',len(targets),'fully visible controls PASS')
