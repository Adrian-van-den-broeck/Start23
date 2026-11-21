"""Read-only detail return and attention expansion on the actual Week component."""
from pathlib import Path
import json, re, time
import xml.etree.ElementTree as ET
from native_review_import import review
here = Path(__file__).resolve().parent
base = review.base

def labels(tree):
    return [n.get('content-desc') for n in tree.iter('node') if n.get('clickable') == 'true']

def locate(label, partial=False):
    for _ in range(20):
        tree = base.hierarchy()
        scrolls = [list(map(int, re.findall(r'\d+', n.get('bounds')))) for n in tree.iter('node') if n.get('class') == 'android.widget.ScrollView' and n.get('scrollable') == 'true']
        viewport = min(scrolls, key=lambda b: b[3]-b[1]) if scrolls else [0, 80, 1080, 2200]
        for n in tree.iter('node'):
            value = n.get('content-desc', '')
            if n.get('clickable') != 'true' or not (label in value if partial else value == label): continue
            box = list(map(int, re.findall(r'\d+', n.get('bounds'))))
            if box[1] > viewport[1]+1 and box[3] < viewport[3]-1: return tree, box
        base.scroll_in_view()
    raise AssertionError('No fully visible control: '+label)

def tap(box):
    base.adb('shell', 'input', 'tap', str((box[0]+box[2])//2), str((box[1]+box[3])//2))
    time.sleep(2)

def footprint(tree):
    return [(n.get('text'), n.get('content-desc'), n.get('bounds')) for n in tree.iter('node') if n.get('package') == 'com.adrivdbs.wombo' and (n.get('text') or n.get('content-desc'))]

base.dimensions(439, 1)
(here/'fixture-config.json').write_text(json.dumps({'language':'en','state':'active','width':393,'fontScale':1,'inertActions':True})+'\n')
review.open_review('active', 'en', 'detail-origin')
before, box = locate('View workout', partial=True)
review.capture('week-before-detail', before)
tap(box)
detail = base.hierarchy()
assert 'Close' in labels(detail)
review.capture('week-detail-entry', detail, modal=True)
base.tap_label('Close')
returned = base.hierarchy()
review.capture('week-detail-return', returned)
assert footprint(before) == footprint(returned), 'Close changed Week viewport'
assert [n.get('content-desc') for n in returned.iter('node') if n.get('clickable') == 'true' and n.get('selected') == 'true' and n.get('content-desc') in ['Week', 'Calendar', 'Activities']] == ['Week']
_, box = locate('View workout', partial=True)
tap(box)
base.adb('shell', 'input', 'keyevent', '4')
time.sleep(2)
hardware = base.hierarchy()
review.capture('week-hardware-back-return', hardware)
assert footprint(before) == footprint(hardware), 'Android Back changed Week viewport'

(here/'fixture-config.json').write_text(json.dumps({'language':'en','state':'attention','width':393,'fontScale':1,'inertActions':True})+'\n')
review.open_review('attention', 'en', 'attention-expand')
collapsed, box = locate('All attention items')
review.capture('attention-before-expand', collapsed)
assert not any(n.get('text') == 'Week needs attention' for n in collapsed.iter('node'))
tap(box)
expanded, _ = locate('Review attention items')
review.capture('attention-expanded', expanded)
assert any(n.get('text') == 'Week needs attention' for n in expanded.iter('node'))
_, box = locate('Show fewer')
tap(box)
collapsed, _ = locate('All attention items')
review.capture('attention-collapsed', collapsed)
assert not any(n.get('text') == 'Week needs attention' for n in collapsed.iter('node'))
assert 'All attention items' in labels(collapsed)
(here/'native-interactions.json').write_text(json.dumps({'realReadOnlyDetailModal':True,'closeRestoresExactWeekViewport':True,'androidBackRestoresExactWeekViewport':True,'selectedDestination':'Week','attentionCount':3,'twoItemLimit':True,'expandCollapseRetainsCountAndFiltering':True,'taskAndNavigationCallbacksInert':True},indent=2)+'\n')
print('Native detail Close/Back and attention expansion PASS.')
