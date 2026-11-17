from pathlib import Path
import datetime,json,re,subprocess,time,os,xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
ADB='C:/Users/Adria/AppData/Local/Android/Sdk/platform-tools/adb.exe'
SERIAL=os.environ.get('BATCH12_ANDROID_SERIAL','emulator-5556')
def adb(*args):
    return subprocess.check_output([ADB,'-s',SERIAL,*args],text=True,encoding='utf-8',timeout=25).strip()
def tree():
    for attempt in range(3):
        try:
            adb('shell','uiautomator','dump','/sdcard/batch12.xml')
            return ET.fromstring(adb('shell','cat','/sdcard/batch12.xml'))
        except (subprocess.CalledProcessError,subprocess.TimeoutExpired,ET.ParseError):
            if attempt==2:raise
            time.sleep(.5)
def bounds(n):return list(map(int,re.findall(r'-?\d+',n.get('bounds',''))))
def valid(t,state):
    ids={n.get('resource-id') for n in t.iter('node')}
    assert 'batch-12-fixture-'+state in ids and ('batch-12-build-final-2' in ids or 'batch-12-build-final-3' in ids or 'batch-12-build-final-4' in ids),'Wrong fixture/build'
    assert not any('LogBox' in str(n.attrib) or 'configured linking in multiple places' in str(n.attrib) for n in t.iter('node')),'Development overlay'
def capture(name,t=None,state=None,modal_open=True):
    t=t if t is not None else tree()
    config=json.loads((HERE/'fixture-config.json').read_text());valid(t,state or config['state'])
    if (state or config['state'])=='sheet':
        is_open=any(n.get('content-desc')=='Bottom sheet backdrop' for n in t.iter('node'))
        assert is_open==modal_open,'Unexpected modal visibility'
    ET.ElementTree(t).write(HERE/(name+'.xml'),encoding='utf-8')
    data=subprocess.check_output([ADB,'-s',SERIAL,'exec-out','screencap','-p'],timeout=25)
    (HERE/(name+'.png')).write_bytes(data)
    (HERE/(name+'.json')).write_text(json.dumps({'timestampUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'fixture':config,'size':adb('shell','wm','size'),'density':adb('shell','wm','density'),'fontScale':adb('shell','settings','get','system','font_scale'),'provenance':'Production CheckIn/Auth/Integrations/Pioneer/Profile and existing Planning modal; typed inert public DTOs; transport blocked; no completed Check-in fixture; callbacks prove UI dispatch only'},indent=2)+'\n')
def scroll(t,reverse=False):
    scrolls=[bounds(n) for n in t.iter('node') if n.get('class')=='android.widget.ScrollView' and n.get('scrollable')=='true']
    if not scrolls:return False
    b=max(scrolls,key=lambda b:b[3]-b[1]);x=b[0]+80 if json.loads((HERE/'fixture-config.json').read_text())['state']=='sheet' else b[0]+12
    adb('shell','input','swipe',str(x),str(round(b[1]+(b[3]-b[1])*(.25 if reverse else .82))),str(x),str(round(b[1]+(b[3]-b[1])*(.82 if reverse else .25))),'300');time.sleep(.3);return True
def open_case(state,width=393,font=1):
    # Density/font changes can recreate the activity. Boot one settled gallery root per case.
    adb('shell','am','force-stop','com.adrivdbs.wombo')
    density=439 if width==393 else round(1080*160/width)
    adb('shell','wm','density',str(density));adb('shell','settings','put','system','font_scale',str(font));time.sleep(.7)
    (HERE/'fixture-config.json').write_text(json.dumps({'state':state,'width':width,'fontScale':font,'build':'final-4','language':'source Dutch','inertActions':True})+'\n')
    (HERE.parents[3]/'mobile/public/batch12-fixture.json').write_text(json.dumps({'state':state,'nonce':str(time.time_ns())}))
    adb('shell','am','start','-a','android.intent.action.VIEW','-d','wombo://expo-development-client/?url=http%3A%2F%2F127.0.0.1%3A8085','com.adrivdbs.wombo')
    time.sleep(8)
    expected={'entry':'Start check-in','questions':'Start check-in','selected':'Start check-in','saved':'Start check-in','confirmed':'Start check-in','error':'Start check-in','candidate':'Start check-in','auth':'Aanmelden','auth-register':'Aanmelden','auth-error':'Aanmelden','pioneer':'Code inwisselen','pioneer-error':'Code inwisselen','unlinked':'Polar','connected':'Polar','history':'Polar','reconnect':'Polar','sheet':'Profielmenu','profile':'Mijn profiel','configuration':'Configuratie ontbreekt','session-loading':'Wombo wordt klaargezet','advice':'Start check-in'}.get(state,'WOMBO')
    for _ in range(30):
        time.sleep(.5)
        t=tree();ids={n.get('resource-id') for n in t.iter('node')}
        if 'batch-12-fixture-'+state in ids and any(expected in (n.get('text','')+' '+n.get('content-desc','')) for n in t.iter('node')):
            valid(t,state)
            if state in ['questions','selected','saved','confirmed','error','candidate','advice']:tap('Start check-in')
            if state=='advice':tap('Lopen: Professioneel advies')
            if state=='selected':tap('Wo');tap('Hoog');tap('Vermoeidheid')
            if state=='candidate':
                fill('Vertel kort wat er deze week speelt (optioneel)','Woensdag niet beschikbaar');tap('Maak invulvoorstel')
            if state=='error':tap('Maak planvoorstel')
            if state in ['auth-register','auth-error']:
                tap('Registreren')
                if state=='auth-error':
                    fill('E-mailadres','review@example.test');fill('Wachtwoord','long-enough');fill('Herhaal wachtwoord','different');tap('Account maken')
            if state=='pioneer-error':fill('Pioneer access-code','EXPIRED1');tap('Code inwisselen')
            if state=='sheet':tap('Profielmenu')
            if state!='sheet':top()
            return
        if 'batch-12-fixture-'+state in ids:scroll(t)
    raise AssertionError('Fixture did not load: '+state)
def pages(prefix):
    seen=set()
    for part in range(60):
        t=tree();signature=tuple((n.get('text'),n.get('content-desc'),n.get('bounds')) for n in t.iter('node'))
        if signature in seen:return part
        seen.add(signature);capture(prefix+'-page-'+str(part),t)
        if json.loads((HERE/'fixture-config.json').read_text())['state']=='sheet':
            modal=next(n for n in t.iter('node') if n.get('class')=='android.widget.ScrollView' and any(c.get('content-desc') in ['Intakeprofiel','Integraties','Automatisch','Nederlands','English','Veilig afmelden'] for c in n.iter('node')))
            vp=bounds(modal)
            if any(n.get('content-desc')=='Veilig afmelden' and bounds(n)[1]>vp[1]+1 and bounds(n)[3]<vp[3]-1 for n in modal.iter('node')):return part+1
        if not scroll(t):return part+1
    raise AssertionError('Scroll did not settle')
def run_case(state,width=393,font=1):
    open_case(state,width,font);prefix=str(width)+'-font-'+str(font)+'-'+state
    for old in HERE.glob(prefix+'-page-*'):old.unlink()
    count=pages(prefix);ledger=json.loads((HERE/'case-ledger.json').read_text()) if (HERE/'case-ledger.json').exists() else []
    ledger=[x for x in ledger if (x['state'],x['width'],x['fontScale'])!=(state,width,font)]
    ledger.append({'state':state,'width':width,'fontScale':font,'pages':count});(HERE/'case-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
    print(prefix+': '+str(count)+' viewports',flush=True)
def target(label,enabled=True):
    for _ in range(60):
        t=tree();config=json.loads((HERE/'fixture-config.json').read_text());valid(t,config['state'])
        sc=[bounds(n) for n in t.iter('node') if n.get('class')=='android.widget.ScrollView' and n.get('scrollable')=='true']
        vp=max(sc,key=lambda b:b[3]-b[1]) if sc else [0,0,1080,2280]
        partial=None
        for n in t.iter('node'):
            if n.get('content-desc','').removesuffix(', busy')!=label or n.get('clickable')!='true':continue
            b=bounds(n)
            # Hierarchy rectangles touching a scroll edge may be clipped, including by the IME.
            fixed_profile_header = label=='Profielmenu' and b[1]>=0 and b[3]<vp[1] and b[3]>b[1]
            if fixed_profile_header or (b[1]>vp[1]+1 and b[3]<vp[3]-1 and b[3]-b[1]>=48):
                assert n.get('enabled')==str(enabled).lower(),label
                return n,b
            # Described radio rows can exceed a 200% viewport. Select through the fully visible label,
            # retaining a >=48 dp visible touch region, rather than shrinking or hiding the source hint.
            labels=[child for child in n.iter('node') if child.get('text')==label]
            factor=1080/config['width']
            if n.get('class')=='android.widget.RadioButton' and labels and b[3]-b[1]>=48*factor:
                lb=bounds(labels[0])
                if lb[1]>vp[1]+1 and lb[3]<vp[3]-1:
                    facts={'label':label,'fixture':config,'visibleControlBounds':b,'fullyVisibleLabelBounds':lb,'minimumVisibleDp':48}
                    log=HERE/'native-long-row-selection.json'
                    records=json.loads(log.read_text()) if log.exists() else []
                    records.append(facts);log.write_text(json.dumps(records,indent=2)+'\n')
                    return n,lb
            if b[2]>b[0] and b[3]>b[1]:partial=b
        if partial is not None:
            # Small gutter scrolls align long source-description rows without overshooting.
            reverse=partial[1]<=vp[1]+1
            y=round(vp[1]+(vp[3]-vp[1])*.5);delta=round((vp[3]-vp[1])*.10)
            adb('shell','input','swipe',str(vp[0]+12),str(y),str(vp[0]+12),str(y+(delta if reverse else -delta)),'300');time.sleep(.3)
        elif not scroll(t):break
    raise AssertionError('Missing complete target '+label)
def tap(label,enabled=True):
    _,b=target(label,enabled);adb('shell','input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2));time.sleep(.6)

def top():
    seen=set()
    for _ in range(80):
        t=tree();signature=ET.tostring(t)
        if signature in seen:break
        seen.add(signature)
        if not scroll(t,True):break

def fill(label,value):
    for _ in range(80):
        t=tree()
        sc=[bounds(n) for n in t.iter('node') if n.get('class')=='android.widget.ScrollView' and n.get('scrollable')=='true']
        vp=max(sc,key=lambda b:b[3]-b[1]) if sc else [0,0,1080,2280]
        partial=None
        for n in t.iter('node'):
            if n.get('class')!='android.widget.EditText' or n.get('content-desc')!=label:continue
            b=bounds(n)
            if b[2]>b[0] and b[3]>b[1] and b[1]>vp[1]+1 and b[3]<vp[3]-1:
                adb('shell','input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2));time.sleep(.5)
                adb('shell','input','keyevent','KEYCODE_MOVE_END');adb('shell','input','keyevent','--longpress','KEYCODE_DEL')
                adb('shell','input','text',value.replace(' ','%s'));time.sleep(.5)
                adb('shell','input','keyevent','4');time.sleep(.5);return
            if b[3]>b[1]:partial=b
        if partial and partial[1]<=vp[1]+1:scroll(t,True)
        else:scroll(t)
    raise AssertionError('Editable target missing: '+label)

if __name__=='__main__':
 import sys
 if sys.argv[1]=='baseline':
  (HERE/'device-baseline.json').write_text(json.dumps({'density':adb('shell','wm','density'),'fontScale':adb('shell','settings','get','system','font_scale')},indent=2))
 elif sys.argv[1]=='case':
  run_case(sys.argv[2],int(sys.argv[3]),int(sys.argv[4]))
