from pathlib import Path
import json,re,time
from native_review_import import review
HERE=Path(__file__).resolve().parent
b=review.base;results=[]
def config(state,w=393,f=1):
 (HERE/'fixture-config.json').write_text(json.dumps({'state':state,'language':'en','width':w,'fontScale':f,'inertActions':True})+'\n')
 b.dimensions(439 if w==393 else round(1080*160/w),f);review.open_review(state,'en','interaction')
def tap(label):
 r=b.hierarchy();n=next(n for n in r.iter('node') if n.get('content-desc')==label and n.get('clickable')=='true' and n.get('enabled')=='true')
 x1,y1,x2,y2=map(int,re.findall(r'\d+',n.get('bounds')));b.adb('shell','input','tap',str((x1+x2)//2),str((y1+y2)//2));time.sleep(1)
def seek(label):
 for _ in range(40):
  r=b.hierarchy()
  targets=[n for n in r.iter('node') if n.get('content-desc')==label and n.get('clickable')=='true' and n.get('enabled')=='true']
  # A target exposed at a scroll edge can still be clipped. Scroll until its
  # entire native target is available rather than tapping the gesture inset.
  for n in targets:
   x1,y1,x2,y2=map(int,re.findall(r'\d+',n.get('bounds')))
   if y1>=70 and y2<=2210 and y2-y1>=132:return
  b.adb('shell','input','swipe','22','1820','22','700','450');time.sleep(.6)
 raise AssertionError('Missing target '+label)
def action(expected,name):
 r=b.hierarchy();assert any(n.get('resource-id')=='batch-6-action-'+expected for n in r.iter('node')),expected
 review.capture(name,r);results.append({'case':name,'exactCallback':expected,'pass':True})
for state,actionKey,label in [('repeated','accept','Choose \u00b7 RUN-013 \u00b7 Wisselduur'),('repeated','pass','Pass \u00b7 RUN-013 \u00b7 Wisselduur'),('skipped','undo','Undo'),('skipped','reset_passed','Reset passed workouts')]:
 config(state);seek(label);tap(label);action(actionKey+'-public-candidate-3','interaction-'+actionKey)
config('placement');seek('Continue to placement');tap('Continue to placement');action('continue','interaction-continue')
config('oneDay');seek('Start choosing workouts');tap('Start choosing workouts');action('create-2026-10-12-2-false','interaction-one-day-create')
config('availability');seek('Tuesday \u00b7 13 October');tap('Tuesday \u00b7 13 October');action('day-1','interaction-toggle-day')
config('availability');seek('Use the same available days as last week');tap('Use the same available days as last week');action('reuse','interaction-reuse')
config('restrictions');seek('Confirmed injury \u00b7 Running');tap('Confirmed injury \u00b7 Running');action('injury-run','interaction-injury')
config('restrictions');seek('Optional alternative training \u00b7 Swimming');tap('Optional alternative training \u00b7 Swimming');action('optIn-swim','interaction-opt-in')
# Keyboard visibility is checked on both the reference width and the narrow large-text form.
for w,f in [(393,1),(320,2)]:
 config('availability',w,f)
 for _ in range(30):
  r=b.hierarchy();n=next((n for n in r.iter('node') if n.get('class')=='android.widget.EditText'),None)
  if n is not None: break
  b.adb('shell','input','swipe','22','1820','22','700','450');time.sleep(.6)
 else: raise AssertionError('Date field not reachable')
 x1,y1,x2,y2=map(int,re.findall(r'\d+',n.get('bounds')))
 b.adb('shell','input','tap',str((x1+x2)//2),str((y1+y2)//2));time.sleep(2)
 ime=b.adb('shell','dumpsys','input_method');assert 'mInputShown=true' in ime or 'mIsInputViewShown=true' in ime
 review.capture(f'keyboard-{w}-font-{f}');b.adb('shell','input','keyevent','4');time.sleep(1)
 results.append({'case':f'keyboard-{w}-font-{f}','nativeKeyboardShown':True,'pass':True})
config('busy')
r=b.hierarchy();n=next(n for n in r.iter('node') if n.get('content-desc','').startswith('Choose \u00b7'));assert n.get('enabled')=='false'
x1,y1,x2,y2=map(int,re.findall(r'\d+',n.get('bounds')));b.adb('shell','input','tap',str((x1+x2)//2),str((y1+y2)//2));time.sleep(1);action('none','interaction-busy-locked')
config('selection');tap('Back to Week');action('back','interaction-back')
(HERE/'native-interactions.json').write_text(json.dumps({'publicInertCallbacksOnly':True,'backendWrites':False,'results':results},indent=2)+'\n');print('Native callbacks and keyboard:',len(results),'passed')
