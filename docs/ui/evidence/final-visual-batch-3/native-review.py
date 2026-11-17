"""Actual Android rendering of unchanged public fixtures and existing route owners."""
from pathlib import Path
import datetime, importlib.util, json, re, sys, time
import xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('shell_review',HERE.parent/'final-visual-batch-2/native-review.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base);base.HERE=HERE

def capture_tree(name,tree):
    ET.ElementTree(tree).write(HERE/(name+'.xml'),encoding='utf-8')
    base.adb('shell','screencap','-p','/sdcard/wombo-shell.png')
    base.adb('pull','/sdcard/wombo-shell.png',str(HERE/(name+'.png')))
    (HERE/(name+'.json')).write_text(json.dumps({
      'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'serial':'emulator-5554',
      'density':base.adb('shell','wm','density'),'fontScale':base.adb('shell','settings','get','system','font_scale'),
      'fixture':json.loads((HERE/'fixture-config.json').read_text()),
      'provenance':'Actual native WorkoutDetailScreen, unchanged existing public test source; no athlete writes',
    },indent=2)+'\n')
    print('Captured '+name,flush=True)

def open_review(state,language='nl',review='initial'):
    path=f'dev-workout-review?state={state}&language={language}&review={review}'
    base.open_path(path)
    for _ in range(20):
        tree=base.hierarchy()
        if any('Exact source workout' in (n.get('text','')+' '+n.get('content-desc','')) for n in tree.iter('node')):return
        if _ % 4 == 3:base.open_path(path)
        time.sleep(1)
    raise AssertionError('Native detail fixture did not settle')

def pages(prefix):
    seen=set();part=0;expanded=False
    while part<16:
        tree=base.hierarchy()
        signature=tuple((n.get('text'),n.get('content-desc'),n.get('bounds')) for n in tree.iter('node'))
        if signature in seen:break
        seen.add(signature)
        name=prefix+f'-page-{part}';capture_tree(name,tree);part+=1
        nodes=list(tree.iter('node'))
        button=next((n for n in nodes if n.get('clickable')=='true' and n.get('content-desc') in ['RPE reference','RPE-uitleg']),None)
        if button is not None and not expanded:
            a,b,c,d=map(int,re.findall(r'\d+',button.get('bounds')))
            if d>b and b>80:
                base.adb('shell','input','tap',str((a+c)//2),str((b+d)//2));time.sleep(1);expanded=True
                base.capture(prefix+'-reference-expanded')
        base.scroll_in_view(cached=name)
    assert part<16,'Unexpected scroll loop'

if __name__=='__main__':
    if sys.argv[1]=='load':
        base.configure('nl');base.adb('reverse','tcp:8123','tcp:8123')
        base.adb('shell','am','force-stop','com.adrivdbs.wombo')
        base.adb('shell',"am start -a android.intent.action.VIEW -d 'wombo://expo-development-client/?url=http%3A%2F%2F127.0.0.1%3A8081' com.adrivdbs.wombo")
        time.sleep(5);open_review('swim');base.capture('first-swim-reference')
    elif sys.argv[1]=='case':
        width,font,language,state=int(sys.argv[2]),int(sys.argv[3]),sys.argv[4],sys.argv[5]
        base.dimensions(540 if width==320 else 439,font);base.configure(language)
        prefix=f'{width}-font-{font}-{language}-{state}'
        open_review(state,language,prefix);pages(prefix)
    elif sys.argv[1]=='capture':base.capture(sys.argv[2])
    elif sys.argv[1]=='origin':
        base.dimensions(439,1);base.configure('en')
        open_review('swim','en','origin-language')
        base.open_path('planning');time.sleep(3)
        tree=base.hierarchy()
        for n in tree.iter('node'):
            if n.get('clickable')=='true' and any(c.get('text')=='UI V2' for c in n.iter('node')):
                a,b,c,d=map(int,re.findall(r'\d+',n.get('bounds')));base.adb('shell','input','tap',str((a+c)//2),str((b+d)//2));break
        time.sleep(3);base.tap_label('Calendar');base.scroll_in_view()
        for _ in range(8):
            try:
                if any(n.get('clickable')=='true' and 'View workout' in n.get('content-desc','') for n in base.hierarchy().iter('node')):
                    base.capture('calendar-before-detail');base.tap_partial('View workout');break
                base.scroll_in_view()
            except StopIteration:base.scroll_in_view()
        else:raise AssertionError('Calendar source workout unreachable')
        base.capture('calendar-detail-entry');base.tap_label('Close');base.capture('calendar-detail-return')
        base.tap_partial('View workout');time.sleep(1)
        base.adb('shell','input','keyevent','4');time.sleep(2)
        base.capture('calendar-hardware-back-return')
        base.tap_label('Week');base.scroll_in_view();base.capture('week-before-detail');base.tap_partial('View workout');base.capture('week-detail-entry')
        base.tap_label('Close');base.capture('week-detail-return')
