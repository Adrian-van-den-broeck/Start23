from pathlib import Path
import importlib.util,json,time,sys,xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('review',HERE/'native-review.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
resuming=any(arg.startswith('--resume-') for arg in sys.argv)
results=json.loads((HERE/'native-interactions.json').read_text())['results'] if resuming else []
def record(name,**facts):
 results.append({'name':name,'pass':True,**facts})
 (HERE/'native-interactions.json').write_text(json.dumps({'backendWrites':False,'fixtureTransportOnly':True,'results':results},indent=2)+'\n')
 print(name,'PASS',flush=True)
def callback():
 return next(n.get('text','') or n.get('content-desc','') for n in r.tree().iter('node') if n.get('resource-id')=='batch-11-callback')
def exact_request(endpoint,body):
 actual=callback();path,_,payload=actual.partition(' ')
 assert path==endpoint,(endpoint,actual)
 assert json.loads(payload or '{}')==body,(body,actual)
 return {'path':path,'body':body}
def top():
 seen=set()
 for _ in range(60):
  t=r.tree();sig=ET.tostring(t)
  if sig in seen:return
  seen.add(sig)
  if not r.scroll(t,True):return
def field(label):
 for _ in range(60):
  t=r.tree();sc=[r.bounds(n) for n in t.iter('node') if n.get('class')=='android.widget.ScrollView' and n.get('scrollable')=='true'];vp=max(sc,key=lambda b:b[3]-b[1]) if sc else [0,0,1080,2280]
  for n in t.iter('node'):
   b=r.bounds(n)
   if n.get('class')=='android.widget.EditText' and n.get('content-desc')==label and b[1]>vp[1]+1 and b[3]<vp[3]-1 and b[3]>b[1]+48:
    r.adb('shell','input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2));time.sleep(.5);return
  if not r.scroll(t):break
 raise AssertionError('Missing field '+label)
if not resuming:
 for action,path,body in [('Zones goedkeuren','/api/v1/change-proposals/zone-proposal/approve',{'expected_base_zone_profile_id':'source-run-v1'}),('Afwijzen','/api/v1/change-proposals/zone-proposal/reject',{})]:
  r.open_case('pending');r.tap(action);request=exact_request(path,body);r.capture('interaction-zone-'+('approve' if action=='Zones goedkeuren' else 'reject'));record('Zone '+action+' retains original proposal/base precondition',request=request)
 r.open_case('known',320,2);r.tap('Bekende waarden bewaren');assert not callback();top();r.pages('interaction-known-invalid')
 text=' '.join(n.get('text','')+' '+n.get('content-desc','') for p in HERE.glob('interaction-known-invalid*.xml') for n in ET.parse(p).iter('node'));assert 'Vul minstens één bekende drempelwaarde' in text
 record('Known value empty validation prevents saving',noWrites=True)
if '--resume-choice' not in sys.argv:
 r.open_case('known',320,2);field('Drempeltempo');r.adb('shell','input','text','5:00');time.sleep(.5)
 assert any(n.get('class')=='android.widget.EditText' and n.get('content-desc')=='Drempeltempo' and n.get('focused')=='true' and n.get('text')=='5:00' for n in r.tree().iter('node')), 'Pace field was not focused/entered'
 r.capture('keyboard-zone-pace');r.adb('shell','input','keyevent','4');time.sleep(.5);r.target('Bekende waarden bewaren');r.capture('keyboard-zone-save-reachable');r.tap('Bekende waarden bewaren')
 actual=callback();assert actual.startswith('run ');body=json.loads(actual[4:]);assert body=={'setup_route':'known_values','guidance_mode':'pace','source_quality':'athlete_entered','thresholds':[{'metric_kind':'run_threshold_pace_seconds_per_km','value':'300'}],'zone_profiles':[]},body
 record('Known pace saves existing canonical seconds payload',discipline='run',body=body)
r.open_case('choice');r.tap('Week-1-kalibratie kiezen');actual=callback();assert actual.startswith('run ');body=json.loads(actual[4:]);assert body=={'setup_route':'calibration_week','guidance_mode':'heart_rate'},body
record('Calibration route saves only current supported setup',body=body)
r.open_case('result');r.tap('Drempel afwijzen');request=exact_request('/api/v1/calibration/evaluations/evaluation-id/threshold/reject',{});r.capture('interaction-threshold-reject');record('Threshold rejection remains distinct from zones',request=request)
r.open_case('result');r.tap('Drempel bevestigen');request=exact_request('/api/v1/calibration/evaluations/evaluation-id/threshold/confirm',{'confirmed':True});r.target('Zones bevestigen');r.capture('interaction-threshold-confirm-pending');record('Threshold confirmation exposes a separately pending zone action',request=request)
r.tap('Zones bevestigen');request=exact_request('/api/v1/change-proposals/zone-proposal/approve',{'expected_base_zone_profile_id':'source-run-v1'});record('Explicit zone approval retains original base profile',request=request)
r.open_case('feedback');r.tap('Opslaan en deterministisch evalueren');assert not callback();record('Incomplete observation cannot submit or manufacture success',noWrites=True)
r.open_case('empty');r.tap('Terug naar intake');assert callback()=='back';record('Unavailable protocol uses existing back callback',callback='back')
