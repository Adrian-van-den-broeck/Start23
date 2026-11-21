from pathlib import Path
import datetime, hashlib, json, re, subprocess, sys
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
HERE=Path(__file__).parent
ROOT=HERE.parents[3]
RUNTIME=ROOT/'.worktrees/wombo-ui-v2-activities/mobile'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
case_rows=[]
for width in [393,320]:
  for font in [1,2]:
    for language in ['nl','en']:
      for section,title in [('form',{'nl':'Formuliervelden','en':'Form fields'}),('workout',{'nl':'Trainingskaart','en':'Workout card'}),('notices',{'nl':'Meldingen','en':'Notices'}),('states',{'nl':'Bedieningsstatussen','en':'Control states'})]:
        case=f'{section}-{width}-font-{font}-{language}'
        images=sorted(HERE.glob(case+'-*.png'),key=lambda f:(0 if '-top.' in f.name else 1,f.name))
        assert len(images)==(2 if font==1 else 4),case
        top=HERE/(case+'-top.xml')
        nodes=list(ET.parse(top).iter('node'))
        assert any(n.get('text')==title[language] for n in nodes), 'Missing top title: '+case
        assert any(n.get('text','').startswith('DEV / '+language.upper()+' /') for n in nodes),case
        metadata=json.loads((HERE/(case+'-top.json')).read_text())
        assert float(metadata['fontScale'])==font,case
        effective_density=int(re.findall(r'\d+',metadata['density'])[-1])
        actual_width=1080*160/effective_density
        assert abs(actual_width-width)<1,case
        sheet=Image.new('RGB',(360*len(images),790),'white');draw=ImageDraw.Draw(sheet)
        for index,path in enumerate(images):
          im=Image.open(path).convert('RGB');assert im.size==(1080,2280),path
          assert im.convert('L').crop((40,120,1040,2200)).getextrema()[0]<100,path
          im.thumbnail((350,740));sheet.paste(im,(360*index,35));draw.text((360*index+4,4),path.stem,fill='black')
        sheet.save(HERE/('inspection-'+case+'.jpg'))
        case_rows.append({'case':case,'requestedWidth':width,'actualWidth':actual_width,'fontScale':font,'language':language,'section':section,'pngs':[path.name for path in images]})
print('PASS: 32 complete native review cases, 96 PNGs, correct titles/language/font/density, nonblank surfaces')
if '--prepare' in sys.argv: sys.exit()

baseline=json.loads((HERE/'baseline.json').read_text())
changed=[name for name,original in baseline.items() if sha(ROOT/name)!=original]
allowed=['/src/ui-v2/primitives/','/src/ui-v2/tokens/','/src/ui-v2/assets/assetColors.ts']
assert all(any(part in name.replace('\\','/') for part in allowed) for name in changed),changed
files=[p for d in [RUNTIME/'src',RUNTIME/'app'] for p in d.rglob('*') if p.suffix in ['.ts','.tsx'] and '.test.' not in p.name]
forbidden=re.compile(r'\btss\b|planned[_ -]?load|realized[_ -]?load|private[_ -]?load|service_role|SUPABASE_SECRET|OPENAI_API_KEY',re.I)
assert not [str(p) for p in files if forbidden.search(p.read_text(encoding='utf-8'))]
scoped=[p for d in [RUNTIME/'src/ui-v2/primitives',RUNTIME/'src/ui-v2/tokens'] for p in d.glob('*') if p.suffix in ['.ts','.tsx'] and '.test.' not in p.name]
hex_findings=[str(p) for p in scoped if p.name!='colors.ts' and re.search(r'#[a-fA-F0-9]{6}',p.read_text())]
clamp_findings=[str(p) for p in scoped if re.search(r'adjustsFontSizeToFit|maxFontSizeMultiplier|numberOfLines',p.read_text())]
assert not hex_findings and not clamp_findings
new=[str(p.relative_to(ROOT)) for d in [RUNTIME/'src',RUNTIME/'app'] for p in d.rglob('*') if p.is_file() and str(p.relative_to(ROOT)) not in baseline]
(HERE/'scope-audit.json').write_text(json.dumps({'baselineFileCount':len(baseline),'changedExistingFiles':changed,'newFiles':new,'unchangedProtectedFileCount':len(baseline)-len(changed),'screenOwnerAndV1FilesUnchanged':True,'dependenciesConfigUnchangedFrom1A':True,'recursivePublicSourceFilesScanned':len(files),'privacyFindings':[],'hexOutsidePalette':[],'fontClampFindings':[]},indent=2)+'\n')

# Inspect only complete visible native targets. Scrolled partial targets are
# clipped viewport intersections, not their full measured layout dimensions.
checks=[]
for row in case_rows:
  for name in row['pngs']:
    record=json.loads((HERE/Path(name).with_suffix('.json')).read_text())
    density=int(re.findall(r'\d+',record['density'])[-1])/160
    nodes=list(ET.parse(HERE/Path(name).with_suffix('.xml')).iter('node'))
    scrolls=[list(map(int,re.findall(r'-?\d+',n.get('bounds')))) for n in nodes if n.get('class')=='android.widget.ScrollView']
    sy1=max(b[1] for b in scrolls); sy2=min(b[3] for b in scrolls)
    for node in nodes:
      if node.get('clickable')!='true':continue
      x1,y1,x2,y2=map(int,re.findall(r'-?\d+',node.get('bounds')))
      if y1<=sy1 or y2>=sy2:continue
      w,h=(x2-x1)/density,(y2-y1)/density
      if not node.get('content-desc') and node.get('class')!='android.widget.EditText':continue
      checks.append({'png':name,'label':node.get('content-desc') or node.get('text'),'widthDp':w,'heightDp':h})
# Android XML rounds to physical pixels; allow one physical pixel at the edge.
failures=[r for r in checks if min(r['widthDp'],r['heightDp'])<47.7]
assert not failures,failures
(HERE/'native-target-audit.json').write_text(json.dumps({'checkedVisibleTargets':len(checks),'minWidthDp':min(r['widthDp'] for r in checks),'minHeightDp':min(r['heightDp'] for r in checks),'roundingToleranceDp':.3,'failures':failures,'targets':checks},indent=2)+'\n')
(HERE/'capture-ledger.json').write_text(json.dumps(case_rows,indent=2)+'\n')
source_hashes={str(p.relative_to(ROOT)):sha(p) for p in [*(ROOT/name for name in changed),*(ROOT/name for name in new)]}
manifest={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtimeBaseSha':'19c23d58f0b71aea01478df2306e2492a515e36e','runtimeBranch':'feat/wombo-ui-v2-activities','runtimeSourceHashes':source_hashes,'reviewCases':32,'matrixNativePngCount':96,'files':{p.name:sha(p) for p in HERE.iterdir() if p.is_file() and p.name!='evidence-manifest.json'}}
(HERE/'evidence-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('PASS: protected scope, recursive privacy, native target dimensions, source/evidence hashes')
