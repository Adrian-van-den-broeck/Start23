from pathlib import Path
import json
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
OUT=HERE/'inspection';OUT.mkdir(exist_ok=True)
cases=json.loads((HERE/'case-ledger.json').read_text());index=[]
for case in cases:
 prefix=str(case['width'])+'-font-'+str(case['fontScale'])+'-'+case['state']
 files=[HERE/(prefix+'-page-'+str(i)+'.png') for i in range(case['pages'])]
 for start in range(0,len(files),3):
  sheet=Image.new('RGB',(1080,790),'#eeeeee');draw=ImageDraw.Draw(sheet)
  for i,p in enumerate(files[start:start+3]):
   im=Image.open(p).convert('RGB');im.thumbnail((344,734));x=i*360
   draw.text((x+8,8),p.stem,fill='black');sheet.paste(im,(x+(360-im.width)//2,42))
  name=prefix+'-'+str(start//3+1)+'.jpg';sheet.save(OUT/name,quality=90)
  index.append({'file':'inspection/'+name,'case':case,'pages':[p.name for p in files[start:start+3]]})
(HERE/'inspection-index.json').write_text(json.dumps(index,indent=2)+'\n')
print(str(len(index))+' contact sheets')
