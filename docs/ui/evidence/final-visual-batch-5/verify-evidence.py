from pathlib import Path
import hashlib,json,re,subprocess
from PIL import Image
here=Path(__file__).resolve().parent
root=here.parents[3]
mobile=root/'.worktrees/wombo-ui-v2-activities/mobile'
read=lambda name:json.loads((here/name).read_text(encoding='utf-8'))
tests=read('full-mobile-tests.json');assert tests['success'] and tests['numFailedTests']==0
assert all(value==0 for value in read('command-checks.json').values())
native,scope=read('native-audit.json'),read('scope-audit.json')
assert len(native['cases'])==47 and all(t['pass'] for t in native['nativeTargets'])
assert not native['privacyFindings'] and not scope['privacyFindings']
for record in native['artifacts']:assert hashlib.sha256((here/record['path']).read_bytes()).hexdigest()==record['sha256'],record['path']
for name,digest in scope['sourceSha256'].items():assert hashlib.sha256((mobile/name).read_bytes()).hexdigest()==digest,name
assert not (mobile/'app/dev-calendar-review.tsx').exists()
cleanup=read('device-cleanup.json')
assert all(cleanup[key] for key in ['temporaryGalleryRemoved','originalRootLayoutUnchanged','physicalDensityRestored','fontScaleRestored','normalAppContextVerifiedWithoutSavingLiveContent','temporaryEmulatorCaptureFilesRemoved'])
assert cleanup['normalAuthenticatedWeekVerifiedWithoutSavingLiveContent'] or cleanup['normalExpiredSessionGateVerified']
assert read('accessibility-cleanup.json')['settingsRestored'] and read('accessibility-cleanup.json')['notificationPermissionRestored']
assert all(float(value)==0 for value in read('reduced-motion-calendar.json')['motionScales'].values())
assert all(pair['pass'] for pair in read('contrast.json')['pairs'])
for name in ['talkback-profile-focus','talkback-today-date-focus']:
 metadata=read(name+'.json');assert 'TalkBackService' in metadata['enabledServices'] and metadata['accessibilityEnabled']=='1'
 image=Image.open(here/(name+'.png')).convert('RGB')
 green=sum(1 for r,g,b in image.getdata() if g>180 and g>r*1.8 and g>b*1.8)
 assert green>100,name+' lacks actual TalkBack focus outline'
interactions=read('native-interactions.json')
assert interactions['closeRestoresExactCalendarViewport'] and interactions['androidBackRestoresExactCalendarViewport'] and interactions['secondSiblingDetailIdentity'] and interactions['activeMoveCallbackInvokedForExactOccurrence']
# Scan text artifacts without printing sensitive matches; only public fixture output belongs here.
for path in here.rglob('*'):
 if path.suffix not in ['.xml','.json','.md','.txt','.py','.log']:continue
 source=path.read_text(encoding='utf-8',errors='strict')
 assert not re.search(r'eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}|sb_secret_[A-Za-z0-9]+|sk-proj-[A-Za-z0-9]+',source),path.name+' credential-shaped text'
 assert chr(0xfffd) not in source,path.name+' invalid Unicode'
for cwd in [root,mobile]:
 result=subprocess.run(['git','diff','--check'],cwd=cwd,capture_output=True,text=True)
 assert result.returncode==0,result.stdout+result.stderr
summary={'status':'PASS','mobileTests':tests['numPassedTests'],'mobileSuites':tests['numPassedTestSuites'],'nativeCases':len(native['cases']),'matrixPngs':native['acceptedCaptures'],'totalPngs':len(list(here.glob('*.png'))),'nativeTargets':len(native['nativeTargets']),'sourceFilesChanged':len(scope['changedExisting'])+len(scope['newFiles']),'unchangedBaselineFiles':scope['unchangedFiles'],'allMappedCalendarStates':True,'allWidthsFontsLanguages':True,'controllerNavigationMapperHashesUnchanged':True,'temporaryGalleryRemoved':True,'deviceSettingsRestored':True,'minimumTextContrast':min(pair['ratio'] for pair in read('contrast.json')['pairs'] if pair['minimum']==4.5),'privacyFindings':[],'liveAuthenticatedSmokeGate':cleanup['liveAuthenticatedSmokeGate'],'normalExpiredSessionGateVerified':cleanup['normalExpiredSessionGateVerified']}
(here/'verification-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
