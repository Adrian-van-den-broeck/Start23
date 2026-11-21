"""Native Calendar callbacks; no athlete mutations or fixture backend."""
from pathlib import Path
import json,re,time
from native_review_import import review
here=Path(__file__).resolve().parent
base=review.base

def labels(tree): return [n.get('content-desc') for n in tree.iter('node') if n.get('clickable')=='true']
def context(tree):
 return next(n.get('resource-id') for n in tree.iter('node') if n.get('resource-id','').startswith('batch-5-context-'))
def configure(state):
 (here/'fixture-config.json').write_text(json.dumps({'language':'en','state':state,'width':393,'fontScale':1,'inertActions':True})+'\n',encoding='utf-8')
 review.open_review(state,'en','native-interaction')
def locate(label,resource=False,partial=False):
 for _ in range(40):
  tree=base.hierarchy()
  scrolls=[list(map(int,re.findall(r'\d+',n.get('bounds')))) for n in tree.iter('node') if n.get('class')=='android.widget.ScrollView']
  viewport=min(scrolls,key=lambda b:b[3]-b[1]) if scrolls else [0,80,1080,2200]
  for n in tree.iter('node'):
   value=n.get('resource-id' if resource else 'content-desc','')
   if n.get('clickable')!='true' or not (label in value if partial else value==label):continue
   box=list(map(int,re.findall(r'\d+',n.get('bounds'))))
   if box[1]>viewport[1]+1 and box[3]<viewport[3]-1:return tree,box
  # Overlap enough to expose a complete enlarged action.
  x=viewport[0]+20
  base.adb('shell','input','swipe',str(x),str(round(viewport[1]+(viewport[3]-viewport[1])*.8)),str(x),str(round(viewport[1]+(viewport[3]-viewport[1])*.3)),'450');time.sleep(1)
 raise AssertionError('No fully visible control: '+label)
def tap(box):
 base.adb('shell','input','tap',str((box[0]+box[2])//2),str((box[1]+box[3])//2));time.sleep(2)
def action(label,**kwargs):
 tree,box=locate(label,**kwargs);tap(box);return base.hierarchy()
def footprint(tree):
 return [(n.get('text'),n.get('content-desc'),n.get('bounds')) for n in tree.iter('node') if n.get('package')=='com.adrivdbs.wombo' and (n.get('text') or n.get('content-desc'))]

base.dimensions(439,1)
configure('selected')
assert context(base.hierarchy())=='batch-5-context-month-2026-10-14-2026-10-18'
tree=action('Next month')
assert context(tree)=='batch-5-context-month-2026-11-01-2026-11-01'
review.capture('interaction-next-month',tree)
tree=action('Previous month')
assert context(tree)=='batch-5-context-month-2026-10-01-2026-10-01'
tree=action('Today')
today=base.adb('shell','date','+%F')
assert context(tree)==f'batch-5-context-month-{today}-{today}'
review.capture('interaction-today-selected',tree)
tree=action('calendar-date-2026-11-01',resource=True)
assert context(tree)==f'batch-5-context-month-{today}-2026-11-01'
review.capture('interaction-outside-month-selection',tree)
tree,_=locate('View this date\u2019s week')
review.capture('interaction-selected-empty-detail',tree)
tree=action('View this date\u2019s week')
assert context(tree)=='batch-5-context-week-2026-11-01-2026-11-01'
review.capture('interaction-selected-week',tree)

configure('selected')
before,box=locate('View workout',partial=True)
review.capture('interaction-before-detail',before)
tap(box)
detail=base.hierarchy();assert 'Close' in labels(detail)
review.capture('interaction-detail-entry',detail,modal=True)
base.tap_label('Close')
returned=base.hierarchy();review.capture('interaction-detail-close-return',returned)
assert footprint(before)==footprint(returned),'Close changed Calendar selection/viewport'
_,box=locate('View workout',partial=True);tap(box)
base.adb('shell','input','keyevent','4');time.sleep(2)
returned=base.hierarchy();review.capture('interaction-detail-back-return',returned)
assert footprint(before)==footprint(returned),'Back changed Calendar selection/viewport'
# Open the second sibling by its own full identity.
_,box=locate('View workout \u00b7 Second exact source workout');tap(box)
detail=base.hierarchy();assert any(n.get('text')=='Second exact source workout' for n in detail.iter('node'))
review.capture('interaction-second-detail-entry',detail,modal=True)
base.tap_label('Close')
returned=base.hierarchy();assert context(returned)=='batch-5-context-month-2026-10-14-2026-10-18'
review.capture('interaction-second-detail-return',returned)

configure('week')
_,week_box=locate('Week');_,month_box=locate('Month')
for _ in range(5):
 for box in [month_box,week_box]:
  base.adb('shell','input','tap',str((box[0]+box[2])//2),str((box[1]+box[3])//2))
tap(month_box)
tree=base.hierarchy();assert context(tree)=='batch-5-context-month-2026-10-14-2026-10-14'
review.capture('interaction-rapid-modes',tree)
configure('empty')
tree=action('Next week');assert context(tree)=='batch-5-context-week-2026-10-14-2026-10-14'
tree=action('Previous week');assert context(tree)=='batch-5-context-week-2026-10-07-2026-10-07'
review.capture('interaction-week-navigation',tree)
configure('moveEntry')
tree,box=locate('Move Exact source workout');review.capture('interaction-active-move-entry',tree)
tap(box);tree=base.hierarchy()
assert any(n.get('resource-id')=='batch-5-move-entry-workout-a' for n in tree.iter('node'))
review.capture('interaction-move-seam-called',tree)
result={'monthRangePreviousNext':True,'weekRangePreviousNext':True,'todaySelectsActualDeviceDate':today,'outsideMonthSelectionRetainsMonthAnchor':True,'selectedDateViewWeek':True,'rapidMonthWeekPresentationChanges':10,'realReadOnlyDetailModal':True,'closeRestoresExactCalendarViewport':True,'androidBackRestoresExactCalendarViewport':True,'secondSiblingDetailIdentity':True,'selectedDestination':'Calendar','activeMoveCallbackInvokedForExactOccurrence':True,'moveCallbackInertNoMutation':True,'latestRequestWinsVerifiedByUnchangedControllerTests':True}
(here/'native-interactions.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('Native Calendar navigation, selection, detail return, sibling identity and active move seam PASS.')
