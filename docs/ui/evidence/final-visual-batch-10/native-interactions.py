from pathlib import Path
import importlib.util,json,re,time,subprocess,xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('review',HERE/'native-review.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
results=[]
def record(name,**facts):
    results.append({'name':name,'pass':True,**facts})
    (HERE/'native-interactions.json').write_text(json.dumps({'backendWrites':False,'fixtureTransportOnly':True,'results':results},indent=2)+'\n')
    print(name,'PASS',flush=True)
def reqs(t=None):
    t=t if t is not None else r.tree()
    return json.loads(next(n.get('content-desc') for n in t.iter('node') if n.get('resource-id')=='batch-10-requests'))
def event(expected):
    assert any(n.get('resource-id')=='batch-10-event' and n.get('content-desc')=='Fixture callback '+expected for n in r.tree().iter('node')),expected
def top():
    seen=set()
    for _ in range(50):
        t=r.tree();key=ET.tostring(t)
        if key in seen:return
        seen.add(key)
        if not r.scroll(t,True):return
def match_req(method,path,body):
    requests=reqs()
    assert requests==[{'method':method,'path':path,'body':None if body is None else json.dumps(body,separators=(',',':'))}],requests
    return requests
def no_write():assert reqs()==[]
def visible_node(label,clickable=None):
    t=r.tree()
    nodes=[n for n in t.iter('node') if n.get('content-desc')==label and (clickable is None or n.get('clickable')==clickable)]
    return nodes
def field(label):
    for _ in range(60):
        t=r.tree()
        sc=[r.bounds(n) for n in t.iter('node') if n.get('class')=='android.widget.ScrollView' and n.get('scrollable')=='true']
        vp=max(sc,key=lambda b:b[3]-b[1]) if sc else [0,0,1080,2280]
        for n in t.iter('node'):
            if n.get('content-desc')==label and n.get('class')=='android.widget.EditText':
                b=r.bounds(n)
                if b[1]>=vp[1] and b[3]<=vp[3]:
                    r.adb('shell','input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2));time.sleep(.6);return
        r.scroll(t)
    raise AssertionError('Missing field '+label)
def modal_capture(name):
    t=r.tree();assert any(n.get('content-desc')=='Duurkeuze sluiten' for n in t.iter('node'))
    assert any(n.get('class')=='android.widget.RadioButton' for n in t.iter('node'))
    ET.ElementTree(t).write(HERE/(name+'.xml'),encoding='utf-8')
    (HERE/(name+'.png')).write_bytes(subprocess.check_output([r.ADB,'-s',r.SERIAL,'exec-out','screencap','-p'],timeout=25))
    (HERE/(name+'.json')).write_text(json.dumps({'fixture':json.loads((HERE/'fixture-config.json').read_text()),'modal':True,'provenance':'Actual DurationPicker modal from immediately validated production fixture; underlying native hierarchy hidden by modal'},indent=2)+'\n')
def modal_tap(label):
    t=r.tree()
    for n in t.iter('node'):
        if n.get('content-desc')==label or n.get('text')==label:
            b=r.bounds(n)
            if n.get('clickable')=='true' and b[3]>b[1]:
                r.adb('shell','input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2));time.sleep(.6);return
    raise AssertionError('Missing modal option '+label)

r.open_case('profile-editor');assert not any(re.search(r'Stap \d van',n.get('text','')+n.get('content-desc','')) for n in r.tree().iter('node'))
for label,callback in [('Week','back'),('Afmelden','signout'),('Testen en kalibratie','tests'),('Pioneer toegang','pioneer')]:
    r.open_case('profile-editor');r.tap(label);event(callback);no_write();record('Profile '+callback,callback=callback)
r.open_case('profile-editor');r.tap('Profiel opslaan')
requests=reqs();assert requests==[
{'method':'PATCH','path':'/api/v1/me/physiology-profile','body':'{"date_of_birth":"1990-05-20","resting_heart_rate_bpm":52}'},
{'method':'PATCH','path':'/api/v1/me/identifying-profile','body':'{"first_name":"Ada","last_name":"Lovelace"}'}],requests
record('Profile exact split payload',requests=requests)

r.open_case('profile-editor-busy');r.tap('Profiel opslaan')
requests=reqs();assert len(requests)==2
nodes=visible_node('Profiel opslaan, busy');assert nodes and nodes[0].get('enabled')=='false'
b=r.bounds(nodes[0]);r.adb('shell','input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2));time.sleep(.3);assert reqs()==requests
r.capture('interaction-profile-busy');record('Profile busy disables repeat save',requests=len(requests))
r.open_case('profile-editor-server-error',320,2);r.tap('Profiel opslaan');top();r.pages('interaction-profile-server-error')
assert any('niet geldig' in (n.get('text','')+n.get('content-desc','')) or 'Controleer' in (n.get('text','')+n.get('content-desc','')) for p in HERE.glob('interaction-profile-server-error*.xml') for n in ET.parse(p).iter('node'))
record('Profile server validation error remains visible at 320 dp / 200%',requests=reqs())

r.open_case('monitor',320,2);r.tap('Ja, ik kan gemiddelde hartslag meten')
record('Monitor prerequisite confirmation unchanged',requests=match_req('PATCH','/api/v1/me/operational-profile',{'heart_rate_monitor_confirmed':True}))
r.open_case('timezone',320,2);r.tap('Europe/Brussels');r.tap('Tijdzone expliciet bevestigen')
record('Manual timezone confirmation unchanged',requests=match_req('PATCH','/api/v1/me/operational-profile',{'timezone':'Europe/Brussels','timezone_source':'manual','timezone_confirmed':True}))
r.open_case('history');r.tap('Trainingshistorie opslaan')
record('Three independent history baselines unchanged',requests=match_req('PUT','/api/v1/me/training-history',{'entries':[{'discipline':'swim','average_hours_per_week':'0'},{'discipline':'bike','average_hours_per_week':'0'},{'discipline':'run','average_hours_per_week':'2'}]}))

for race,disciplines in [('run',['run']),('bike',['bike']),('swim',['swim']),('duathlon',['bike','run']),('triathlon',['swim','bike','run'])]:
    r.open_case('goal-'+race);r.tap('A-doel opslaan')
    body={'race_type':race,'race_name':'Fixture race','race_date':'2099-06-15'}
    distance={'swim':1500,'bike':40000,'run':10000};split={'swim':1803,'bike':7207,'run':3601}
    body.update({d+'_distance_meters':distance[d] for d in disciplines});body['total_target_time_seconds']=13530
    body.update({d+'_target_time_seconds':split[d] for d in disciplines})
    record('Exact '+race+' payload retains applicable distances and seconds',requests=match_req('PUT','/api/v1/me/goals/fixture-goal',body))

r.open_case('goal-run-busy',320,2);r.tap('A-doel opslaan')
requests=reqs();assert len(requests)==1
nodes=visible_node('A-doel opslaan, busy');assert nodes and nodes[0].get('enabled')=='false'
b=r.bounds(nodes[0]);r.adb('shell','input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2));time.sleep(.3);assert reqs()==requests
r.capture('interaction-goal-busy');record('Goal busy disables repeat submission at 320 dp / 200%',requests=requests)

r.open_case('goal-run',320,2);r.tap('Richttempo (min/km)');field('Richttempo');r.adb('shell','input','text','5:00');time.sleep(.6)
r.capture('keyboard-goal-pace');r.target('A-doel opslaan');r.capture('keyboard-goal-save-reachable');r.tap('A-doel opslaan')
record('Run pace keyboard save retains existing total-time contract',requests=match_req('PUT','/api/v1/me/goals/fixture-goal',{'race_type':'run','race_name':'Fixture race','race_date':'2099-06-15','run_distance_meters':10000,'total_target_time_seconds':3000}))
r.adb('shell','input','keyevent','BACK')

r.open_case('goal-error',320,2);r.tap('Wedstrijd of evenement');r.tap('A-doel opslaan')
t=r.tree();assert any(n.get('class')=='android.widget.EditText' and n.get('content-desc')=='Naam van de race' and n.get('focused')=='true' for n in t.iter('node')),'First invalid name not focused'
ime=r.adb('shell','dumpsys','input_method');assert 'mInputShown=true' in ime or 'isInputViewShown=true' in ime,'IME not visible'
r.capture('keyboard-first-invalid-goal');no_write();r.adb('shell','input','keyevent','BACK');top();r.pages('interaction-goal-errors')
text=' '.join(n.get('text','')+' '+n.get('content-desc','') for p in HERE.glob('interaction-goal-errors*.xml') for n in ET.parse(p).iter('node'))
for label in ['Naam van de race is verplicht.','Racedatum is verplicht.','Afstand is verplicht.','Totale richttijd is verplicht.','Vul de gemarkeerde verplichte velden in']:assert label in text,label
record('Goal errors preserve validation and focus first invalid field',firstInvalid='Naam van de race',noWrites=True)
r.open_case('goal-run-english',320,2);r.tap('Persoonlijk doel');r.pages('interaction-personal-unavailable')
text=' '.join(n.get('text','')+' '+n.get('content-desc','') for p in HERE.glob('interaction-personal-unavailable*.xml') for n in ET.parse(p).iter('node'))
assert 'An optional personal goal with a very long supplied English label, still unavailable' in text
assert 'A-doel opslaan' not in text;no_write();record('Long supplied English personal label remains complete and unavailable',noSave=True)

r.open_case('goal-run',320,2);r.tap('Kies uren voor Totale richttijd');modal_capture('interaction-duration-modal-320-200');modal_tap('1 uur')
r.tap('Kies minuten voor Totale richttijd');modal_tap('1 minuut')
r.tap('Kies seconden voor Totale richttijd');modal_tap('3 sec')
r.tap('A-doel opslaan')
requests=reqs();body=json.loads(requests[0]['body']);assert body['total_target_time_seconds']==3663
record('Duration modal preserves hours minutes and seconds at 320 dp / 200%',totalSeconds=3663,requests=requests)

r.open_case('review-blocked',320,2);_,b=r.target('Onboarding afronden',False);r.adb('shell','input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2));no_write();record('Review prerequisite keeps completion disabled')
r.open_case('review');r.tap('Onboarding afronden');event('planning')
record('Review completion uses exact revision and opens planning',requests=match_req('POST','/api/v1/onboarding/complete',{'expected_onboarding_revision':9}),pendingPlanOnly=True)
r.open_case('review-pending');r.tap('Zones bevestigen')
record('Separate zone approval retains base precondition',requests=match_req('POST','/api/v1/change-proposals/fixture-run-proposal/approve',{'expected_base_zone_profile_id':None}))
r.open_case('review-pending');r.tap('Zonevoorstel afwijzen')
record('Separate zone rejection remains explicit',requests=match_req('POST','/api/v1/change-proposals/fixture-run-proposal/reject',None))
print('Native interactions complete:',len(results),flush=True)
