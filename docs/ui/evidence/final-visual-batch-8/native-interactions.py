from pathlib import Path
import importlib.util,json,re,sys,time,xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('review',HERE/'native-review.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
results=[]
if '--resume-occurrence' in sys.argv or '--resume-return' in sys.argv:
    saved=json.loads((HERE/'native-interactions.json').read_text())
    expected=23 if '--resume-return' in sys.argv else 20
    assert saved['backendWrites'] is False and len(saved['results'])==expected and all(v['pass'] for v in saved['results'])
    results=saved['results']

def bounds(node):
    return list(map(int,re.findall(r'\d+',node.get('bounds'))))

def within(child,parent):
    # Native parent/child edges can differ by one pixel after dp rounding.
    return child[2]>child[0] and child[3]>child[1] and parent[0]-2<=child[0] and parent[1]-2<=child[1] and child[2]<=parent[2]+2 and child[3]<=parent[3]+2

def complete_pages(prefix):
    # A callback may retain its previous scroll offset; inspect the whole return.
    for p in HERE.glob(prefix+'-page-*'):
        assert p.resolve().parent==HERE.resolve()
        p.unlink()
    r.top()
    r.pages(prefix)

def start(state,width=393,font=1):
    r.adb('shell','wm','density',str(439 if width==393 else round(1080*160/width)))
    r.adb('shell','settings','put','system','font_scale',str(font));time.sleep(2)
    (HERE/'fixture-config.json').write_text(json.dumps({'state':state,'language':'en','width':width,'fontScale':font,'inertActions':True})+'\n')
    r.open_review(state,'en')

def check(expected,name,returned=False):
    tree=r.hierarchy();assert any(n.get('resource-id')=='batch-8-action-'+expected for n in tree.iter('node')),expected
    if returned:assert not any(n.get('resource-id')=='workout-detail-scroll' for n in tree.iter('node'))
    r.capture(name,tree);results.append({'case':name,'exactCallback':expected,'modalReturned':returned,'pass':True})
    (HERE/'native-interactions.json').write_text(json.dumps({'publicInertCallbacksOnly':True,'backendWrites':False,'results':results},indent=2)+'\n')

def scoped_tap(id,label):
    for _ in range(45):
        tree=r.hierarchy();assert r.marker(tree,'multiple')
        scope=next((n for n in tree.iter('node') if n.get('resource-id')=='calendar-workout-'+id),None)
        viewport=min([list(map(int,re.findall(r'\d+',n.get('bounds')))) for n in tree.iter('node') if n.get('class')=='android.widget.ScrollView'],key=lambda b:b[3]-b[1])
        if scope is not None:
            # UIAutomator exposes test-ID wrappers and their accessible controls
            # as siblings: require the exact occurrence wrapper's visible bounds.
            for n in tree.iter('node'):
                if r.label_of(n)!=label or n.get('clickable')!='true':continue
                box=bounds(n)
                if within(box,bounds(scope)) and box[1]>viewport[1]+2 and box[3]<viewport[3]-2:
                    assert n.get('enabled')=='true' and box[3]-box[1]>=100
                    r.adb('shell','input','tap',str((box[0]+box[2])//2),str((box[1]+box[3])//2));time.sleep(.7);return
        r.scroll(tree)
    raise AssertionError('Missing scoped occurrence '+id)

if not results:
    start('before');r.tap('Move RUN-013 · Wisselduur');check('entry-workout-a','interaction-calendar-entry')
    start('chooser');r.tap('Review move',False);check('none','interaction-origin-noop-lock')
    r.tap('Thursday 8 October 2026');check('none','interaction-date-local-only')
    r.tap('Review move');check('review-workout-a-2026-10-08','interaction-explicit-review')
    complete_pages('interaction-warning-complete')
    r.tap('Move anyway');check('confirm-workout-a-2026-10-08','interaction-explicit-proceed',True)
    complete_pages('interaction-after-complete')
    start('chooser');r.tap('Thursday 8 October 2026');r.top();r.tap('Wednesday 7 October 2026 · Current date');r.tap('Review move',False)
    check('none','interaction-return-to-origin-lock')
    r.tap('Cancel');check('cancel-workout-a','interaction-chooser-cancel',True)
    start('chooser');r.adb('shell','input','keyevent','4');time.sleep(1);check('cancel-workout-a','interaction-chooser-system-back',True)
    start('warning');r.tap('Move anyway');check('confirm-workout-a-2026-10-08','interaction-warning-proceed',True)
    start('warning');r.tap('Cancel');check('cancel-workout-a','interaction-warning-cancel',True)
    start('warning');r.adb('shell','input','keyevent','4');time.sleep(1);check('cancel-workout-a','interaction-warning-system-back',True)
    start('validation');r.tap('Thursday 8 October 2026');r.tap('Review move');r.tap('Review move',False)
    check('review-workout-a-2026-10-08','interaction-validation-locked')
    r.tap('Cancel',False);r.adb('shell','input','keyevent','4');time.sleep(1)
    check('review-workout-a-2026-10-08','interaction-validation-dismissal-locked')
    start('confirmBusy');r.tap('Move anyway',False);check('none','interaction-busy-proceed-locked')
    r.tap('Cancel',False);r.adb('shell','input','keyevent','4');time.sleep(1);check('none','interaction-busy-dismissal-locked')
    start('stale');r.tap('Move anyway',False);check('none','interaction-stale-proceed-locked')
    r.tap('Cancel');check('cancel-workout-a','interaction-stale-cancel',True)
    start('staleChooser');r.tap('Thursday 8 October 2026',False);r.tap('Review move',False);check('none','interaction-stale-date-locked')
    for state in ['rejected','ambiguous']:
        start(state);complete_pages('interaction-'+state+'-complete');r.tap('Cancel');check('cancel-workout-a','interaction-'+state+'-cancel',True)
if len(results)==20:
    start('multiple');scoped_tap('repeat-occurrence','Move RUN-013 · Wisselduur');check('entry-repeat-occurrence','interaction-exact-repeat-entry')
    r.tap('Thursday 8 October 2026');r.tap('Review move');check('review-repeat-occurrence-2026-10-08','interaction-exact-repeat-review')
    r.tap('Move anyway');check('confirm-repeat-occurrence-2026-10-08','interaction-exact-repeat-proceed',True)
    complete_pages('interaction-repeat-after-complete')
locations={}
completed_move=False
for p in HERE.glob('interaction-repeat-after-complete-page-*.xml'):
    tree=ET.parse(p).getroot()
    for day in tree.iter('node'):
        date=(day.get('resource-id') or '').removeprefix('calendar-day-')
        if not re.fullmatch(r'2026-10-\d{2}',date):continue
        for row in tree.iter('node'):
            id=(row.get('resource-id') or '').removeprefix('calendar-workout-')
            if id not in ['workout-a','repeat-occurrence','completed-occurrence']:continue
            if not within(bounds(row),bounds(day)):continue
            assert id not in locations or locations[id]==date
            locations[id]=date
            if id=='completed-occurrence':completed_move |= any(n.get('content-desc','').startswith('Move ') and within(bounds(n),bounds(row)) for n in tree.iter('node'))
assert locations=={'workout-a':'2026-10-07','repeat-occurrence':'2026-10-08','completed-occurrence':'2026-10-07'}
assert not completed_move
(HERE/'native-occurrence-return-audit.json').write_text(json.dumps({'pass':True,'locations':locations,'completedOccurrenceHasMove':False,'identityEvidence':'Exact native occurrence/day test IDs and their visible bounds; Android accessibility siblings'},indent=2)+'\n')
start('chooser',320,2);r.tap('Thursday 8 October 2026');r.tap('Review move');check('review-workout-a-2026-10-08','interaction-large-type-review')
complete_pages('interaction-large-type-warning-complete');r.tap('Cancel');check('cancel-workout-a','interaction-large-type-cancel',True)
print('Native callbacks:',len(results),'passed')
