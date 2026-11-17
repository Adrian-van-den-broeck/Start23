"""Build labeled native contact sheets, including every captured lower viewport."""
from pathlib import Path
import json, re
from PIL import Image,ImageDraw
here=Path(__file__).resolve().parent
out=here/'inspection';out.mkdir(exist_ok=True)
for case in json.loads((here/'case-ledger.json').read_text()):
    prefix=f"{case['width']}-font-{case['fontScale']}-{case['language']}-{case['state']}"
    paths=sorted(here.glob(prefix+'-page-*.png'),key=lambda p:int(re.search(r'page-(\d+)',p.stem)[1]))
    paths+=list(here.glob(prefix+'-reference-expanded.png'))
    width,height=300,655
    sheet=Image.new('RGB',(width*min(4,len(paths)),height*((len(paths)+3)//4)),'white');draw=ImageDraw.Draw(sheet)
    for i,p in enumerate(paths):
        im=Image.open(p).convert('RGB');im.thumbnail((width-4,height-24))
        x,y=(i%4)*width,(i//4)*height
        sheet.paste(im,(x,y+24));draw.text((x+4,y+4),p.stem.replace(prefix+'-',''),fill='black')
    sheet.save(out/(prefix+'.jpg'),quality=95)
print('Contact sheets:',len(list(out.glob('*.jpg'))))
