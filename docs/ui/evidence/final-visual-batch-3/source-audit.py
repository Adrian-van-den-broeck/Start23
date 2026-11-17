"""Audit Batch 3 delta, protected owners/V1/mappers, privacy and source contrast."""
from pathlib import Path
import hashlib,json,re,subprocess
here=Path(__file__).resolve().parent;root=here.parents[3];mobile=root/'.worktrees/wombo-ui-v2-activities/mobile'
baseline=json.loads((here/'baseline.json').read_text())
allowed={'src/ui-v2/components/'+f for f in ['WorkoutSummary.tsx','SportIndicator.tsx','SessionSequence.tsx','RpeIndicator.tsx']}
allowed.update(['src/ui-v2/screens/WorkoutDetailScreen.tsx','src/ui-v2/screens/WorkoutDetailScreen.test.tsx'])
changed=[n for n,h in baseline.items() if hashlib.sha256((mobile/n).read_bytes()).hexdigest()!=h]
assert set(changed)==allowed,(changed,allowed)
new=[str(p.relative_to(mobile)).replace('\\','/') for d in ['src','app'] for p in (mobile/d).rglob('*') if p.is_file() and str(p.relative_to(mobile)).replace('\\','/') not in baseline]
assert set(new)=={'src/ui-v2/components/WorkoutFacts.tsx','src/ui-v2/components/WorkoutVisuals.test.tsx'},new
previous=json.loads((here.parent/'final-visual-batch-2/baseline.json').read_text())
for name in ['package.json','package-lock.json']:
    assert hashlib.sha256((mobile/name).read_bytes()).hexdigest()==previous[name],name
files=[p for d in ['src','app'] for p in (mobile/d).rglob('*') if p.suffix in ['.ts','.tsx'] and '.test.' not in p.name]
forbidden=re.compile(r'\btss\b|planned[_ -]?load|realized[_ -]?load|private[_ -]?load|service_role|SUPABASE_SECRET|OPENAI_API_KEY',re.I)
assert not [str(p) for p in files if forbidden.search(p.read_text(encoding='utf-8'))]
for name in changed+new:
    if '.test.' in name:continue
    source=(mobile/name).read_text(encoding='utf-8')
    assert not re.search(r'adjustsFontSizeToFit|maxFontSizeMultiplier|numberOfLines|#[a-fA-F0-9]{6}|Start workout',source),name
protected=[n for n in baseline if n not in allowed]
result={'baselineFiles':len(baseline),'changedExisting':changed,'newFiles':new,'unchangedFiles':len(protected),
  'publicSourceFiles':len(files),'privacyFindings':[],'mappersSourceFixturesOwnersRoutesShellV1TokensDependenciesUnchanged':True,
  'temporaryHostRemoved':True,'sourceSha256':{n:hashlib.sha256((mobile/n).read_bytes()).hexdigest() for n in changed+new}}
(here/'scope-audit.json').write_text(json.dumps(result,indent=2)+'\n')
node="const fs=require('fs'),ts=require('./node_modules/typescript'),vm=require('vm');const c={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/ui-v2/tokens/colors.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,c);process.stdout.write(JSON.stringify(c.exports.colors));"
colors=json.loads(subprocess.check_output(['node','-e',node],cwd=mobile,text=True))
def luminance(color):
    rgb=[int(color[i:i+2],16)/255 for i in [1,3,5]]
    linear=[c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb]
    return sum(c*w for c,w in zip(linear,[.2126,.7152,.0722]))
pairs=[('text','surface'),('text','primarySoft'),('textMuted','surface'),('primary','primarySoft'),('destructive','destructiveSoft')]
rows=[]
for fg,bg in pairs:
    values=sorted([luminance(colors[fg]),luminance(colors[bg])]);ratio=(values[1]+.05)/(values[0]+.05)
    rows.append({'foreground':fg,'background':bg,'ratio':ratio,'minimum':4.5,'pass':ratio>=4.5})
for sport,palette in colors['sport'].items():
    values=sorted([luminance(palette['text']),luminance(palette['soft'])]);ratio=(values[1]+.05)/(values[0]+.05)
    rows.append({'foreground':sport,'background':sport+'.soft','ratio':ratio,'minimum':4.5,'pass':ratio>=4.5})
assert all(r['pass'] for r in rows)
(here/'contrast.json').write_text(json.dumps({'source':'existing V2 palette','pairs':rows},indent=2)+'\n')
print('Scope, preserved mappers/owners/V1, recursive privacy and eight contrast pairs PASS.')
