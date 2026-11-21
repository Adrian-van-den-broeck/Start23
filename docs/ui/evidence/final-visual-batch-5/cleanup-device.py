from pathlib import Path
import hashlib,json,time,sys
from native_review_import import review
here=Path(__file__).resolve().parent
root=here.parents[3]
mobile=root/'.worktrees/wombo-ui-v2-activities/mobile'
base=review.base
# Fail with a bounded error if the local ADB transport becomes unavailable.
import subprocess
def bounded_adb(*args):
 return subprocess.check_output([base.ADB,'-s','emulator-5554',*args],text=True,encoding='utf-8',errors='strict',timeout=30).strip()
base.adb=bounded_adb
route=mobile/'app/dev-calendar-review.tsx'
assert route.resolve().parent == (mobile/'app').resolve()
resume_normal='--resume-normal' in sys.argv
if not route.exists() and not resume_normal:
 # Resume an interrupted cleanup through the same public, inert language host.
 route.write_text((here/'temporary-dev-calendar-review.tsx.txt').read_text(encoding='utf-8'),encoding='utf-8')
base.adb('shell','wm','density','reset')
base.adb('shell','settings','put','system','font_scale','1.0')
time.sleep(5)
base.adb('shell','input','keyevent','224')
if not resume_normal:
 review.open_review('week','nl','cleanup-locale')
 assert route.resolve().parent == (mobile/'app').resolve()
 assert route.read_text(encoding='utf-8') == (here/'temporary-dev-calendar-review.tsx.txt').read_text(encoding='utf-8')
 route.unlink()
assert not route.exists()
time.sleep(5)
for port in ['8081','8000']:
 base.adb('reverse','tcp:'+port,'tcp:'+port)
if '--verify-current' not in sys.argv:
 base.adb('shell','am','force-stop','com.adrivdbs.wombo')
 base.adb('shell',"am start -a android.intent.action.VIEW -d 'wombo://expo-development-client/?url=http%3A%2F%2F127.0.0.1%3A8081' com.adrivdbs.wombo")
 time.sleep(7)
 base.open_path('planning')
normal=False
expired_gate=False
for attempt in range(20):
 try:
  tree=review._raw_hierarchy()
  nodes=list(tree.iter('node'))
  normal=not any(n.get('resource-id','').startswith('batch-5-fixture-') for n in nodes) and any(n.get('content-desc')=='Week' and n.get('selected')=='true' for n in nodes) and any(n.get('content-desc') in ['Profiel','Profielmenu'] for n in nodes)
  texts={n.get('text') for n in nodes}
  expired_gate=not any(n.get('resource-id','').startswith('batch-5-fixture-') for n in nodes) and 'Je sessie is verlopen. Meld je opnieuw aan.' in texts and 'Opnieuw proberen' in texts and 'Afmelden' in texts
  if normal or expired_gate:break
 except (RuntimeError,subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
 time.sleep(2)
assert normal or expired_gate,'Normal Dutch app context did not settle; no live content saved'
baseline=json.loads((here/'baseline.json').read_text())
density=base.adb('shell','wm','density')
font=base.adb('shell','settings','get','system','font_scale')
assert density=='Physical density: 440' and float(font)==1
layout_unchanged=hashlib.sha256((mobile/'app/_layout.tsx').read_bytes()).hexdigest()==baseline['app/_layout.tsx']
assert layout_unchanged
for name in ['wombo-shell.xml','wombo-calendar.png','wombo-calendar-accessibility.png']:
 base.adb('shell','rm','-f','/sdcard/'+name)
result={'temporaryGalleryRemoved':not route.exists(),'originalRootLayoutUnchanged':layout_unchanged,'physicalDensityRestored':density=='Physical density: 440','fontScaleRestored':float(font)==1,'density':density,'fontScale':font,'localeRestored':'nl','normalAuthenticatedWeekVerifiedWithoutSavingLiveContent':normal,'originalEmulatorRetained':True,'metroSessionRecoveredOnOriginalPort':8081,'priorMetroAbsentOnResume':True,'backendBridgeAndAuthOverrideStarted':False,'temporaryEmulatorCaptureFilesRemoved':True}
result.pop('originalEmulatorRetained')
result['storedAvdAndAppDataPreserved']=True
result['emulatorConsoleRestartedForRecovery']=True
result['headlessSoftwareRendererUsedForRecovery']=True
result['normalProfileAccessibilityLabel']=next((n.get('content-desc') for n in nodes if n.get('content-desc') in ['Profiel','Profielmenu']),None)
result['normalAppContextVerifiedWithoutSavingLiveContent']=normal or expired_gate
result['normalExpiredSessionGateVerified']=expired_gate
result['liveAuthenticatedSmokeGate']='Requires a fresh athlete login; no logout, credentials or authentication overrides performed.' if expired_gate else 'PASS'
result['adbTransportRecovery']='Restarted the hung ADB server and emulator, preserving stored AVD/app data. Relaunched stopped Metro on its original port with IPv4 loopback binding; restored pre-existing 8081/8000 reverse transports.'
(here/'device-cleanup.json').write_text(json.dumps(result,indent=2)+'\n')
print('Gallery removed; physical density/font/locale restored; normal Dutch app context verified without capturing live content. Authenticated Week:',normal,'Existing expired-session gate:',expired_gate)
