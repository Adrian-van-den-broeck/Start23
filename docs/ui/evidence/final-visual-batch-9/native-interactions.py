from pathlib import Path
import importlib.util,json,re,time
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('review',HERE/'native-review.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
results=[]
def begin(state,width=393,font=1):
    r.adb('shell','wm','density',str(439 if width==393 else round(1080*160/width)))
    r.adb('shell','settings','put','system','font_scale',str(font));time.sleep(1)
    (HERE/'fixture-config.json').write_text(json.dumps({'width':width,'fontScale':font,'language':'en','state':state,'build':'final-4','inertActions':True})+'\n')
    r.open_review(state,'en')
def action(expected,name):
    tree=r.hierarchy();assert r.marker(tree,json.loads((HERE/'fixture-config.json').read_text())['state'])
    assert any(n.get('resource-id')=='batch-9-action-'+expected for n in tree.iter('node')),expected
    results.append({'name':name,'exactMarker':expected,'pass':True})
    (HERE/'native-interactions.json').write_text(json.dumps({'backendWrites':False,'results':results},indent=2)+'\n')
def find_label(predicate):
    for _ in range(35):
        tree=r.hierarchy()
        labels=[r.label_of(n) for n in tree.iter('node') if predicate(r.label_of(n)) and n.get('clickable')=='true']
        if labels:return labels[0]
        r.scroll(tree)
    raise AssertionError('Missing exact fixture action')
def score(value):return find_label(lambda s:s.startswith('Save RPE · ') and s.endswith(f'(RPE {value})'))
def outer_tap(label):
    nodes=[n for n in r.hierarchy().iter('node') if r.label_of(n)==label and n.get('clickable')=='true']
    assert len(nodes)==1
    box=list(map(int,re.findall(r'\d+',nodes[0].get('bounds'))))
    assert box[3]-box[1]>=130 and nodes[0].get('enabled')=='true'
    r.adb('shell','input','tap',str((box[0]+box[2])//2),str((box[1]+box[3])//2));time.sleep(1)

begin('empty');r.tap('Add activity');action('add','Add opens existing entry')
r.tap('Choose a planned or extra workout');action('add','Context expansion does not create')
r.tap('Same supplied template · Running · Wednesday, 7 October 2026');action('context-occurrence-b','Choose exact repeated occurrence')
r.tap('Choose a planned or extra workout');r.tap('Extra, unplanned workout');action('context-unplanned','Reset to deliberate extra')
r.tap('Cycling');action('sport-bike','Sport choice stays local')
r.tap('Running');action('sport-run','Return to Run stays local')
r.tap('Save activity');action('create-run-45-5000','Explicit create enters same pending feedback')
r.tap(score(4));action('rpe-activity-a-4-hr-','RPE tap directly saves and returns; no Save step')
tree=r.hierarchy();assert any(n.get('resource-id')=='v2-activities' for n in tree.iter('node'))
r.top();r.pages('interaction-after-feedback')

begin('context');r.tap('Choose a planned or extra workout')
r.tap('Public external activity · Cycling · Thursday, 8 October 2026, 18:00 · Outside Wombo')
action('context-external-a','External exact identity')
r.top();r.tap('Back to Activities');action('entry-back','Entry Back returns without create')

begin('blocked');r.tap('Add activity',False);action('none','Pending disables Add')
r.tap('Complete feedback');action('feedback-activity-a','Pending continuation preserves activity identity')
r.top();r.tap('Back to Activities');action('feedback-back-activity-a','Feedback Back preserves pending context')

begin('history');correction=find_label(lambda s:s.startswith("Correct this week’s RPE · Running · "))
r.tap(correction);action('correct-activity-a','Eligible correction uses exact activity')
r.tap(score(7));action('rpe-activity-a-7-hr-','Correction choice saves immediately')

begin('match');match=find_label(lambda s:s.startswith('Explicitly confirm match · Same supplied template · '))
action('none','Match is not automatic');r.tap(match);action('match-activity-a-occurrence-b','Explicit match exact identifiers')

begin('reminderWeek');outer_tap('1 workout waiting for RPE · open Training & RPE')
action('reminder-activity-a','Global reminder enters pending Activities')
r.tap('Complete feedback');action('feedback-activity-a','Reminder destination resumes same feedback')
r.capture('interaction-reminder-feedback')

begin('busyCreate');r.tap('Save activity',False);action('none','Create busy prevents submission')
r.top();r.tap('Back to Activities',False);action('none','Create busy locks dismissal')
begin('busyRpe');r.tap(score(4),False);action('none','Feedback busy prevents a choice save')
r.top();r.tap('Back to Activities',False);action('none','Feedback busy locks dismissal')
begin('timezoneMissing');r.tap('Save activity',False);action('none','Missing confirmed timezone retains disabled save')

begin('rpe',320,2);r.tap(score(10));action('rpe-activity-a-10-hr-','Last canonical choice saves at 320 dp and 200% text')
print('Native exact callback checks:',len(results),'PASS')
