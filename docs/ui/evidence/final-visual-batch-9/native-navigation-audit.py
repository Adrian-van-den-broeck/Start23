from pathlib import Path
import json,re,xml.etree.ElementTree as ET
from PIL import Image
HERE=Path(__file__).resolve().parent
ledger=json.loads((HERE/'case-ledger.json').read_text());results=[]
for case in ledger:
    if case['state'] in ['busyRpe','busyCreate']:continue
    prefix=f"{case['width']}-font-{case['fontScale']}-{case['language']}-{case['state']}"
    for p in HERE.glob(prefix+'-page-*.xml'):
        tree=ET.parse(p).getroot();selected=[n for n in tree.iter('node') if n.get('content-desc') in ['Activities','Activiteiten','Week'] and n.get('selected')=='true']
        assert len(selected)==1,p.name
        box=list(map(int,re.findall(r'\d+',selected[0].get('bounds'))))
        im=Image.open(p.with_suffix('.png')).convert('RGB');assert box[3]<=im.height and box[1]>im.height*.65
        green=sum(1 for r,g,b in im.crop(tuple(box)).getdata() if r<80 and 50<g<140 and b<130)
        assert green>5000,(p.name,green)
        results.append({'capture':p.with_suffix('.png').name,'nativeSelectedLabel':selected[0].get('content-desc'),'actualForestPixels':green})
(HERE/'native-navigation-audit.json').write_text(json.dumps({'result':'PASS','cases':len(ledger),'capturesWithVisibleSelectedNavigation':len(results),'results':results},indent=2)+'\n');print('Visible native navigation:',len(results),'captures PASS')
