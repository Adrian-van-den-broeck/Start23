"""Final source/evidence integrity, credential scan and verification summary."""
from pathlib import Path
import hashlib, json, re, subprocess
import xml.etree.ElementTree as ET
from PIL import Image
here = Path(__file__).resolve().parent
root = here.parents[3]
mobile = root/'.worktrees/wombo-ui-v2-activities/mobile'
tests = json.loads((here/'full-mobile-tests.json').read_text(encoding='utf-8'))
assert tests['success'] and tests['numFailedTests'] == tests['numFailedTestSuites'] == 0
native = json.loads((here/'native-audit.json').read_text(encoding='utf-8'))
scope = json.loads((here/'scope-audit.json').read_text())
for artifact in native['artifacts']:
    assert hashlib.sha256((here/artifact['path']).read_bytes()).hexdigest() == artifact['sha256'], artifact['path']
for path, digest in scope['sourceSha256'].items():
    assert hashlib.sha256((mobile/path).read_bytes()).hexdigest() == digest, path
for directory in ['src', 'app']:
    for path in (mobile/directory).rglob('*'):
        if path.is_file(): assert 'dev-week-review' not in path.read_text(encoding='utf-8'), str(path)
interactions = json.loads((here/'native-interactions.json').read_text())
assert interactions['closeRestoresExactWeekViewport'] and interactions['androidBackRestoresExactWeekViewport'] and interactions['expandCollapseRetainsCountAndFiltering']
a11y=json.loads((here/'accessibility-cleanup.json').read_text(encoding='utf-8'))
assert a11y['settingsRestored'] and a11y['notificationPermissionRestored']
talk=json.loads((here/'talkback-profile-focus.json').read_text(encoding='utf-8'))
assert talk['enabledServices']=='com.google.android.marvin.talkback/.TalkBackService' and talk['accessibilityEnabled']=='1'
motion=json.loads((here/'reduced-motion-week.json').read_text(encoding='utf-8'))
assert all(float(value)==0 for value in motion['motionScales'].values())
profile=next(n for n in ET.parse(here/'reduced-motion-week.xml').iter('node') if n.get('content-desc')=='Profile' and n.get('clickable')=='true')
x1,y1,x2,y2=map(int,re.findall(r'\d+',profile.get('bounds')))
focus=Image.open(here/'talkback-profile-focus.png').convert('RGB').crop((x1-8,y1-8,x2+8,y2+8))
assert sum(1 for r,g,b in focus.getdata() if g>140 and g>r*1.3 and g>b*1.3)>30, 'No actual green TalkBack Profile focus'
commands=json.loads((here/'command-checks.json').read_text(encoding='utf-8'))
assert all(value==0 for value in commands.values())
device = json.loads((here/'device-cleanup.json').read_text())
assert device['temporaryGalleryRemoved'] and device['originalRootLayoutUnchanged'] and device['physicalDensityRestored'] and device['fontScaleRestored']
readme = (root/'README.md').read_bytes()
readme = readme.decode('utf-16') if readme[:2] in [b'\xff\xfe', b'\xfe\xff'] else readme.decode('utf-8-sig')
credentials = set(re.findall(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', readme))
credentials.update(value.strip(' `\r') for value in re.findall(r'(?:password|wachtwoord)\s*:\s*([^\n]+)', readme, re.I) if len(value.strip(' `\r')) >= 6)
assert credentials
for path in here.rglob('*'):
    if path.suffix not in ['.txt', '.log', '.json', '.xml', '.py', '.md']: continue
    data = path.read_bytes()
    value = data.decode('utf-16') if data[:2] in [b'\xff\xfe', b'\xfe\xff'] else data.decode('utf-8-sig')
    assert not any(credential in value for credential in credentials), path.name+' contains README credentials'
for cwd in [root, root/'.worktrees/wombo-ui-v2-activities']:
    result = subprocess.run(['git', 'diff', '--check'], cwd=cwd, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout
contrast = json.loads((here/'contrast.json').read_text())
assert all(pair['pass'] for pair in contrast['pairs'])
artifacts = []
for path in here.glob('*'):
    if path.suffix in ['.png', '.xml', '.json'] and not path.name.startswith('debug-') and path.name not in ['evidence-integrity.json', 'verification-summary.json']:
        artifacts.append({'path':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(here/'evidence-integrity.json').write_text(json.dumps({'artifacts':artifacts},indent=2)+'\n')
result = {'mobileTests':tests['numPassedTests'],'mobileSuites':tests['numPassedTestSuites'],'typeScript':'PASS','unused':'PASS',
    'publicSourceFiles':scope['publicSourceFiles'],'privacyFindings':0,'changedExistingFiles':len(scope['changedExisting']),'addedFiles':len(scope['newFiles']),
    'protectedBaselineFiles':scope['unchangedFiles'],'nativeCases':len(native['cases']),'mappedStateCaptures':native['acceptedCaptures'],
    'nativeTargetMeasurements':len(native['nativeTargets']),'contrastPairs':len(contrast['pairs']),'minimumContrast':min(pair['ratio'] for pair in contrast['pairs']),
    'nativeDetailReturn':'PASS: Close and Android Back','nativeAttentionFiltering':'PASS: count 3, default 2, expand/collapse',
    'reducedMotion':'PASS','talkBack':'PASS: actual Profile focus screenshot reviewed','credentialEvidenceScan':'PASS','manifestIntegrity':'PASS',
    'diffCheck':'PASS','sourceCleanup':'PASS','deviceCleanup':'PASS','fixtureBackendOrAuthenticationOverrides':0,
    'nativeFixtureTaskAndNavigationCallbacks':'inert; existing actual owner/navigation behavior covered by full mobile suite',
    'releaseGates':'Physical Android/iOS, signing and release artifacts remain separate'}
(here/'verification-summary.json').write_text(json.dumps(result,indent=2)+'\n')
print('Final evidence integrity, protected-source, credential and cleanup checks PASS.')
