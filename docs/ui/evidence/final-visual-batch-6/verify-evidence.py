from pathlib import Path
import hashlib,json,re,subprocess
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];MOBILE=ROOT/'.worktrees/wombo-ui-v2-activities/mobile'
assert not (MOBILE/'app/dev-creation-review.tsx').exists()
assert not (ROOT/'.tmp/wombo-batch6-emulator').exists()
checks=json.loads((HERE/'command-checks.json').read_text());assert all(v==0 for v in checks.values()),checks
jest=json.loads((HERE/'full-mobile-tests.json').read_text(encoding='utf-8'));assert jest['numFailedTests']==0 and jest['numPassedTests']==551 and jest['numPassedTestSuites']==62
scope=json.loads((HERE/'scope-audit.json').read_text());assert scope['protectedOwnersMappersRoutesV1TokensDependenciesUnchanged'] and not scope['privacyFindings']
for n,h in scope['sourceSha256'].items(): assert hashlib.sha256((MOBILE/n).read_bytes()).hexdigest()==h,n
ledger=json.loads((HERE/'case-ledger.json').read_text());assert len(ledger)==57,len(ledger)
for w in [320,360,393,412]:
 for f in [1,2]:
  for l in ['nl','en']:
   for s in ['availability','selection']: assert {'width':w,'fontScale':f,'language':l,'state':s} in ledger
states={c['state'] for c in ledger};assert {'none','oneDay','reuse','restrictions','availabilityBusy','incomplete','loading','unavailable','exhausted','stale','busy','skipped','accepted','repeated','placement','warning','distance','sparse','long','rpe'} <= states
native=json.loads((HERE/'native-target-audit.json').read_text());assert native['cases']==57 and native['matrixAndStateContentPass'] and native['targetsAtLeast48DpWithinPixelQuantization']
contrast=json.loads((HERE/'contrast.json').read_text());assert all(r['pass'] for r in contrast['pairs'])
interactions=json.loads((HERE/'native-interactions.json').read_text());assert len(interactions['results'])==14 and all(r['pass'] for r in interactions['results']) and not interactions['backendWrites']
a11y=json.loads((HERE/'accessibility-cleanup.json').read_text());assert a11y['settingsRestored'] and a11y['notificationPermissionRestored']
for name in ['talkback-back-focus','talkback-choose-focus']:
 im=Image.open(HERE/(name+'.png')).convert('RGB')
 box=json.loads((HERE/(name+'.json')).read_text(encoding='utf-8'))['nativeTargetBoundsBeforeTalkBack']
 # Check the focus target itself. This device's TalkBack lime is RGB 106/199/62,
 # so a red<100 heuristic incorrectly rejected the visually verified outline.
 crop=im.crop((max(0,box[0]-12),max(0,box[1]-12),min(im.width,box[2]+12),min(im.height,box[3]+12)))
 green=sum(1 for r,g,b in crop.getdata() if g>180 and r<160 and b<120 and g-r>=50);assert green>100,(name,green)
for name in ['keyboard-393-font-1','keyboard-320-font-2','reduced-motion-selection','talkback-back-focus','talkback-choose-focus']:assert (HERE/(name+'.png')).is_file(),name
for name in ['keyboard-393-font-1','keyboard-320-font-2']:
 metadata=json.loads((HERE/(name+'.json')).read_text(encoding='utf-8'));assert metadata['serial']=='emulator-5554' and metadata['nativeKeyboardShown'] and metadata['nativeInputViewShown']
visual=json.loads((HERE/'visual-review.json').read_text());assert visual['accepted'] and set(visual['sheetsReviewed'])=={p.stem for p in (HERE/'inspection').glob('*.jpg')}
cleanup=json.loads((HERE/'device-cleanup.json').read_text());assert cleanup['temporaryEmulatorStopped'] and cleanup['temporaryDataRemoved'] and cleanup['galleryRemoved']
assert cleanup['normalWeekRoot'] and cleanup['originalLanguageRestored'] and cleanup['originalVersion']=='v1' and cleanup['originalPreviewServerHealthy']
for cwd in [ROOT,MOBILE]: subprocess.run(['git','diff','--check'],cwd=cwd,check=True,capture_output=True)
manifest={p.relative_to(HERE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.rglob('*') if p.is_file() and p.name not in ['artifact-hashes.json','verification.json'] and '__pycache__' not in p.parts}
(HERE/'artifact-hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
result={'batch':6,'pass':True,'mobileTests':551,'testSuites':62,'nativeCases':57,'nativePngs':len(list(HERE.glob('*.png'))),'nativeControls':native['controlsReviewed'],'visualQualityGate':True,'mappedFamily':['S039','S040','S091'],'temporaryGalleryAndDeviceDataRemoved':True,'checks':checks,'sourceScopeProtected':True,'physicalDeviceOrReleaseApprovalClaimed':False}
(HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
