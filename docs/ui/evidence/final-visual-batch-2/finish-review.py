"""Record accepted accessibility observations and restored emulator state."""
from pathlib import Path
import importlib.util, json, socket, time
from PIL import Image
here = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('review', here/'native-review.py')
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
names = ['accepted-talkback-'+part for part in [
    'calendar-focus','calendar-activated','activities-focus','activities-activated',
    'week-focus','week-activated','heading-focus','profile-focus','profile-activated']]
for name in names:
    data = json.loads((here/(name+'.json')).read_text())
    assert data['enabled']=='1' and 'TalkBackService' in data['accessibilityServices']
    im = Image.open(here/(name+'.png')).convert('RGB')
    assert sum(1 for r,g,b in im.getdata() if 60<r<160 and 150<g<235 and b<90)>500
(here/'accessibility-review.json').write_text(json.dumps({
    'acceptedCaptures':names,'talkBackVersion':'15.0.0.639625893',
    'input':'Emulator native touchscreen events through one authenticated console connection for timed double taps',
    'uiAutomationUsedWhileTalkBackEnabled':False,
    'visuallyVerified':['Calendar focus and activation selects Calendar','Activities focus and activation selects Activities',
      'Week focus and activation selects Week','Week return automatically focuses heading','Profile focus and activation opens secondary profile'],
    'decorativeLandscape':'Excluded from accessibility tree in source/component assertions',
    'speechAudioRecorded':False,'reducedMotionCapture':'reduced-motion-week',
    'diagnosticPromptStaleAndFrameworkInputFramesExcluded':True,
},indent=2)+'\n')
baseline = json.loads((here/'accessibility-baseline.json').read_text())
state={}
for namespace,key,field in [('secure','enabled_accessibility_services','enabledServices'),
    ('secure','accessibility_enabled','enabled'),('global','animator_duration_scale','animator'),
    ('global','window_animation_scale','window'),('global','transition_animation_scale','transition')]:
    state[field]=review.adb('shell','settings','get',namespace,key)
    assert state[field]==baseline[field], field
state['density']=review.adb('shell','wm','density')
state['fontScale']=review.adb('shell','settings','get','system','font_scale')
assert 'Override' not in state['density'] and float(state['fontScale'])==1
state['reversePorts']=review.adb('reverse','--list').splitlines()
assert not any('8123' in s for s in state['reversePorts'])
with socket.socket() as sock:
    state['fixtureServiceStopped']=sock.connect_ex(('127.0.0.1',8123))!=0
assert state['fixtureServiceStopped']
permission=review.adb('shell','dumpsys','package','com.google.android.marvin.talkback')
permission=next(s.strip() for s in permission.splitlines() if 'POST_NOTIFICATIONS: granted=' in s)
assert 'granted=false' in permission and 'USER_SET' not in permission and 'USER_FIXED' not in permission
state['talkBackNotifications']=permission
for _ in range(15):
    time.sleep(2)
    nodes=list(review.hierarchy().iter('node'))
    if any(n.get('content-desc') in ['Profile','Profiel','Afmelden'] for n in nodes):break
else: raise AssertionError('Clean runtime did not restore authenticated app')
state['cleanRuntimeAuthenticated']=True
state['cleanRuntimeFixtureBridgeAbsent']=True
state['credentialsOrRealAthleteContentsRecorded']=False
(here/'device-cleanup.json').write_text(json.dumps(state,indent=2)+'\n')
print('Accepted TalkBack evidence recorded; clean authenticated runtime and emulator restoration verified.')
