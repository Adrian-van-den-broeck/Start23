from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,re,xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
out=HERE/'inspection';out.mkdir(exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
cases=json.loads((HERE/'case-ledger.json').read_text())
# Contact sheets are inspection aids made only from unmodified native viewports.
index=[]
for case in {(x['state'],x['width'],x['fontScale']) for x in cases}:
    state,width,scale=case;prefix=f'{width}-font-{scale}-{state}'
    shots=sorted(HERE.glob(prefix+'-page-*.png'),key=lambda p:int(p.stem.rsplit('-',1)[1]))
    for offset in range(0,len(shots),6):
        group=shots[offset:offset+6];sheet=Image.new('RGB',(1440,2126),'#e5e7e3');d=ImageDraw.Draw(sheet)
        for i,path in enumerate(group):
            x=(i%3)*480;y=(i//3)*1063
            d.text((x+8,y+8),path.stem,font=font,fill='#102d2e')
            im=Image.open(path).convert('RGB');im.thumbnail((480,1013));sheet.paste(im,(x,y+42))
        name=prefix+'-'+str(offset//6+1)+'.jpg';sheet.save(out/name,quality=88)
        index.append({'sheet':name,'sourceViewports':[p.name for p in group]})
(HERE/'inspection-index.json').write_text(json.dumps(index,indent=2)+'\n')
print(len(index),'native contact sheets')
