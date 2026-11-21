"""Restore the emulator and verify an authenticated runtime without fixture hooks."""
from pathlib import Path
import importlib.util,json,re,subprocess,time
here=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('native_review',here/'native-review.py')
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review);base=review.base
base.adb('shell','wm','density','reset')
base.adb('shell','settings','put','system','font_scale','1.0')
if 'tcp:8123' in base.adb('reverse','--list'):
    base.adb('reverse','--remove','tcp:8123')
base.adb('shell','am','force-stop','com.adrivdbs.wombo')
base.adb('shell',"am start -a android.intent.action.VIEW -d 'wombo://expo-development-client/?url=http%3A%2F%2F127.0.0.1%3A8081' com.adrivdbs.wombo")
time.sleep(5);base.open_path('planning')
for attempt in range(40):
    tree=base.hierarchy();nodes=list(tree.iter('node'))
    selector=next((n for n in nodes if n.get('clickable')=='true' and n.get('selected')!='true'
        and any(c.get('text')=='UI V2' for c in n.iter('node'))),None)
    if selector is not None:
        a,b,c,d=map(int,re.findall(r'\d+',selector.get('bounds')))
        base.adb('shell','input','tap',str((a+c)//2),str((b+d)//2));time.sleep(3)
        continue
    labels=[n.get('content-desc') for n in nodes if n.get('clickable')=='true'
        and n.get('content-desc') in ['Week','Calendar','Activities','Kalender','Activiteiten']]
    if len(labels)==3:break
    time.sleep(2)
else:raise AssertionError('Clean authenticated root did not settle')
listeners=subprocess.check_output(['powershell','-NoProfile','-Command',
    '@(Get-NetTCPConnection -State Listen -LocalPort 8123 -ErrorAction SilentlyContinue).Count'],text=True).strip()
assert listeners=='0','Fixture service still listening'
previous=json.loads((here.parent/'final-visual-batch-2/device-cleanup.json').read_text())
result={
    'enabledServices':base.adb('shell','settings','get','secure','enabled_accessibility_services'),
    'enabled':base.adb('shell','settings','get','secure','accessibility_enabled'),
    'animator':base.adb('shell','settings','get','global','animator_duration_scale'),
    'window':base.adb('shell','settings','get','global','window_animation_scale'),
    'transition':base.adb('shell','settings','get','global','transition_animation_scale'),
    'density':base.adb('shell','wm','density'),
    'fontScale':base.adb('shell','settings','get','system','font_scale'),
    'reversePorts':base.adb('reverse','--list').splitlines(),
    'fixtureServiceStopped':True,
    'cleanRuntimeAuthenticated':True,
    'cleanRuntimeFixtureBridgeAbsent':True,
    'credentialsOrRealAthleteContentsRecorded':False,
}
for key in ['enabledServices','enabled','animator','window','transition','density','fontScale']:
    assert result[key]==previous[key],(key,result[key],previous[key])
assert not any('8123' in line for line in result['reversePorts'])
(here/'device-cleanup.json').write_text(json.dumps(result,indent=2)+'\n')
print('Emulator restored; fixture service/port removed; clean authenticated V2 root verified.')
