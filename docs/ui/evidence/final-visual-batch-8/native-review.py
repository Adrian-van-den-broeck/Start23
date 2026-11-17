from pathlib import Path
import datetime, importlib.util, json, re, subprocess, sys, time
import xml.etree.ElementTree as ET
HERE = Path(__file__).resolve().parent
ADB = 'C:/Users/Adria/AppData/Local/Android/Sdk/platform-tools/adb.exe'
def adb(*args):
    return subprocess.check_output([ADB, '-s', 'emulator-5554', *args], text=True, encoding='utf-8').strip()
def hierarchy():
    for attempt in range(8):
        try:
            result = adb('shell','uiautomator','dump','/sdcard/wombo-batch8.xml')
            if 'dumped to' not in result: raise RuntimeError('No accessibility root')
            return ET.fromstring(adb('shell','cat','/sdcard/wombo-batch8.xml'))
        except (RuntimeError, subprocess.CalledProcessError):
            if attempt == 7: raise
            time.sleep(1)
def marker(tree, state):
    return any(n.get('resource-id') == 'batch-8-fixture-'+state for n in tree.iter('node'))

def label_of(node):
    # Android appends the native accessibility busy state to content-desc.
    return node.get('content-desc', '').removesuffix(', busy')
def capture(name, tree=None):
    config = json.loads((HERE/'fixture-config.json').read_text())
    tree = tree if tree is not None else hierarchy()
    assert marker(tree, config['state']), 'Refuse non-fixture evidence'
    ET.ElementTree(tree).write(HERE/(name+'.xml'), encoding='utf-8')
    adb('shell','screencap','-p','/sdcard/wombo-batch8.png')
    adb('pull','/sdcard/wombo-batch8.png',str(HERE/(name+'.png')))
    metadata = {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'serial':'emulator-5554',
      'size':adb('shell','wm','size'), 'density':adb('shell','wm','density'),
      'fontScale':adb('shell','settings','get','system','font_scale'), 'fixture':config,
      'provenance':'Actual production WorkoutMoveScreen/CalendarScreen; production public mappers; inert callback ledger; no server or athlete writes'}
    (HERE/(name+'.json')).write_text(json.dumps(metadata,indent=2)+'\n')
    print('Captured '+name,flush=True)
def open_review(state, language='nl'):
    back=('Back to Week' if language=='en' else 'Terug naar Week') if state in ['before','after','cancel','laterCalendar','multiple'] else ('Cancel' if language=='en' else 'Annuleren')
    for connection in range(2):
        path=f'wombo:///dev-batch8-review?state={state}&language={language}&review={time.time_ns()}'
        adb('shell',f"am start -a android.intent.action.VIEW -d '{path}' com.adrivdbs.wombo")
        time.sleep(3)
        for attempt in range(20):
            tree=hierarchy()
            if marker(tree,state) and any(label_of(n)==back for n in tree.iter('node')):return
            time.sleep(1)
        if connection==0:
            print('Fixture unavailable; reconnecting only the owned preview',flush=True)
            adb('reverse','tcp:8084','tcp:8084');adb('shell','am','force-stop','com.adrivdbs.wombo')
            adb('shell',"am start -a android.intent.action.VIEW -d 'wombo://expo-development-client/?url=http%3A%2F%2F127.0.0.1%3A8084' com.adrivdbs.wombo")
            time.sleep(12)
    raise AssertionError('Fixture did not settle')

def target(label, enabled=True):
    for _ in range(45):
        tree=hierarchy();state=json.loads((HERE/'fixture-config.json').read_text())['state']
        assert marker(tree,state),'Refuse interaction outside public fixture'
        scrolls=[list(map(int,re.findall(r'\d+',n.get('bounds')))) for n in tree.iter('node') if n.get('class')=='android.widget.ScrollView']
        viewport=min(scrolls,key=lambda b:b[3]-b[1])
        for n in tree.iter('node'):
            if label_of(n)!=label or n.get('clickable')!='true':continue
            box=list(map(int,re.findall(r'\d+',n.get('bounds'))))
            if box[1]>=viewport[1]+2 and box[3]<=viewport[3]-2 and box[3]-box[1]>=100:
                assert n.get('enabled')==str(enabled).lower(),label
                return n,box
        scroll(tree)
    raise AssertionError('Missing complete target '+label)

def tap(label, enabled=True):
    _,box=target(label,enabled)
    adb('shell','input','tap',str((box[0]+box[2])//2),str((box[1]+box[3])//2));time.sleep(.7)

def top():
    previous=None
    for _ in range(15):
        tree=hierarchy();signature=tuple((n.get('text'),n.get('content-desc'),n.get('bounds')) for n in tree.iter('node'))
        if signature==previous:return
        previous=signature
        if not scroll(tree,True):return

def scroll(tree, reverse=False):
    boxes=[list(map(int,re.findall(r'\d+', n.get('bounds')))) for n in tree.iter('node') if n.get('class')=='android.widget.ScrollView' and n.get('scrollable')=='true']
    if not boxes:return False
    box=min(boxes,key=lambda b:b[3]-b[1]); x=(box[0]+box[2])//2
    adb('shell','input','swipe',str(x),str(round(box[1]+(box[3]-box[1])*(.3 if reverse else .8))),str(x),str(round(box[1]+(box[3]-box[1])*(.8 if reverse else .3))),'350')
    time.sleep(.6);return True
def pages(prefix):
    seen=set();stalled=0
    for part in range(60):
        tree=hierarchy()
        signature=tuple((n.get('text'),n.get('content-desc'),n.get('bounds')) for n in tree.iter('node'))
        if signature in seen:
            boxes=[list(map(int,re.findall(r'\d+',n.get('bounds')))) for n in tree.iter('node') if n.get('class')=='android.widget.ScrollView']
            viewport=min(boxes,key=lambda b:b[3]-b[1])
            config=json.loads((HERE/'fixture-config.json').read_text())
            calendar=any(n.get('resource-id')=='calendar-scroll' for n in tree.iter('node'))
            end=[]
            for n in tree.iter('node'):
                matches=n.get('resource-id')=='calendar-day-2026-10-11' if calendar else label_of(n) in ['Cancel','Annuleren']
                if not matches:continue
                box=list(map(int,re.findall(r'\d+',n.get('bounds'))))
                if box[1]>max(viewport[1]+2,760 if not calendar else viewport[1]+2) and box[3]<viewport[3]-2:end.append(box)
            if end:return
            stalled+=1
            if stalled>3:raise AssertionError('Refuse incomplete scroll evidence: '+prefix)
            scroll(tree);continue
        stalled=0
        seen.add(signature);capture(prefix+f'-page-{part}',tree)
        if not scroll(tree):return
    raise AssertionError('Unexpected scroll loop')
def run_case(width,font,language,state):
    density=439 if width==393 else round(1080*160/width)
    adb('shell','wm','density',str(density));adb('shell','settings','put','system','font_scale',str(font));time.sleep(2)
    (HERE/'fixture-config.json').write_text(json.dumps({'width':width,'fontScale':font,'language':language,'state':state,'inertActions':True})+'\n')
    open_review(state,language)
    if state in ['selected','validation']:
        tap('Thursday 8 October 2026' if language=='en' else 'donderdag 8 oktober 2026')
        if state=='validation':tap('Review move' if language=='en' else 'Verplaatsing controleren')
        top()
    prefix=f'{width}-font-{font}-{language}-{state}'
    for p in HERE.glob(prefix+'-page-*'):
        assert p.resolve().parent==HERE.resolve()
        p.unlink()
    pages(prefix)
if __name__=='__main__':
    if sys.argv[1]=='load':
        original={key:adb('shell','settings','get',group,key) for group,key in [('system','font_scale'),('secure','enabled_accessibility_services'),('secure','accessibility_enabled'),('global','animator_duration_scale'),('global','window_animation_scale'),('global','transition_animation_scale')]}
        original['density']=adb('shell','wm','density');original['size']=adb('shell','wm','size')
        if not (HERE/'device-baseline.json').exists(): (HERE/'device-baseline.json').write_text(json.dumps(original,indent=2)+'\n')
        adb('reverse','tcp:8084','tcp:8084');adb('shell','am','force-stop','com.adrivdbs.wombo')
        adb('shell',"am start -a android.intent.action.VIEW -d 'wombo://expo-development-client/?url=http%3A%2F%2F127.0.0.1%3A8084' com.adrivdbs.wombo")
        time.sleep(12);run_case(393,1,'nl','chooser')
    elif sys.argv[1]=='case':run_case(int(sys.argv[2]),int(sys.argv[3]),sys.argv[4],sys.argv[5])
