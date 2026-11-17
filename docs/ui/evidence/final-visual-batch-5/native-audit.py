"""Calendar state/content parity, actual native hit targets and raw artifact hashes."""
from pathlib import Path
import hashlib,json,math,re,sys
import xml.etree.ElementTree as ET
from PIL import Image
here=Path(__file__).resolve().parent
cases=json.loads((here/'case-ledger.json').read_text(encoding='utf-8'))
partial='--partial' in sys.argv
if not partial:
 required={'week','empty','month','selected','moveEntry','cancelReturn','afterMove','calendarAfterMove','long','sparse','loading','failed','retained'}
 assert required <= {c['state'] for c in cases}
 for state in ['week','selected']:
  assert {(c['width'],c['fontScale'],c['language']) for c in cases if c['state']==state}=={(w,f,l) for w in [320,360,393,412] for f in [1,2] for l in ['nl','en']}
targets,accepted,rows=[],[],[]
for case in cases:
 prefix=f"{case['width']}-font-{case['fontScale']}-{case['language']}-{case['state']}"
 paths=sorted(here.glob(prefix+'-page-*.xml'),key=lambda p:int(p.stem.rsplit('-',1)[1]))
 assert paths,prefix
 texts,labels,ids,fully_visible=[],[],set(),set()
 day_records={}
 for path in paths:
  image=Image.open(path.with_suffix('.png')).convert('RGB').crop((0,0,1080,600))
  assert sum(1 for r,g,b in image.getdata() if b>150 and b>r*1.6 and g>r*1.6)<10000,path.name+' refreshing overlay'
  nodes=list(ET.parse(path).iter('node'))
  record=json.loads(path.with_suffix('.json').read_text(encoding='utf-8'))
  assert record['fixture']['language']==case['language'] and record['fixture']['state']==case['state'],path.name
  assert float(record['fontScale'])==case['fontScale'],path.name
  density=int(re.findall(r'\d+',record['density'])[-1])/160
  assert abs(1080/density-case['width'])<1,path.name
  texts += [n.get('text','') for n in nodes];labels += [n.get('content-desc','') for n in nodes];ids.update(n.get('resource-id','') for n in nodes)
  nav=[n for n in nodes if n.get('clickable')=='true' and n.get('content-desc') in ['Week','Calendar','Activities','Kalender','Activiteiten']][-3:]
  assert len(nav)==3 and [n.get('content-desc') for n in nav if n.get('selected')=='true']==['Kalender' if case['language']=='nl' else 'Calendar'],path.name
  scrolls=[list(map(int,re.findall(r'\d+',n.get('bounds')))) for n in nodes if n.get('class')=='android.widget.ScrollView']
  assert len([n for n in nodes if n.get('class')=='android.widget.ScrollView' and n.get('scrollable')=='true'])<=1,path.name+' scroll owner'
  viewport=min(scrolls,key=lambda b:b[3]-b[1])
  # Android exports these noninteractive test-ID containers as flat siblings.
  # Associate visible workout rectangles with their enclosing day rectangle;
  # allow the renderer's one-pixel border rounding at the right edge.
  for day_node in [n for n in nodes if n.get('resource-id','').startswith('calendar-day-')]:
   day_box=list(map(int,re.findall(r'\d+',day_node.get('bounds'))))
   bucket=day_records.setdefault(day_node.get('resource-id'),set())
   if day_box[3]<=day_box[1]:continue
   for workout_node in [n for n in nodes if n.get('resource-id','').startswith('calendar-workout-')]:
    box=list(map(int,re.findall(r'\d+',workout_node.get('bounds'))))
    if box[3]>box[1] and box[0]>=day_box[0]-2 and box[2]<=day_box[2]+2 and box[1]>=day_box[1]-2 and box[3]<=day_box[3]+2:
     bucket.add(workout_node.get('resource-id'))
  for n in nodes:
   rid=n.get('resource-id','')
   if rid.startswith('calendar-day-'):
    day_records.setdefault(rid,set()).update(child.get('resource-id','') for child in n.iter('node') if child.get('resource-id','').startswith('calendar-workout-'))
   if n.get('clickable')!='true':continue
   label=n.get('content-desc','') or n.get('text','')
   box=list(map(int,re.findall(r'\d+',n.get('bounds'))))
   if box[1]<80 or box[3]>2200:continue
   if n not in nav and (box[1]<=viewport[1]+1 or box[3]>=viewport[3]-1):continue
   passed=min(box[2]-box[0],box[3]-box[1])>=math.floor(48*density)
   targets.append({'capture':path.stem,'label':label,'widthDp':(box[2]-box[0])/density,'heightDp':(box[3]-box[1])/density,'pass':passed})
   fully_visible.add(label)
  accepted.append(path.stem)
 content='\n'.join(texts+labels)
 state,nl=case['state'],case['language']=='nl'
 assert ('Trainingskalender' if nl else 'Training calendar') in content,prefix+' title'
 assert ('Profiel' if nl else 'Profile') in fully_visible,prefix+' Profile not reachable'
 assert ('Terug naar Week' if nl else 'Back to Week') in fully_visible,prefix+' Back not reachable'
 assert ('Vandaag' if nl else 'Today') in fully_visible,prefix+' Today not reachable'
 assert ('Maand' if nl else 'Month') in fully_visible and 'Week' in fully_visible,prefix+' segments'
 month=state in ['month','selected']
 if month:
  fallback=case['width'] in [320,360] or case['fontScale']==2
  assert ('calendar-month-day-list' if fallback else 'calendar-month-grid') in ids,prefix+' responsive mode'
  assert all('calendar-date-'+date in ids for date in ['2026-09-28','2026-10-07','2026-10-18','2026-11-01']),prefix+' month dates'
  for day in range(1,32):assert any('calendar-date-2026-10-'+f'{day:02}'==rid for rid in ids),prefix+' missing date'
  assert ('Bekijk de week van deze datum' if nl else 'View this date\u2019s week') in fully_visible,prefix+' selected week action'
  assert 'calendar-selected-day' in ids,prefix+' selected detail'
  assert ('2 trainingen' if nl else '2 workouts') in content,prefix+' supplied count'
 else:
  start='2026-10-05' if state=='empty' else '2026-11-02' if state=='retained' else '2026-10-12'
  for day in range(7):
   import datetime
   date=(datetime.date.fromisoformat(start)+datetime.timedelta(days=day)).isoformat()
   assert 'calendar-day-'+date in ids,prefix+' missing '+date
 if state in ['week','selected','long','moveEntry','cancelReturn','afterMove','calendarAfterMove','retained']:
  assert 'Exact source workout' in content and '30.5 min' in content and '1200 m' in content and 'Exact source description.' in content,prefix+' missing literal summary'
  assert ('Bekijk training' if nl else 'View workout')+' \u00b7 Exact source workout' in fully_visible,prefix+' detail not reachable'
 if state in ['week','selected','long','retained']:
  name='Long exact source name '*6 if state=='long' else 'Second exact source workout'
  assert name.strip() in content,prefix+' missing sibling title'
  assert ('Bekijk training' if nl else 'View workout')+' \u00b7 '+name in fully_visible,prefix+' missing sibling action'
 if state=='sparse':
  assert '30.5 min' not in content and '1200 m' not in content and 'Exact source description.' not in content,prefix+' invented measure'
  assert 'Exact source workout' in content,prefix
 if state=='empty':
  assert ('Geen training gepland.' if nl else 'No workout planned.') in content,prefix
  assert ('Rustdag' if nl else 'Rest day') not in content,prefix+' empty is rest'
 if state in ['loading','failed']:
  assert ('Geen training gepland.' if nl else 'No workout planned.') not in content,prefix+' unknown became empty'
 if state=='loading':assert ('Laden\u2026' if nl else 'Loading\u2026') in content,prefix
 if state in ['failed','retained']:assert 'Safe fixture range error' in content,prefix
 if state=='retained':
  assert 'calendar-retained-range' in ids and ('Laatst geladen periode:' if nl else 'Last loaded period:') in content,prefix
  assert not any(value for key,value in day_records.items() if key.startswith('calendar-day-2026-11-')),prefix+' retained attached to requested range'
 if state in ['moveEntry','cancelReturn','afterMove','calendarAfterMove']:
  assert ('Verplaats ' if nl else 'Move ')+'Exact source workout' in fully_visible,prefix+' active move not reachable'
  expected='2026-10-15' if state in ['cancelReturn','afterMove'] else '2026-10-14'
  assert day_records.get('calendar-day-'+expected)=={'calendar-workout-workout-a'},prefix+' wrong authoritative location'
  assert not any('calendar-workout-workout-a' in value for key,value in day_records.items() if key!='calendar-day-'+expected),prefix+' duplicate occurrence'
 assert not re.search(r'\btss\b|private_load|planned_load|realized_load|Start workout|Begin training',content,re.I),prefix
 rows.append({**case,'captures':len(paths),'suppliedContentAndActionsReachable':True,'singleScrollOwner':True})
assert targets and all(t['pass'] for t in targets),[t for t in targets if not t['pass']]
artifacts=[]
for name in accepted:
 for ext in ['png','xml','json']:
  path=here/f'{name}.{ext}';artifacts.append({'path':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
result={'cases':rows,'acceptedCaptures':len(accepted),'nativeTargets':targets,'artifacts':artifacts,'privacyFindings':[], 'allWidthsFontsLocales':not partial,'allMappedCalendarStates':not partial}
(here/('native-audit-partial.json' if partial else 'native-audit.json')).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('Native Calendar state/content/targets PASS:',len(cases),'cases;',len(accepted),'captures;',len(targets),'targets.')
