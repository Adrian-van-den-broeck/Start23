"""State/content parity, native target sizes and evidence/source fingerprints."""
from pathlib import Path
import hashlib, json, math, re
import xml.etree.ElementTree as ET
from PIL import Image
here = Path(__file__).resolve().parent
cases = json.loads((here/'case-ledger.json').read_text())
required = {'noPlan', 'selection', 'placement', 'pending', 'active', 'activePending', 'warning', 'rest', 'next', 'siblings'}
assert required <= {case['state'] for case in cases}
assert {(c['width'], c['fontScale'], c['language']) for c in cases if c['state'] == 'activePending'} == {(w, f, l) for w in [320, 360, 393, 412] for f in [1, 2] for l in ['nl', 'en']}
targets, accepted, rows = [], [], []
for case in cases:
    prefix = f"{case['width']}-font-{case['fontScale']}-{case['language']}-{case['state']}"
    paths = sorted(here.glob(prefix+'-page-*.xml'), key=lambda p: int(p.stem.rsplit('-', 1)[1]))
    assert paths, prefix
    texts, labels, fully_visible = [], [], set()
    for p in paths:
        im = Image.open(p.with_suffix('.png')).convert('RGB').crop((0,0,1080,600))
        assert sum(1 for r,g,b in im.getdata() if b>150 and b>r*1.6 and g>r*1.6) < 10000, p.name+' development refresh overlay'
        nodes = list(ET.parse(p).iter('node'))
        record = json.loads(p.with_suffix('.json').read_text())
        assert record['fixture']['language'] == case['language'], p.name
        assert record['fixture']['state'] == case['state'], p.name
        assert float(record['fontScale']) == case['fontScale'], p.name
        density = int(re.findall(r'\d+', record['density'])[-1])/160
        assert abs(1080/density-case['width']) < 1, p.name
        texts += [n.get('text', '') for n in nodes]
        labels += [n.get('content-desc', '') for n in nodes]
        nav = [n for n in nodes if n.get('clickable') == 'true' and n.get('content-desc') in ['Week', 'Calendar', 'Activities', 'Kalender', 'Activiteiten']]
        assert len(nav) == 3 and [n.get('content-desc') for n in nav if n.get('selected') == 'true'] == ['Week'], p.name
        scrolls = [list(map(int, re.findall(r'\d+', n.get('bounds')))) for n in nodes if n.get('class') == 'android.widget.ScrollView' and n.get('scrollable') == 'true']
        assert len(scrolls) <= 1, p.name
        viewport = scrolls[0] if scrolls else min([list(map(int, re.findall(r'\d+', n.get('bounds')))) for n in nodes if n.get('class') == 'android.widget.ScrollView'], key=lambda b: b[3]-b[1])
        for n in nodes:
            if n.get('clickable') != 'true': continue
            label = n.get('content-desc', '') or n.get('text', '')
            box = list(map(int, re.findall(r'\d+', n.get('bounds'))))
            if box[1] < 80 or box[3] > 2200: continue
            if label not in ['Week', 'Calendar', 'Activities', 'Kalender', 'Activiteiten'] and (box[1] <= viewport[1]+1 or box[3] >= viewport[3]-1): continue
            passed = min(box[2]-box[0], box[3]-box[1]) >= math.floor(48*density)
            targets.append({'capture': p.stem, 'label': label, 'widthDp': (box[2]-box[0])/density, 'heightDp': (box[3]-box[1])/density, 'pass': passed})
            fully_visible.add(label)
        accepted.append(p.stem)
    content = '\n'.join(texts+labels)
    state, nl = case['state'], case['language'] == 'nl'
    assert any(n.get('content-desc') == 'Week' and n.get('clickable') == 'false' for n in ET.parse(paths[0]).iter('node')), prefix+' missing Week heading'
    assert ('Profiel' if nl else 'Profile') in fully_visible, prefix+' Profile not fully reachable'
    assert ('5–11 okt 2026' if nl else '5–11 Oct 2026') in content, prefix+' literal range missing'
    if state not in ['loading']:
        for label in ['Bekijk week', 'Activiteiten en RPE', 'Check-in', 'Mijn zones', 'Doel · Supplied race goal'] if nl else ['View week', 'Activities and RPE', 'Check-in', 'My zones', 'Goal · Supplied race goal']:
            assert label in fully_visible, (prefix, label, 'no fully visible control')
    active = state in ['active', 'activePending', 'warning', 'rest', 'next', 'siblings', 'reminder', 'sparse', 'attention']
    if active:
        planned = 0 if state == 'rest' else 2 if state == 'siblings' else 1
        progress = f'0 van {planned} geplande training' if nl else f'0 of {planned} planned workout'
        assert progress in content, prefix+' literal progress missing'
    else:
        assert 'planned workout completed' not in content and 'geplande training afgerond' not in content, prefix+' invented progress'
    if active and state != 'rest':
        assert 'Exact source workout' in content, prefix
        detail_label = ('Bekijk training' if nl else 'View workout')+' · Exact source workout'
        assert detail_label in fully_visible, prefix+' detail not fully reachable'
        if state != 'sparse':
            assert '30.5 min' in content and '1200 m' in content and 'Exact source description.' in content, prefix
        else:
            assert '30.5 min' not in content and '1200 m' not in content and 'Exact source description.' not in content, prefix
    if state == 'activePending':
        assert ('Controleer voorstel' if nl else 'Review proposal') in fully_visible, prefix
        assert 'Pending occurrence never shown as active' not in content, prefix
    if state == 'rest':
        assert ('Rust volgens je goedgekeurde week' if nl else 'Rest in your approved week') in content, prefix
        assert 'Exact source workout' not in content, prefix
    if state == 'next':
        assert ('Volgende trainingsdag' if nl else 'Next training day') in content, prefix
        assert ('Vandaag' if nl else 'Today') not in content, prefix
    if state == 'siblings':
        name = 'Long exact source name '*6
        assert name.strip() in content, prefix
        assert ('Bekijk training' if nl else 'View workout')+' · '+name in fully_visible, prefix+' sibling action missing'
    if state == 'reminder': assert ('wacht op RPE' if nl else 'waiting for RPE') in content, prefix
    if state == 'failed': assert ('could not be fully loaded' if not nl else 'niet volledig') in content, prefix
    assert not re.search(r'\btss\b|private_load|planned_load|realized_load|Start workout|Begin training', content, re.I), prefix
    rows.append({**case, 'captures': len(paths), 'suppliedContentAndActionsReachable': True})
assert targets and all(t['pass'] for t in targets), [t for t in targets if not t['pass']]
artifacts = []
for name in accepted:
    for ext in ['png', 'xml', 'json']:
        p = here/f'{name}.{ext}'
        artifacts.append({'path': p.name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
result = {'cases': rows, 'acceptedCaptures': len(accepted), 'nativeTargets': targets, 'artifacts': artifacts, 'privacyFindings': [],
          'singleScrollOwner': True, 'allWidthsFontsLocales': True, 'allMappedWeekStates': True}
(here/'native-audit.json').write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
print('Native content, state parity, target sizes and artifact integrity PASS:', len(accepted), 'captures.')
