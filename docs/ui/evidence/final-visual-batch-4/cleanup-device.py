from pathlib import Path
import hashlib,json,time
from native_review_import import review
here=Path(__file__).resolve().parent
root=here.parents[3]
mobile=root/'.worktrees/wombo-ui-v2-activities/mobile'
base=review.base
base.adb('shell','wm','density','reset')
base.adb('shell','settings','put','system','font_scale','1.0')
time.sleep(5)
review.open_review('active','nl','cleanup-locale')
route=mobile/'app/dev-week-review.tsx'
assert route.resolve().parent == (mobile/'app').resolve()
assert route.read_text() == (here/'temporary-dev-week-review.tsx.txt').read_text()
route.unlink()
time.sleep(5)
base.adb('shell','am','force-stop','com.adrivdbs.wombo')
base.adb('shell',"am start -a android.intent.action.VIEW -d 'wombo://expo-development-client/?url=http%3A%2F%2F127.0.0.1%3A8081' com.adrivdbs.wombo")
time.sleep(7)
base.open_path('planning')
normal=False
for attempt in range(20):
 try:
  tree=base.hierarchy()
  nodes=list(tree.iter('node'))
  normal=not any(n.get('resource-id','').startswith('batch-4-fixture-') for n in nodes) and any(n.get('content-desc')=='Week' and n.get('selected')=='true' for n in nodes) and any(n.get('content-desc')=='Profiel' for n in nodes)
  if normal:break
 except RuntimeError:pass
 time.sleep(2)
assert normal,'Normal authenticated Dutch Week did not settle; no live content saved'
baseline=json.loads((here/'baseline.json').read_text())
density=base.adb('shell','wm','density')
font=base.adb('shell','settings','get','system','font_scale')
assert density=='Physical density: 440' and float(font)==1
layout_unchanged=hashlib.sha256((mobile/'app/_layout.tsx').read_bytes()).hexdigest()==baseline['app/_layout.tsx']
assert layout_unchanged
for name in ['wombo-shell.xml','wombo-week.png','wombo-week-accessibility.png']:
 base.adb('shell','rm','-f','/sdcard/'+name)
result={'temporaryGalleryRemoved':not route.exists(),'originalRootLayoutUnchanged':layout_unchanged,'physicalDensityRestored':density=='Physical density: 440','fontScaleRestored':float(font)==1,'density':density,'fontScale':font,'localeRestored':'nl','normalAuthenticatedWeekVerifiedWithoutSavingLiveContent':normal,'originalMetroAndEmulatorRetained':True,'backendBridgeAndAuthOverrideStarted':False,'temporaryEmulatorCaptureFilesRemoved':True}
(here/'device-cleanup.json').write_text(json.dumps(result,indent=2)+'\n')
print('Gallery removed; physical density/font/locale restored; normal authenticated Week returned without capturing live content.')
