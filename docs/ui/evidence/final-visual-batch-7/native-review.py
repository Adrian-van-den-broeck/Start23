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
            result = adb('shell','uiautomator','dump','/sdcard/wombo-batch7.xml')
            if 'dumped to' not in result: raise RuntimeError('No accessibility root')
            return ET.fromstring(adb('shell','cat','/sdcard/wombo-batch7.xml'))
        except (RuntimeError, subprocess.CalledProcessError):
            if attempt == 7: raise
            time.sleep(1)
def marker(tree, state):
    return any(n.get('resource-id') == 'batch-7-fixture-'+state for n in tree.iter('node'))
def capture(name, tree=None):
    config = json.loads((HERE/'fixture-config.json').read_text())
    tree = tree if tree is not None else hierarchy()
    assert marker(tree, config['state']), 'Refuse non-fixture evidence'
    ET.ElementTree(tree).write(HERE/(name+'.xml'), encoding='utf-8')
    adb('shell','screencap','-p','/sdcard/wombo-batch7.png')
    adb('pull','/sdcard/wombo-batch7.png',str(HERE/(name+'.png')))
    metadata = {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'serial':'emulator-5554',
      'size':adb('shell','wm','size'), 'density':adb('shell','wm','density'),
      'fontScale':adb('shell','settings','get','system','font_scale'), 'fixture':config,
      'provenance':'Actual production PlacementScreen/ProposalReviewScreen/ProposalAlternativesScreen; production public mappers; inert callback ledger; no server or athlete writes'}
    (HERE/(name+'.json')).write_text(json.dumps(metadata,indent=2)+'\n')
    print('Captured '+name,flush=True)
def open_review(state, language='nl'):
    path=f'wombo:///dev-batch7-review?state={state}&language={language}&review={time.time_ns()}'
    adb('shell',f"am start -a android.intent.action.VIEW -d '{path}' com.adrivdbs.wombo")
    time.sleep(3)
    for attempt in range(20):
        tree=hierarchy()
        back='Back to proposal' if language=='en' and state in ['alternatives','selected','remove','noRemove','loading','retry','emptyAlternatives','staleAlternatives','distance','sparse','long'] else 'Back to Week' if language=='en' else 'Terug naar voorstel' if state in ['alternatives','selected','remove','noRemove','loading','retry','emptyAlternatives','staleAlternatives','distance','sparse','long'] else 'Terug naar Week'
        if marker(tree,state) and any(n.get('content-desc')==back for n in tree.iter('node')): return
        time.sleep(1)
    raise AssertionError('Fixture did not settle')
def scroll(tree, reverse=False):
    boxes=[list(map(int,re.findall(r'\d+', n.get('bounds')))) for n in tree.iter('node') if n.get('class')=='android.widget.ScrollView' and n.get('scrollable')=='true']
    if not boxes:return False
    box=min(boxes,key=lambda b:b[3]-b[1]); x=box[0]+max(12,(box[2]-box[0])//50)
    adb('shell','input','swipe',str(x),str(round(box[1]+(box[3]-box[1])*(.3 if reverse else .8))),str(x),str(round(box[1]+(box[3]-box[1])*(.8 if reverse else .3))),'350')
    time.sleep(.6);return True
def pages(prefix):
    seen=set()
    for part in range(60):
        tree=hierarchy()
        signature=tuple((n.get('text'),n.get('content-desc'),n.get('bounds')) for n in tree.iter('node'))
        if signature in seen:return
        seen.add(signature);capture(prefix+f'-page-{part}',tree)
        if not scroll(tree):return
    raise AssertionError('Unexpected scroll loop')
def run_case(width,font,language,state):
    density=439 if width==393 else round(1080*160/width)
    adb('shell','wm','density',str(density));adb('shell','settings','put','system','font_scale',str(font));time.sleep(2)
    (HERE/'fixture-config.json').write_text(json.dumps({'width':width,'fontScale':font,'language':language,'state':state,'inertActions':True})+'\n')
    open_review(state,language);pages(f'{width}-font-{font}-{language}-{state}')
if __name__=='__main__':
    if sys.argv[1]=='load':
        original={key:adb('shell','settings','get',group,key) for group,key in [('system','font_scale'),('secure','enabled_accessibility_services'),('secure','accessibility_enabled'),('global','animator_duration_scale'),('global','window_animation_scale'),('global','transition_animation_scale')]}
        original['density']=adb('shell','wm','density');original['size']=adb('shell','wm','size')
        if not (HERE/'device-baseline.json').exists(): (HERE/'device-baseline.json').write_text(json.dumps(original,indent=2)+'\n')
        adb('reverse','tcp:8083','tcp:8083');adb('shell','am','force-stop','com.adrivdbs.wombo')
        adb('shell',"am start -a android.intent.action.VIEW -d 'wombo://expo-development-client/?url=http%3A%2F%2F127.0.0.1%3A8083' com.adrivdbs.wombo")
        time.sleep(12);run_case(393,1,'nl','manual')
    elif sys.argv[1]=='case':run_case(int(sys.argv[2]),int(sys.argv[3]),sys.argv[4],sys.argv[5])
