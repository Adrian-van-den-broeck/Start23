from pathlib import Path
import hashlib,json,re,subprocess
HERE=Path(__file__).resolve().parent
root=HERE.parents[3];mobile=root/'.worktrees/wombo-ui-v2-activities/mobile'
assert not (mobile/'app/dev-batch8-review.tsx').exists()
commands={'jest':['npm.cmd','test','--','--watch=false','--setupFilesAfterEnv','./jest.setup.ts',str(HERE/'deterministic-proposal-fixture-date.cjs'),'--json','--outputFile='+str(HERE/'full-mobile-tests.json')],
          'typecheck':['npm.cmd','run','typecheck'],'unused':['npm.cmd','run','check:unused']}
exits={}
for name,command in commands.items():
    result=subprocess.run(command,cwd=mobile,capture_output=True,encoding='utf-8',errors='strict')
    log='\n'.join(line.rstrip() for line in (result.stdout+result.stderr).splitlines()).rstrip()+'\n'
    (HERE/(name+'.log')).write_text(log,encoding='utf-8')
    exits[name]=result.returncode;print(name,result.returncode,flush=True)
(HERE/'command-checks.json').write_text(json.dumps(exits,indent=2)+'\n');assert all(v==0 for v in exits.values())
src=(mobile/'src/ui-v2/tokens/colors.ts').read_text()
palette=dict(re.findall(r"(\w+): '(#[0-9A-Fa-f]{6})'",src))
palette.update(dict(re.findall(r"const (\w+) = '(#[0-9A-Fa-f]{6})'",src)))
def luminance(color):
    c=[int(color[i:i+2],16)/255 for i in [1,3,5]]
    c=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c]
    return sum(a*b for a,b in zip(c,[.2126,.7152,.0722]))
pairs=[('text','background',4.5),('text','surface',4.5),('textMuted','surface',4.5),('primary','primarySoft',4.5),('textInverse','primary',4.5),('textInverse','destructive',4.5),('warning','warningSoft',4.5),('destructive','destructiveSoft',4.5),('borderControl','surface',3),('text','surfaceSubtle',4.5)]
contrast=[]
for fg,bg,minimum in pairs:
    a,b=sorted([luminance(palette[fg]),luminance(palette[bg])]);ratio=(b+.05)/(a+.05)
    contrast.append({'foreground':fg,'background':bg,'ratio':ratio,'minimum':minimum,'pass':ratio>=minimum})
(HERE/'contrast.json').write_text(json.dumps({'pairs':contrast},indent=2)+'\n');assert all(v['pass'] for v in contrast)
print('Contrast',len(contrast),'pairs pass')
