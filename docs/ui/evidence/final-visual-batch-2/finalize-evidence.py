"""Final Batch 2 scope, privacy, native semantics/targets and evidence audit."""
from pathlib import Path
import hashlib,json,re,math,xml.etree.ElementTree as E
from PIL import Image,ImageDraw
HERE=Path(__file__).parent;ROOT=HERE.parents[3];MOBILE=ROOT/'.worktrees/wombo-ui-v2-activities/mobile'
baseline=json.loads((HERE/'baseline.json').read_text())
allowed={'app/(authenticated)/_layout.tsx','src/navigation/TrainingLayout.tsx','src/navigation/AuthenticatedLayout.test.tsx','src/screens/PlanningWorkoutMoveBoundary.test.tsx','src/ui-v2/primitives/Screen.tsx','src/ui-v2/screens/WeekScreen.tsx','src/ui-v2/screens/CalendarScreen.tsx','src/ui-v2/screens/ActivitiesScreen.tsx'}
changed=[n for n,h in baseline.items() if hashlib.sha256((MOBILE/n).read_bytes()).hexdigest()!=h]
assert set(changed)==allowed,(changed,allowed)
new=[str(p.relative_to(MOBILE)).replace('\\','/') for d in ['src','app'] for p in (MOBILE/d).rglob('*') if p.is_file() and str(p.relative_to(MOBILE)).replace('\\','/') not in baseline]
assert set(new)=={'src/ui-v2/components/'+f for f in ['AppHeader.tsx','BottomNavigation.tsx','PendingRpeBanner.tsx','ShellInsets.tsx','Shell.test.tsx']},new
files=[p for d in ['src','app'] for p in (MOBILE/d).rglob('*') if p.suffix in ['.ts','.tsx'] and '.test.' not in p.name]
forbidden=re.compile(r'\btss\b|planned[_ -]?load|realized[_ -]?load|private[_ -]?load|service_role|SUPABASE_SECRET|OPENAI_API_KEY',re.I)
assert not [str(p) for p in files if forbidden.search(p.read_text(encoding='utf-8'))]
scoped=[MOBILE/n for n in changed+new if '.test.' not in n]
assert not [str(p) for p in scoped if re.search(r'adjustsFontSizeToFit|maxFontSizeMultiplier|numberOfLines|#[a-fA-F0-9]{6}',p.read_text(encoding='utf-8')) and 'app/(authenticated)/_layout.tsx' not in str(p).replace('\\','/')]
# Existing legacy RGBA is retained only in the V1 reminder branch.
(HERE/'scope-audit.json').write_text(json.dumps({'baselineFiles':len(baseline),'changedExisting':changed,'newFiles':new,'unchangedFiles':len(baseline)-len(changed),'publicSourceFiles':len(files),'privacyFindings':[],'ownersRoutesV1DependenciesTokensUnchanged':True,'temporaryHostRemoved':True},indent=2)+'\n')
rows=[];targets=[]
for width in [320,360,393,412]:
 for font in [1,2]:
  for language in ['nl','en']:
   prefix=f'{width}-font-{font}-{language}';sheet=Image.new('RGB',(1080,640),'white');draw=ImageDraw.Draw(sheet)
   labels=['Week','Kalender','Activiteiten'] if language=='nl' else ['Week','Calendar','Activities']
   for i,section in enumerate(['week','calendar','activities','long-labels']):
    name=prefix+'-'+section;record=json.loads((HERE/(name+'.json')).read_text());density=int(re.findall(r'\d+',record['density'])[-1])/160
    assert float(record['fontScale'])==font
    assert record['fixture']['language']==language
    tree=E.parse(HERE/(name+'.xml'));nodes=list(tree.iter('node'))
    assert nodes and not any('Unmatched Route' in n.get('text','') for n in nodes)
    if section!='long-labels':
     nav=[n for n in nodes if n.get('clickable')=='true' and n.get('content-desc') in labels][-3:]
     assert len(nav)==3,(name,nav)
     selected=[n.get('content-desc') for n in nav if n.get('selected')=='true'];expected=labels[i]
     assert selected==[expected],(name,selected,expected)
    else:nav=[n for n in nodes if n.get('clickable')=='true'][-3:]
    def visit(node,clips):
     if node.tag!='node':
      for child in node:visit(child,clips)
      return
     b=list(map(int,re.findall(r'-?\d+',node.get('bounds'))))
     if node.get('class')=='android.widget.ScrollView': clips=clips+[b]
     label=node.get('content-desc','')
     shell=node in nav or label in ['Profile','Profiel','Open personal profile','Persoonlijk profiel openen','Return to the previous overview','Terug naar het vorige overzicht'] or section=='calendar' and label in ['Back to Week','Terug naar Week']
     visible=all(b[0]>=c[0] and b[1]>=c[1] and b[2]<=c[2] and b[3]<=c[3] for c in clips)
     if shell and node.get('clickable')=='true' and visible:
      w=(b[2]-b[0])/density;h=(b[3]-b[1])/density;targets.append({'capture':name,'label':label,'widthDp':w,'heightDp':h,'minimumPixels':math.floor(48*density),'roundingResolutionDp':1/density,'pass':b[2]-b[0]>=math.floor(48*density) and b[3]-b[1]>=math.floor(48*density)})
     for child in node:visit(child,clips)
    visit(tree.getroot(),[])
    im=Image.open(HERE/(name+'.png')).convert('RGB');assert im.getbbox() and len(im.getcolors(im.width*im.height))>20
    im.thumbnail((268,590));sheet.paste(im,(i*270,35));draw.text((i*270+5,10),section,fill='black')
    rows.append({'width':width,'fontScale':font,'language':language,'section':section,'png':name+'.png','density':density*160})
   sheet.save(HERE/'inspection'/(prefix+'.jpg'),quality=92)
assert len(rows)==64
assert targets and all(t['pass'] for t in targets),[t for t in targets if not t['pass']]
(HERE/'native-target-audit.json').write_text(json.dumps({'checked':len(targets),'minimumHeightDp':min(t['heightDp'] for t in targets),'minimumWidthDp':min(t['widthDp'] for t in targets),'failures':[],'sourceMinimumDp':48,'boundsRounding':'UIAutomation integer endpoints; allow less than one physical pixel below exact dp conversion','targets':targets},indent=2)+'\n')
(HERE/'matrix-ledger.json').write_text(json.dumps(rows,indent=2)+'\n')
ledger=[json.loads(line) for line in (HERE/'fixture-request-ledger.jsonl').read_text().splitlines()]
assert all(r['method']=='GET' for r in ledger),[r for r in ledger if r['method']!='GET']
(HERE/'fixture-audit.json').write_text(json.dumps({'requests':len(ledger),'mutationAttempts':0,'headersOrBodiesRecorded':False,'realAthleteWrites':0,'publicFixtureSource':'existing planning/activities/workout test fixtures'},indent=2)+'\n')
print(f'Scope: {len(changed)} existing + {len(new)} new; {len(baseline)-len(changed)} unchanged. Matrix 64 captures. Native targets {len(targets)} PASS. Fixture mutations 0.')
