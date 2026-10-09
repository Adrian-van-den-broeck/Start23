from pathlib import Path
import datetime,json,re,subprocess,time,os,xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
ADB='C:/Users/Adria/AppData/Local/Android/Sdk/platform-tools/adb.exe'
SERIAL=os.environ.get('BATCH10_ANDROID_SERIAL','emulator-5554')
def adb(*args):
    return subprocess.check_output([ADB,'-s',SERIAL,*args],text=True,encoding='utf-8',timeout=25).strip()
def tree():
    adb('shell','uiautomator','dump','/sdcard/batch10.xml')
    return ET.fromstring(adb('shell','cat','/sdcard/batch10.xml'))
def bounds(n):return list(map(int,re.findall(r'-?\d+',n.get('bounds',''))))
def valid(t,state):
    ids={n.get('resource-id') for n in t.iter('node')}
    assert 'batch-10-fixture-'+state in ids and 'batch-10-build-final-7' in ids,'Wrong fixture/build'
    assert not any('LogBox' in str(n.attrib) or 'configured linking in multiple places' in str(n.attrib) for n in t.iter('node')),'Development overlay'
def capture(name,t=None,state=None):
    t=t if t is not None else tree()
    config=json.loads((HERE/'fixture-config.json').read_text());valid(t,state or config['state'])
    ET.ElementTree(t).write(HERE/(name+'.xml'),encoding='utf-8')
    data=subprocess.check_output([ADB,'-s',SERIAL,'exec-out','screencap','-p'],timeout=25)
    (HERE/(name+'.png')).write_bytes(data)
    (HERE/(name+'.json')).write_text(json.dumps({'timestampUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'fixture':config,'size':adb('shell','wm','size'),'density':adb('shell','wm','density'),'fontScale':adb('shell','settings','get','system','font_scale'),'provenance':'Production ProfileScreen/OnboardingScreen and GoalStep; typed inert DTOs; blocked live transport; callback markers prove UI dispatch only'},indent=2)+'\n')
def scroll(t,reverse=False):
    scrolls=[bounds(n) for n in t.iter('node') if n.get('class')=='android.widget.ScrollView' and n.get('scrollable')=='true']
    if not scrolls:return False
    b=max(scrolls,key=lambda b:b[3]-b[1]);x=b[0]+12
    adb('shell','input','swipe',str(x),str(round(b[1]+(b[3]-b[1])*(.25 if reverse else .82))),str(x),str(round(b[1]+(b[3]-b[1])*(.82 if reverse else .25))),'300');time.sleep(.3);return True
def open_case(state,width=393,font=1):
    # A previous Android Back cleanup can return to the launcher; foreground the existing client.
    adb('shell','am','start','-n','com.adrivdbs.wombo/.MainActivity')
    density=439 if width==393 else round(1080*160/width)
    adb('shell','wm','density',str(density));adb('shell','settings','put','system','font_scale',str(font));time.sleep(.7)
    (HERE/'fixture-config.json').write_text(json.dumps({'state':state,'width':width,'fontScale':font,'build':'final-7','language':'source Dutch','inertActions':True})+'\n')
    (HERE.parents[3]/'mobile/public/batch10-fixture.json').write_text(json.dumps({'state':state,'nonce':str(time.time_ns())}))
    expected = 'Jouw basis' if state.startswith('profile') else 'Kies je trainingsdoel' if state.startswith('goal') else 'Bevestig je tijdzone' if state in ['timezone','upgrade'] else 'Heb je toegang tot een hartslagmeter?' if state in ['monitor','resume'] else 'Waar sta je nu?' if state=='history' else 'Instellen voor' if state=='zones' else 'Klaar voor je eerste voorstel'
    moved=False
    for _ in range(30):
        time.sleep(.7)
        t=tree()
        ids={n.get('resource-id') for n in t.iter('node')}
        if 'batch-10-fixture-'+state in ids and any(expected in (n.get('text','')+' '+n.get('content-desc','')) for n in t.iter('node')):
            valid(t,state)
            if moved:
                seen=set()
                for _ in range(50):
                    back=tree();signature=ET.tostring(back)
                    if signature in seen:break
                    seen.add(signature)
                    if not scroll(back,True):break
            return
        if 'batch-10-fixture-'+state in ids:
            valid(t,state);moved=scroll(t) or moved
    raise AssertionError('Fixture did not load: '+state)
def pages(prefix):
    seen=set()
    for part in range(60):
        t=tree();signature=tuple((n.get('text'),n.get('content-desc'),n.get('bounds')) for n in t.iter('node'))
        if signature in seen:return part
        seen.add(signature);capture(prefix+'-page-'+str(part),t)
        if not scroll(t):return part+1
    raise AssertionError('Scroll did not settle')
def run_case(state,width=393,font=1):
    open_case(state,width,font);prefix=str(width)+'-font-'+str(font)+'-'+state
    count=pages(prefix);ledger=json.loads((HERE/'case-ledger.json').read_text()) if (HERE/'case-ledger.json').exists() else []
    ledger.append({'state':state,'width':width,'fontScale':font,'pages':count});(HERE/'case-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
    print(prefix+': '+str(count)+' viewports',flush=True)
def target(label,enabled=True):
    for _ in range(60):
        t=tree();config=json.loads((HERE/'fixture-config.json').read_text());valid(t,config['state'])
        sc=[bounds(n) for n in t.iter('node') if n.get('class')=='android.widget.ScrollView' and n.get('scrollable')=='true']
        vp=max(sc,key=lambda b:b[3]-b[1]) if sc else [0,0,1080,2280]
        for n in t.iter('node'):
            if n.get('content-desc','').removesuffix(', busy')!=label or n.get('clickable')!='true':continue
            b=bounds(n)
            # Hierarchy rectangles touching a scroll edge may be clipped, including by the IME.
            if b[1]>vp[1]+1 and b[3]<vp[3]-1 and b[3]-b[1]>=48:
                assert n.get('enabled')==str(enabled).lower(),label
                return n,b
        if not scroll(t):break
    raise AssertionError('Missing complete target '+label)
def tap(label,enabled=True):
    _,b=target(label,enabled);adb('shell','input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2));time.sleep(.6)
if __name__=='__main__':
    import sys
    if sys.argv[1]=='connect':
        baseline={'density':adb('shell','wm','density'),'size':adb('shell','wm','size'),'fontScale':adb('shell','settings','get','system','font_scale')}
        if not (HERE/'device-baseline.json').exists(): (HERE/'device-baseline.json').write_text(json.dumps(baseline,indent=2)+'\n')
        adb('reverse','tcp:8084','tcp:8084');adb('shell','am','force-stop','com.adrivdbs.wombo')
        adb('shell',"am start -a android.intent.action.VIEW -d 'wombo://expo-development-client/?url=http%3A%2F%2F127.0.0.1%3A8084' com.adrivdbs.wombo")
        time.sleep(10);run_case('profile-editor')
    elif sys.argv[1]=='case':run_case(sys.argv[2],int(sys.argv[3]),int(sys.argv[4]))
