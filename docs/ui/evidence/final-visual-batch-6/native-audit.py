from pathlib import Path
import json,re,xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
ledger=json.loads((HERE/'case-ledger.json').read_text()); rows=[]; total=0
for case in ledger:
 prefix=f"{case['width']}-font-{case['fontScale']}-{case['language']}-{case['state']}"
 paths=list(HERE.glob(prefix+'-page-*.xml')); assert paths,prefix
 nodes=[n for path in paths for n in ET.parse(path).getroot().iter('node')]
 content=' '.join(n.get('text','')+' '+n.get('content-desc','') for n in nodes)
 ids={n.get('resource-id') for n in nodes}
 assert 'batch-6-fixture-'+case['state'] in ids
 lang=case['language']; state=case['state']
 avail=state in ['availability','none','oneDay','reuse','restrictions','availabilityBusy','incomplete']
 expected=['Start met kiezen' if lang=='nl' else 'Start choosing workouts'] if avail else ['Gekozen trainingen' if lang=='nl' else 'Chosen workouts','Verder naar inplannen' if lang=='nl' else 'Continue to placement']
 # Localized exact labels are checked below from known fixture controls.
 texts=sorted(set(n.get('text','') or n.get('content-desc','') for n in nodes))
 if avail:
  assert ('Start trainingskeuze' if lang=='nl' else 'Start choosing workouts') in content,prefix
  assert sum(1 for day in (['maandag','dinsdag','woensdag','donderdag','vrijdag','zaterdag','zondag'] if lang=='nl' else ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']) if day in content)==7,prefix
  checked={n.get('content-desc') for n in nodes if n.get('checked')=='true' and any(n.get('content-desc','').startswith(day) for day in (['maandag','dinsdag','woensdag','donderdag','vrijdag','zaterdag','zondag'] if lang=='nl' else ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']))}
  assert len(checked)==(0 if state in ['none','reuse'] else 1 if state=='oneDay' else 3),(prefix,checked)
 else:
  assert ('Verder naar inplannen' if lang=='nl' else 'Continue to placement') in content,prefix
  if state not in ['loading','unavailable','exhausted','placement']:
   assert 'selection-occurrence-public-candidate-3' in ids,prefix
  if state in ['accepted','repeated','placement','exhausted']: assert 'selection-occurrence-public-accepted-1' in ids,prefix
  if state=='repeated': assert 'selection-occurrence-public-accepted-2' in ids,prefix
  if state=='distance': assert '2500' in content and '90 min' not in content,prefix
  if state=='sparse': assert '90 min' not in content and '2500' not in content,prefix
  if state=='rpe': assert 'RPE 2-3' not in content,prefix
  if state in ['exhausted','unavailable','loading','placement']: assert not any(n.get('content-desc','').startswith(('Choose \u00b7','Kiezen \u00b7','Pass \u00b7','Overslaan \u00b7')) for n in nodes),prefix
  if state=='stale': assert 'Refresh required: the supplied draft has changed.' in content,prefix
 density=json.loads(paths[0].with_suffix('.json').read_text())['density']; dpi=int(re.findall(r'\d+',density)[-1]); scale=dpi/160
 observed={}
 for n in nodes:
  if n.get('clickable')!='true' and n.get('class') not in ['android.widget.Button','android.widget.CheckBox','android.widget.RadioButton','android.widget.EditText']: continue
  if n.get('class')=='android.widget.ScrollView': continue
  label=n.get('content-desc') or n.get('text')
  if not label: continue
  x1,y1,x2,y2=map(int,re.findall(r'-?\d+',n.get('bounds')))
  # Prefer the largest observed vertical extent to exclude scroll-edge clips.
  size=((x2-x1)/scale,(y2-y1)/scale)
  prior=observed.get(label,(0,0))
  if size[1]>prior[1]: observed[label]=size
 for label,(w,h) in observed.items(): assert w>=47.5 and h>=47.5,(prefix,label,w,h)
 total+=len(observed)
 rows.append({'case':case,'pages':len(paths),'controls':len(observed),'minimumObservedDp':min(min(s) for s in observed.values())})
result={'cases':len(rows),'controlsReviewed':total,'matrixAndStateContentPass':True,'targetsAtLeast48DpWithinPixelQuantization':True,'results':rows}
(HERE/'native-target-audit.json').write_text(json.dumps(result,indent=2)+'\n');print('Native audit:',len(rows),'cases,',total,'controls passed')
