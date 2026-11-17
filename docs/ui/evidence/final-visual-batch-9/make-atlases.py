from pathlib import Path
from PIL import Image,ImageDraw
import json
HERE=Path(__file__).resolve().parent
out=HERE/'atlases';out.mkdir(exist_ok=True)
sheets=sorted((HERE/'inspection').glob('*.jpg'))
index=[]
for start in range(0,len(sheets),4):
    sheet=Image.new('RGB',(1600,950),'#dddddd');draw=ImageDraw.Draw(sheet)
    paths=sheets[start:start+4]
    for i,p in enumerate(paths):
        im=Image.open(p);im.thumbnail((800,450))
        x=(i%2)*800;y=(i//2)*475
        draw.text((x+4,y+2),p.stem,fill='black');sheet.paste(im,(x,y+25))
    name=f'atlas-{start//4+1:02}.jpg';sheet.save(out/name)
    index.append({'atlas':name,'contactSheets':[p.name for p in paths]})
(HERE/'atlas-index.json').write_text(json.dumps(index,indent=2)+'\n')
print(len(index),'atlases',len(sheets),'complete contact sheets')
