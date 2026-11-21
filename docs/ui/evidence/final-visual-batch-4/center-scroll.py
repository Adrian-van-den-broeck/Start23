from native_review_import import review
import time
base=review.base
for x in ['540','100','21']:
 base.adb('shell','input','swipe',x,'1450',x,'350','1000');time.sleep(2)
 t=base.hierarchy()
 goal=next(n for n in t.iter('node') if n.get('content-desc','').startswith('Goal '))
 print(x,goal.get('bounds'),flush=True)
review.capture('diagnostics/sibling-center-bottom',t)
