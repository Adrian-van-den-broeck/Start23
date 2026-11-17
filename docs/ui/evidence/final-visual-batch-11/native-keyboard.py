from pathlib import Path
import importlib.util,json,time
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('review',HERE/'native-review.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
def focus(label):
 for _ in range(45):
  r.adb('shell','input','keyevent','61');time.sleep(.2);t=r.tree()
  if any(n.get('focused')=='true' and (n.get('content-desc')==label or n.get('text')==label) for n in t.iter('node')):return t
 raise AssertionError('Native keyboard focus missing: '+label)
def ime():
 out=r.adb('shell','dumpsys','input_method');return 'mInputShown=true' in out or 'isInputViewShown=true' in out
def callback():
 return next(n.get('text','') or n.get('content-desc','') for n in r.tree().iter('node') if n.get('resource-id')=='batch-11-callback')
preference=r.adb('shell','settings','get','secure','show_ime_with_hard_keyboard');results=[]
try:
 r.adb('shell','settings','put','secure','show_ime_with_hard_keyboard','1')
 r.open_case('overview');r.capture('keyboard-zones-back-focus',focus('Week'));r.adb('shell','input','keyevent','66');time.sleep(.5);assert callback()=='back';results.append({'tabEnterZonesBack':True})
 r.open_case('known');r.capture('keyboard-zone-source-focus',focus('Gemeten door arts/lab'));r.adb('shell','input','keyevent','66');time.sleep(.5);t=r.tree();assert any(n.get('content-desc')=='Gemeten door arts/lab' and n.get('checked')=='true' for n in t.iter('node'));assert not callback();results.append({'tabEnterSourceChoice':True,'noAutomaticSave':True})
 # Exercise the real nested ZoneProfile editor and its KeyboardAvoidingView, rather than just the isolated form.
 r.open_case('overview',320,2);r.tap('Waarden of route wijzigen');r.tap('Ik ken mijn waarden');r.tap('CSS');time.sleep(3);assert ime(), 'Native numeric IME did not open';r.capture('keyboard-zones-nested-css-focus')
 t=focus('Bekende waarden bewaren');assert ime();target=next(n for n in t.iter('node') if n.get('content-desc')=='Bekende waarden bewaren' and n.get('focused')=='true');b=r.bounds(target);label=next(n for n in target.iter('node') if n.get('text')=='Bekende waarden bewaren');lb=r.bounds(label);assert lb[1]>b[1] and lb[3]<b[3],'Save label clipped';r.capture('keyboard-zones-nested-save-reachable',t);assert not callback();results.append({'actualNestedZoneProfileEditor':True,'discipline':'swim','widthDp':320,'fontScale':2,'IMEVisible':True,'tabToSaveWithoutDismissingDrag':True,'fullyVisibleSaveLabel':True,'noWrites':True})
 (HERE/'keyboard-review.json').write_text(json.dumps({'pass':True,'backendWrites':False,'results':results},indent=2)+'\n');print('Native keyboard review PASS',flush=True)
finally:
 r.adb('shell','input','keyevent','4');r.adb('shell','settings','delete','secure','show_ime_with_hard_keyboard') if preference=='null' else r.adb('shell','settings','put','secure','show_ime_with_hard_keyboard',preference);restored=r.adb('shell','settings','get','secure','show_ime_with_hard_keyboard');assert restored==preference;(HERE/'keyboard-cleanup.json').write_text(json.dumps({'original':preference,'restored':restored,'overrideRestored':True},indent=2)+'\n')
