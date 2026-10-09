from pathlib import Path
import json,re
HERE=Path(__file__).resolve().parent
source=(HERE.parents[3]/'mobile/src/ui-v2/tokens/colors.ts').read_text()
colors=dict(re.findall(r"(\w+): '(#[A-Fa-f0-9]{6})'",source));colors.update(dict(re.findall(r"const (\w+) = '(#[A-Fa-f0-9]{6})'",source)))
for name,alias in re.findall(r"(\w+): (primarySoft|primary),",source):colors[name]=colors[alias]
colors['focus']=colors['primary']
def luminance(h):
    v=[int(h[i:i+2],16)/255 for i in (1,3,5)]
    v=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v]
    return .2126*v[0]+.7152*v[1]+.0722*v[2]
pairs=[('text','background',4.5),('text','surface',4.5),('textMuted','surface',4.5),('textMuted','background',4.5),('primary','primarySoft',4.5),('textInverse','primary',4.5),('destructive','surface',4.5),('warning','warningSoft',4.5),('destructive','destructiveSoft',4.5),('borderControl','surface',3),('focus','surface',3),('text','surfaceSubtle',4.5)]
result=[]
for fg,bg,minimum in pairs:
    a,b=sorted([luminance(colors[fg]),luminance(colors[bg])])
    ratio=(b+.05)/(a+.05);result.append({'foreground':fg,'background':bg,'ratio':ratio,'minimum':minimum,'pass':ratio>=minimum})
(HERE/'contrast.json').write_text(json.dumps({'source':'mobile/src/ui-v2/tokens/colors.ts','pairs':result},indent=2)+'\n')
assert all(x['pass'] for x in result)
print(len(result),'contrast pairs PASS')
