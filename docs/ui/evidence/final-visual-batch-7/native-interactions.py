from pathlib import Path
import importlib.util,json,re,time
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('review',HERE/'native-review.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
results=[]
def config(state,width=393,font=1):
    r.adb('shell','wm','density',str(439 if width==393 else round(1080*160/width)))
    r.adb('shell','settings','put','system','font_scale',str(font));time.sleep(2)
    (HERE/'fixture-config.json').write_text(json.dumps({'state':state,'language':'en','width':width,'fontScale':font,'inertActions':True})+'\n')
    r.open_review(state,'en')
def target(label,enabled=True):
    for _ in range(45):
        tree=r.hierarchy()
        state=json.loads((HERE/'fixture-config.json').read_text())['state']
        assert r.marker(tree,state), 'Refuse interaction outside the public fixture: '+state
        scrolls=[list(map(int,re.findall(r'\d+',n.get('bounds')))) for n in tree.iter('node') if n.get('class')=='android.widget.ScrollView']
        viewport=min(scrolls,key=lambda b:b[3]-b[1])
        for n in tree.iter('node'):
            if n.get('content-desc')!=label or n.get('clickable')!='true':continue
            box=list(map(int,re.findall(r'\d+',n.get('bounds'))))
            if box[1]>=viewport[1]+2 and box[3]<=viewport[3]-2 and box[3]-box[1]>=100:
                assert n.get('enabled')==str(enabled).lower(),label
                return n,box
        r.scroll(tree)
    raise AssertionError('Missing complete target '+label)
def tap(label,enabled=True):
    n,box=target(label,enabled)
    r.adb('shell','input','tap',str((box[0]+box[2])//2),str((box[1]+box[3])//2));time.sleep(.7)
def action(expected,name):
    tree=r.hierarchy();assert any(n.get('resource-id')=='batch-7-action-'+expected for n in tree.iter('node')),expected
    r.capture(name,tree);results.append({'case':name,'exactCallback':expected,'pass':True})
    (HERE/'native-interactions.json').write_text(json.dumps({'publicInertCallbacksOnly':True,'backendWrites':False,'results':results},indent=2)+'\n')
config('automatic');tap('Place automatically and submit proposal');action('submit-automatic','interaction-automatic-submit')
config('manual');tap('Submit manual placement as proposal');action('submit-manual','interaction-manual-submit')
config('incomplete');tap('Choice 2 · RUN-013 · Wisselduur · Monday 5 October 2026');action('place-repeat-2026-10-05','interaction-occurrence-date')
tap('Submit manual placement as proposal');action('submit-manual','interaction-same-date-submit')
config('incomplete');tap('Submit manual placement as proposal',False);action('none','interaction-incomplete-locked')
config('automatic');tap('Choose dates manually');action('mode-manual','interaction-mode')
config('manual');tap('Inspect workout choices');action('selection','interaction-selection-return')
config('review');tap('View alternatives · Choice 2 · RUN-010 · Duur');action('edit-proposed-repeat','interaction-edit-exact-occurrence')
for label,expected in [('Approve week','approve'),('Reject proposal','reject')]:
    config('activePending');tap(label);action(expected,'interaction-'+expected)
config('alternatives');tap('Select alternative · 2 · RUN-020 · Duur');action('select-alternative-2','interaction-select')
tap('Replace workout in proposal');action('replace-alternative-2','interaction-replace')
config('remove');tap('Remove workout from proposal');action('none','interaction-remove-confirmation')
tap('Keep workout');action('none','interaction-keep')
tap('Remove workout from proposal');tap('Confirm removal from proposal');action('remove','interaction-explicit-remove')
config('remove',320,2);tap('Remove workout from proposal');action('none','confirmation-320-font-2-en');r.pages('confirmation-320-font-2-en')
config('placementBusy');tap('Choose dates manually',False);action('none','interaction-busy-locked')
config('stale');tap('Approve week',False);action('none','interaction-stale-locked')
config('retry');tap('Reload alternatives');action('retry','interaction-retry')
config('review');tap('Back to Week');action('back','interaction-back')
(HERE/'native-interactions.json').write_text(json.dumps({'publicInertCallbacksOnly':True,'backendWrites':False,'results':results},indent=2)+'\n')
print('Native callbacks: '+str(len(results))+' passed')
