"""Check native supplied content, minimum targets, wrapping and exact origins."""
from pathlib import Path
import hashlib,json,math,re,xml.etree.ElementTree as ET
here=Path(__file__).resolve().parent
cases=json.loads((here/'case-ledger.json').read_text());assert len(cases)==22
rows=[];targets=[];accepted=[]
for case in cases:
    prefix=f"{case['width']}-font-{case['fontScale']}-{case['language']}-{case['state']}"
    paths=sorted(here.glob(prefix+'-page-*.xml'))+list(here.glob(prefix+'-reference-expanded.xml'))
    assert paths,prefix
    texts=[];seen=set()
    for p in paths:
        nodes=list(ET.parse(p).iter('node'));texts.extend(n.get('text','') for n in nodes)
        record=json.loads(p.with_suffix('.json').read_text());assert float(record['fontScale'])==case['fontScale']
        assert record['fixture']['language']==case['language']
        density=int(re.findall(r'\d+',record['density'])[-1])/160
        assert abs(1080/density-case['width'])<1
        viewports=[list(map(int,re.findall(r'\d+',n.get('bounds')))) for n in nodes if n.get('class')=='android.widget.ScrollView']
        for n in nodes:
            if n.get('clickable')!='true':continue
            label=n.get('content-desc','')+n.get('text','')
            if not any(s in label for s in ['Close','Sluiten','RPE reference','RPE-uitleg','Choose','Kiezen','Pass','Overslaan']):continue
            bounds=list(map(int,re.findall(r'\d+',n.get('bounds'))))
            # Only fully visible controls; clipped continuation rows are scrollable evidence.
            if bounds[1]<100 or bounds[3]>2200:continue
            if any(bounds[1]<=v[1]+1 or bounds[3]>=v[3]-1 for v in viewports):continue
            key=tuple(bounds)+(label,)
            if key in seen:continue
            seen.add(key)
            passed=min(bounds[2]-bounds[0],bounds[3]-bounds[1])>=math.floor(48*density)
            targets.append({'capture':p.stem,'label':label,'widthDp':(bounds[2]-bounds[0])/density,
                'heightDp':(bounds[3]-bounds[1])/density,'pass':passed})
        accepted.append(p.stem)
    value='\n'.join(texts)
    assert 'Exact source workout' in value,prefix
    assert '1200 m' in value,prefix
    if case['state']!='distance':
        assert '30.5 min' in value and 'Exact source description.' in value,prefix
    if case['state'] not in ['distance','candidate']:
        for needle in ['12.5 min','800 m','Zone 2','3–4','6–7','4 × 200 m.',
                       'Rest exactly as instructed in source.','Exact reference description.']:
            assert needle in value,(prefix,needle)
        assert any('reference-expanded' in p.stem for p in paths),prefix
    if case['state']=='distance':
        assert not any(' min' in text for text in texts),prefix
        assert 'No further session detail available' in value or 'Geen verdere opbouw beschikbaar' in value,prefix
    if case['state']=='run':
        for number in [1,4,2,3]:assert f'{number}. Source segment' in value,prefix
        assert 'Expected RPE 5' in value or 'Verwachte RPE 5' in value,prefix
    if case['state'] in ['swim','distance']:
        assert 'Cancelled' in value or 'Geannuleerd' in value,prefix
    assert not re.search(r'\btss\b|private_load|planned_load|realized_load|Start workout|Begin training',value,re.I)
    rows.append({**case,'captures':len(paths),'suppliedContentReachable':True})
assert targets and all(t['pass'] for t in targets),[t for t in targets if not t['pass']]
origins=[]
for origin,destination in [('calendar','Calendar'),('week','Week')]:
    entry=list(ET.parse(here/(origin+'-detail-entry.xml')).iter('node'))
    returned=list(ET.parse(here/(origin+'-detail-return.xml')).iter('node'))
    assert any(n.get('text')=='Exact source workout' for n in entry)
    assert not any(n.get('clickable')=='true' and n.get('content-desc') in ['Week','Calendar','Activities'] for n in entry)
    selected=[n.get('content-desc') for n in returned if n.get('clickable')=='true' and n.get('selected')=='true' and n.get('content-desc') in ['Week','Calendar','Activities']]
    assert selected==[destination],(origin,selected)
    before=list(ET.parse(here/(origin+'-before-detail.xml')).iter('node'))
    def footprint(nodes):
        # Android can toggle a decorative child Text selected flag after modal
        # dismissal. Compare selection on the actual interactive destination.
        return [(n.get('text'),n.get('content-desc'),n.get('bounds')) for n in nodes
                if n.get('text') or n.get('content-desc')]
    def destinations(nodes):
        return [(n.get('content-desc'),n.get('selected')) for n in nodes if n.get('clickable')=='true'
                and n.get('content-desc') in ['Week','Calendar','Activities']]
    assert destinations(before)==destinations(returned),origin+' destination selection changed'
    assert footprint(before)==footprint(returned),origin+' origin viewport changed'
    if origin=='calendar':
        hardware=list(ET.parse(here/'calendar-hardware-back-return.xml').iter('node'))
        assert footprint(before)==footprint(hardware),'Hardware back origin viewport changed'
        assert destinations(before)==destinations(hardware),'Hardware back destination changed'
        accepted.append('calendar-hardware-back-return')
    origins.append({'origin':origin,'exactSelectedReturn':destination,'sameContentBoundsAndScroll':True,'pass':True})
    accepted.extend([origin+'-before-detail',origin+'-detail-entry',origin+'-detail-return'])
artifacts=[]
for name in sorted(set(accepted)):
    for suffix in ['.png','.xml','.json']:
        path=here/(name+suffix);assert path.is_file()
        artifacts.append({'path':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(here/'native-audit.json').write_text(json.dumps({'cases':rows,'nativeTargets':targets,
  'targetRounding':'Integer hierarchy bounds; less than one physical pixel endpoint tolerance',
  'origins':origins,'acceptedCaptures':len(set(accepted)),'artifacts':artifacts},indent=2)+'\n')
print('Native content/targets/origin audit PASS:',len(cases),'cases;',len(set(accepted)),'captures;',len(targets),'fully visible targets.')
