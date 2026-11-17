from pathlib import Path
import json,importlib.util,time,xml.etree.ElementTree as ET
spec=importlib.util.spec_from_file_location('review',str(Path(__file__).with_name('native-review.py')))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
results=[]
def capture_dialog(name,title):
 import datetime,subprocess
 t=r.tree();assert any(n.get('text')==title for n in t.iter('node')),title
 ET.ElementTree(t).write(r.HERE/(name+'.xml'),encoding='utf-8')
 (r.HERE/(name+'.png')).write_bytes(subprocess.check_output([r.ADB,'-s',r.SERIAL,'exec-out','screencap','-p'],timeout=25))
 (r.HERE/(name+'.json')).write_text(json.dumps({'timestampUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'fixture':json.loads((r.HERE/'fixture-config.json').read_text()),'nativeDialog':title,'density':r.adb('shell','wm','density'),'fontScale':r.adb('shell','settings','get','system','font_scale'),'provenance':'Actual native Alert from production Integrations; inert transport; no disconnect success'},indent=2)+'\n')
def text():return ' '.join(n.get('text','')+' '+n.get('content-desc','') for n in r.tree().iter('node'))
def callback():return next((n.get('text','') for n in r.tree().iter('node') if n.get('resource-id')=='batch-12-callback'),'')
def proof(name,predicate):
 assert predicate,name
 results.append({'check':name,'pass':True,'scope':'Native dispatch against inert transport, not backend persistence'})
def native_text_tap(label):
 n=next(n for n in r.tree().iter('node') if n.get('text','').lower()==label.lower() and n.get('clickable')=='true');b=r.bounds(n)
 r.adb('shell','input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2));time.sleep(.6)
r.open_case('saved',393,1);r.tap('Deze context bevestigen')
proof('Saved context confirmation dispatch retains revision/fingerprint','context-confirmation' in callback() and 'expected_revision' in callback() and '3' in callback() and 'inert-context' in callback())
r.capture('interaction-context-confirmation');r.tap('Maak planvoorstel')
proof('Proposal rejection retains confirmed context and has no approval/completion','/plan-proposals' in callback() and 'De wijziging kon niet veilig worden opgeslagen.' in text() and 'Context bevestigd' in text() and 'Voorstel goedkeuren' not in text())
r.capture('interaction-proposal-rejection')
r.open_case('connected',393,1);r.tap('Ontkoppelen')
proof('Disconnect requires explicit native confirmation','Polar ontkoppelen?' in text() and 'niet automatisch gewist' in text() and 'annuleren' in text().casefold())
capture_dialog('interaction-disconnect-confirmation','Polar ontkoppelen?');native_text_tap('Annuleren')
proof('Cancel disconnect does not issue DELETE',callback()=='')
r.open_case('sheet',393,1);r.tap('English')
proof('Existing language control updates current translations','Sign out securely' in text())
r.capture('interaction-language-english');r.tap('Nederlands')
proof('Dutch preference restores current translations','Veilig afmelden' in text())
r.capture('interaction-language-dutch');r.tap('Veilig afmelden');time.sleep(1)
proof('Sign-out callback dispatched after existing sheet dismissal',callback()=='signout' and 'Intakeprofiel' not in text())
r.capture('interaction-signout-dispatch',modal_open=False)
r.open_case('sheet',393,1);r.tap('Intakeprofiel');time.sleep(1)
proof('Profile destination callback dispatched after sheet dismissal',callback()=='profile' and 'Intakeprofiel' not in text())
r.capture('interaction-profile-dispatch',modal_open=False)
r.open_case('auth',393,1);r.fill('E-mailadres','review@example.test');r.fill('Wachtwoord','inert-only')
for n in r.tree().iter('node'):
 if n.get('class')=='android.widget.EditText' and n.get('content-desc')=='Wachtwoord':
  b=r.bounds(n);r.adb('shell','input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2));break
time.sleep(.8)
proof('Native secure password input retains password semantics',any(n.get('password')=='true' for n in r.tree().iter('node')))
proof('Android IME is visible for secure input','mInputShown=true' in r.adb('shell','dumpsys','input_method'))
r.capture('interaction-auth-keyboard');r.adb('shell','input','keyevent','4')
(r.HERE/'native-interactions.json').write_text(json.dumps({'completedCheckIn':False,'liveTransport':False,'checks':results},indent=2)+'\n')
print(str(len(results))+' native interaction checks PASS',flush=True)
