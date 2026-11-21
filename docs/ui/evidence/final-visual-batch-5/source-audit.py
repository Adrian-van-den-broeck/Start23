"""Compare final Batch 5 sources to accepted Batch 4; protect owners and public data."""
from pathlib import Path
import hashlib, json, re, subprocess
here = Path(__file__).resolve().parent
root = here.parents[3]
mobile = root/'.worktrees/wombo-ui-v2-activities/mobile'
baseline = json.loads((here/'baseline.json').read_text())
allowed = {'src/ui-v2/components/'+f for f in ['DayHeader.tsx', 'MonthGrid.tsx', 'WeekAgenda.tsx']}
allowed.update(['src/ui-v2/screens/CalendarScreen.tsx', 'src/ui-v2/screens/CalendarScreen.test.tsx',
 'src/ui-v2/primitives/SegmentedControl.tsx', 'src/ui-v2/assets/HeaderLandscape.tsx', 'src/i18n/LanguageProvider.tsx'])
changed = [n for n, digest in baseline.items() if hashlib.sha256((mobile/n).read_bytes()).hexdigest() != digest]
assert set(changed) == allowed, changed
new = [str(p.relative_to(mobile)).replace('\\', '/') for directory in ['src', 'app'] for p in (mobile/directory).rglob('*') if p.is_file() and str(p.relative_to(mobile)).replace('\\', '/') not in baseline]
assert set(new) == {'src/ui-v2/components/CalendarRangeNavigation.tsx'}, new
manifests=json.loads((here.parent/'final-visual-batch-2/baseline.json').read_text(encoding='utf-8'))
for name in ['package.json', 'package-lock.json']:
    assert hashlib.sha256((mobile/name).read_bytes()).hexdigest() == manifests[name], name
files = [p for directory in ['src', 'app'] for p in (mobile/directory).rglob('*') if p.suffix in ['.ts', '.tsx'] and '.test.' not in p.name]
forbidden = re.compile(r'\btss\b|planned[_ -]?load|realized[_ -]?load|private[_ -]?load|service_role|SUPABASE_SECRET|OPENAI_API_KEY', re.I)
assert not [str(p) for p in files if forbidden.search(p.read_text(encoding='utf-8'))]
for name in changed+new:
    source = (mobile/name).read_text(encoding='utf-8')
    assert not any(line.rstrip() != line for line in source.splitlines()), name
    if '.test.' not in name and name != 'src/i18n/LanguageProvider.tsx':
        assert not re.search(r'adjustsFontSizeToFit|maxFontSizeMultiplier|numberOfLines|#[a-fA-F0-9]{6}|Start workout', source), name
    assert 'dev-calendar-review' not in source, name
references = json.loads((here/'reference-hashes.json').read_text())
for name, digest in references.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest() == digest, name
result = {'baselineFiles': len(baseline), 'changedExisting': changed, 'newFiles': new, 'unchangedFiles': len(baseline)-len(changed),
    'publicSourceFiles': len(files), 'privacyFindings': [], 'protectedOwnersMappersRoutesV1TokensDependenciesUnchanged': True,
    'sourceSha256': {n: hashlib.sha256((mobile/n).read_bytes()).hexdigest() for n in changed+new}, 'referencesUnchanged': True}
(here/'scope-audit.json').write_text(json.dumps(result, indent=2)+'\n')
node = "const fs=require('fs'),ts=require('./node_modules/typescript'),vm=require('vm');const c={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/ui-v2/tokens/colors.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,c);process.stdout.write(JSON.stringify(c.exports.colors));"
colors = json.loads(subprocess.check_output(['node', '-e', node], cwd=mobile, text=True))
def luminance(color):
    rgb = [int(color[i:i+2], 16)/255 for i in [1, 3, 5]]
    linear = [c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in rgb]
    return sum(c*w for c, w in zip(linear, [.2126, .7152, .0722]))
pairs = [('borderControl', 'surface'), ('primary', 'primarySoft'), ('text', 'background'), ('text', 'surface'), ('textMuted', 'surface'), ('textMuted', 'background'), ('text', 'primarySoft'), ('text', 'warningSoft'), ('textMuted', 'primarySoft'), ('textMuted', 'warningSoft'), ('primary', 'primarySoft'),
         ('textInverse', 'primary'), ('primary', 'surface'), ('primary', 'warningSoft'), ('warning', 'warningSoft')]
rows = []
for fg, bg in pairs:
    values = sorted([luminance(colors[fg]), luminance(colors[bg])])
    ratio = (values[1]+.05)/(values[0]+.05)
    rows.append({'foreground': fg, 'background': bg, 'ratio': ratio, 'minimum': 3 if fg == 'borderControl' else 4.5, 'pass': ratio >= (3 if fg == 'borderControl' else 4.5)})
# Worst-case overlapping HeaderLandscape layers, including trees; do not round.
alpha = 1
for opacity in [.10, .16, .22, .28, .28]: alpha *= 1-opacity
alpha = (1-alpha)*(1-.84)
foreground = [int(colors['primary'][i:i+2],16) for i in [1,3,5]]
background = [int(colors['background'][i:i+2],16) for i in [1,3,5]]
composite = [a*(1-alpha)+b*alpha for a,b in zip(background,foreground)]
linear = [(c/255)/12.92 if c/255 <= .04045 else ((c/255+.055)/1.055)**2.4 for c in composite]
bg_luminance = sum(c*w for c,w in zip(linear,[.2126,.7152,.0722]))
ratio = (bg_luminance+.05)/(luminance(colors['textMuted'])+.05)
rows.append({'foreground':'textMuted', 'background':'worstCaseCalendarHeaderUnderCopy', 'ratio':ratio, 'minimum':4.5, 'pass':ratio >= 4.5})
assert all(r['pass'] for r in rows)
(here/'contrast.json').write_text(json.dumps({'pairs': rows}, indent=2)+'\n')
print('Source scope, protected state owners, recursive privacy, references and contrast PASS.')
