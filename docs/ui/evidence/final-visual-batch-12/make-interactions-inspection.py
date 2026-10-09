from pathlib import Path
from PIL import Image,ImageDraw
import json
root=Path(__file__).resolve().parent
items=sorted(root.glob('interaction-*.png'))
records=[]
for start in range(0,len(items),2):
 group=items[start:start+2]
 sheet=Image.new('RGB',(1080,1190),'#f4f4e8')
 d=ImageDraw.Draw(sheet)
 for col,path in enumerate(group):
  img=Image.open(path).convert('RGB');img.thumbnail((540,1140))
  sheet.paste(img,(col*540,50));d.text((col*540+8,12),path.stem,fill='#17372e')
 name='interaction-inspection-'+str(start//2+1)+'.jpg'
 sheet.save(root/name,quality=92)
 records.append({'file':name,'sources':[p.name for p in group]})
(root/'interaction-inspection-index.json').write_text(json.dumps(records,indent=2)+'\n')
print(str(len(records))+' interaction sheets')
