from pathlib import Path
import importlib.util,json,re,time,xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
root=HERE.parents[3];mobile=root/'.worktrees/wombo-ui-v2-activities/mobile'
spec=importlib.util.spec_from_file_location('review',HERE/'native-review.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
original=json.loads((HERE/'device-baseline.json').read_text())
gallery=mobile/'app/dev-batch7-review.tsx'
assert gallery.resolve().parent==(mobile/'app').resolve()
assert gallery.read_bytes()==(HERE/'temporary-dev-batch7-review.tsx.txt').read_bytes()
# Restore the language through its established preference path before removing the fixture.
r.open_review('automatic','nl');time.sleep(2)
gallery.unlink()
density=int(re.findall(r'(?:Physical density|Override density): (\d+)',original['density'])[-1])
r.adb('shell','wm','density',str(density));r.adb('shell','settings','put','system','font_scale',original['font_scale'])
r.adb('reverse','tcp:8081','tcp:8081');r.adb('shell','am','force-stop','com.adrivdbs.wombo')
r.adb('shell',"am start -a android.intent.action.VIEW -d 'wombo://expo-development-client/?url=http%3A%2F%2F127.0.0.1%3A8081' com.adrivdbs.wombo")
time.sleep(10)
r.adb('shell',"am start -a android.intent.action.VIEW -d 'wombo:///planning' com.adrivdbs.wombo")
for _ in range(15):
    time.sleep(2)
    tree=r.hierarchy();labels={n.get('content-desc','') for n in tree.iter('node')}
    # Verify the existing root without saving any athlete text or screenshots.
    v1={'Week','Kalender','Profielmenu'}.issubset(labels)
    v2={'Week','Kalender','Activiteiten','Profiel'}.issubset(labels)
    if (v1 or v2) and not any(n.get('resource-id','').startswith('batch-7-fixture-') for n in tree.iter('node')):break
else:raise AssertionError('Normal original preview has not settled')
r.adb('reverse','--remove','tcp:8083')
r.adb('shell','rm','-f','/sdcard/wombo-batch7.xml','/sdcard/wombo-batch7.png','/sdcard/wombo-batch7-a11y.png')
data={'galleryRemoved':not gallery.exists(),'normalWeekRoot':True,'originalVersion':'v1' if v1 else 'v2','dutchLanguageRestored':True,
      'density':r.adb('shell','wm','density'),'fontScale':r.adb('shell','settings','get','system','font_scale'),'reviewTransportRemoved':True,
      'athleteDataCapturedDuringCleanup':False,'ownedDeviceScratchRemoved':True}
assert data['density']==original['density'] and data['fontScale']==original['font_scale']
(HERE/'device-cleanup.json').write_text(json.dumps(data,indent=2)+'\n')
print('Temporary route removed; original app preference, language, display and preview restored')
