from pathlib import Path
import json,re,xml.etree.ElementTree as ET,hashlib
HERE=Path(__file__).resolve().parent
checks=[];failures=[];targets=[];cases=json.loads((HERE/'case-ledger.json').read_text())
def check(name,value):checks.append({'name':name,'pass':value});assert value,name
for case in { (x['state'],x['width'],x['fontScale']) for x in cases }:
    state,width,scale=case
    files=sorted(HERE.glob(f'{width}-font-{scale}-{state}-page-*.xml'))
    text=' '.join(n.get('text','')+' '+n.get('content-desc','') for p in files for n in ET.parse(p).iter('node'))
    check(f'{state} {width}/{scale} build marker',all(('batch-12-build-final-2' in p.read_text() or 'batch-12-build-final-3' in p.read_text() or 'batch-12-build-final-4' in p.read_text()) for p in files))
    check(f'{state} {width}/{scale} no development overlay','LogBox' not in text and 'configured linking' not in text)
    check(f'{state} {width}/{scale} private load absent',not re.search(r'\bTSS\b|private_load|planned_load|realized_load',text,re.I))
    labels={n.get('content-desc'):n.get('checked') for p in files for n in ET.parse(p).iter('node') if n.get('content-desc')}
    check(f'{state} {width}/{scale} no fabricated Check-in/Pioneer success',all(x not in text for x in ['Voorstel goedkeuren','Pioneer toegang actief','Check-in voltooid']))
    if state=='entry':check(f'{state} {width}/{scale} exact entry fields/action','Week start op maandag' in text and 'Start check-in' in text)
    if state in ['questions','selected','candidate','saved','advice']:
        check(f'{state} {width}/{scale} all restriction/sport/source fields survive',all(x in text for x in ['Zwemmen: Professioneel advies','Fietsen: Professioneel advies','Lopen: Professioneel advies','alarmsymptomen','Naam extra activiteit','Tijdstip (ISO inclusief tijdzone)','Geplande duur (minuten)','Inspannend','Terugkerend','Toevoegen','Context opslaan']))
        check(f'{state} {width}/{scale} no confirmed/completed presentation','Context bevestigd' not in text and 'Maak planvoorstel' not in text)
    if state=='selected':check(f'{state} {width}/{scale} selected drafts',all(labels.get(x)=='true' for x in ['Wo','Hoog','Vermoeidheid']))
    if state=='candidate':check(f'{state} {width}/{scale} temporary review actions',all(x in text for x in ['Controleer het invulvoorstel','Neem datums, vermoeidheid en redenen over','Negeer invulvoorstel','Mogelijke blessure genoemd voor:']))
    if state=='saved':check(f'{state} {width}/{scale} source/expiry and separate confirm','Bron: gestructureerd formulier' in text and 'Deze context bevestigen' in text and 'Clubtraining' in text)
    if state=='advice':check(f'{state} {width}/{scale} real professional advice field','Advies en herleidbare bron' in text)
    if state in ['confirmed','error']:
        check(f'{state} {width}/{scale} confirmed context only','Context bevestigd' in text and 'Maak planvoorstel' in text and 'Context opslaan' not in text)
    if state=='error':check(f'{state} {width}/{scale} documented rejection displayed','De wijziging kon niet veilig worden opgeslagen. Probeer opnieuw.' in text and '/plan-proposals' in text)
    if state.startswith('auth'):
        check(f'{state} {width}/{scale} real auth mode/fields',all(x in text for x in ['Aanmelden','Registreren','E-mailadres','Wachtwoord']))
        check(f'{state} {width}/{scale} secure password fields',any(n.get('password')=='true' for p in files for n in ET.parse(p).iter('node')))
    if state=='auth-register':check(f'{state} {width}/{scale} register confirmation field','Herhaal wachtwoord' in text and 'Account maken' in text)
    if state=='auth-error':check(f'{state} {width}/{scale} actual local validation','De wachtwoorden zijn niet gelijk.' in text)
    if state in ['unlinked','connected','history','reconnect']:
        check(f'{state} {width}/{scale} imports/privacy/destination',all(x in text for x in ['Polar','Imports','Privacy','Status vernieuwen','Geïmporteerde activiteiten bekijken']))
    if state=='unlinked':check(f'{state} {width}/{scale} unlinked empty','Niet gekoppeld' in text and 'Nog geen imports.' in text and 'Polar koppelen' in text)
    if state in ['connected','history']:check(f'{state} {width}/{scale} supported import selection',all(x in text for x in ['7 dagen','14 dagen','30 dagen','Import starten','Ontkoppelen']))
    if state=='history':check(f'{state} {width}/{scale} source-backed bounded retry','Nu opnieuw proberen' in text and 'geïmporteerd' in text and 'Webhook' in text)
    if state=='reconnect':check(f'{state} {width}/{scale} fresh consent required','Opnieuw koppelen' in text and 'Opnieuw toestemming geven' in text)
    if state.startswith('pioneer'):check(f'{state} {width}/{scale} code/destination survives',all(x in text for x in ['Profiel','Pioneer access-code','Code inwisselen']))
    if state=='pioneer-error':check(f'{state} {width}/{scale} public rejected-code error','De wijziging kon niet veilig worden opgeslagen. Probeer opnieuw.' in text)
    if state=='sheet':check(f'{state} {width}/{scale} existing sheet destinations/language/signout',all(x in text for x in ['Intakeprofiel','Integraties','Nederlands','English','Veilig afmelden']))
    if state=='profile':check(f'{state} {width}/{scale} existing profile destinations',all(x in text for x in ['Testen en kalibratie','Pioneer toegang']))
    if state=='configuration':check(f'{state} {width}/{scale} missing configuration remains explicit','Configuratie ontbreekt' in text and 'Configureer EXPO_PUBLIC_SUPABASE_URL en de publishable key.' in text)
    if state=='session-loading':check(f'{state} {width}/{scale} original loading destination','Wombo wordt klaargezet' in text)
    for p in files:
        t=ET.parse(p);meta=json.loads(p.with_suffix('.json').read_text());density=int(re.findall(r'-?\d+',meta['density'])[-1]);factor=density/160
        scrolls=[list(map(int,re.findall(r'-?\d+',n.get('bounds','')))) for n in t.iter('node') if n.get('class')=='android.widget.ScrollView' and n.get('scrollable')=='true']
        vp=max(scrolls,key=lambda b:b[3]-b[1]) if scrolls else [0,0,1080,2280]
        audit_nodes=list(t.iter('node'))
        if state=='sheet':
            modal_scroll=min((n for n in t.iter('node') if n.get('class')=='android.widget.ScrollView' and any(c.get('content-desc') in ['Intakeprofiel','Integraties','Automatisch','Nederlands','English','Veilig afmelden'] for c in n.iter('node'))),key=lambda n:len(list(n.iter('node'))))
            audit_nodes=list(modal_scroll.iter('node'));vp=list(map(int,re.findall(r'-?\d+',modal_scroll.get('bounds',''))))
        for n in audit_nodes:
            if n.get('clickable')!='true' or n.get('class') in ['android.widget.ScrollView','android.widget.EditText'] or n.get('package')!='com.adrivdbs.wombo':continue
            b=list(map(int,re.findall(r'-?\d+',n.get('bounds',''))))
            # Native accessibility bounds are clipped at ScrollView edges; exclude those partial rectangles.
            if len(b)!=4 or b[2]<=b[0] or b[3]<=b[1] or b[1]<=vp[1]+1 or b[3]>=vp[3]-1:continue
            w=(b[2]-b[0])/factor;h=(b[3]-b[1])/factor
            facts={'file':p.name,'label':n.get('content-desc'),'widthDp':w,'heightDp':h}
            targets.append(facts)
            if w<47.5 or h<47.5:failures.append(facts)
(HERE/'native-target-audit.json').write_text(json.dumps({'scope':'Batch 12 Check-in and current supporting controls; existing V1 week background excluded behind its profile modal', 'minimumDp':48,'nativePixelToleranceDp':.5,'fullyVisibleControls':len(targets),'failures':failures,'targets':targets},indent=2)+'\n')
(HERE/'native-state-audit.json').write_text(json.dumps({'checks':checks,'caseCount':len(set((x['state'],x['width'],x['fontScale']) for x in cases))},indent=2)+'\n')
assert not failures,failures
print(len(checks),'native state checks;',len(targets),'fully visible controls PASS')
