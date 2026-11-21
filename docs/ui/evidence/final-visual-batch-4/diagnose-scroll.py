from native_review_import import review
import re,time,json
base=review.base
base.dimensions(540,2)
(review.HERE/'fixture-config.json').write_text(json.dumps({'language':'en','state':'siblings','width':320,'fontScale':2,'inertActions':True})+'\n')
review.open_review('siblings','en','goal-diagnostic')
for i in range(8):
    base.adb('shell','input','swipe','21','1500','21','400','450')
    time.sleep(2)
    t=base.hierarchy()
    goal=next((n for n in t.iter('node') if n.get('content-desc','').startswith('Goal ')),None)
    print(i, goal.get('bounds') if goal is not None else 'goal not mounted',flush=True)
review.capture('diagnostics/sibling-bottom-diagnostic', t)

print("\n".join(line for line in base.adb("logcat", "-d", "-s", "ReactNativeJS:I", "*:S").splitlines() if "B4_SCROLL" in line),flush=True)
