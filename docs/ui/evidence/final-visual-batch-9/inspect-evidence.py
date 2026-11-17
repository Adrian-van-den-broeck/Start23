from pathlib import Path
import hashlib,json,re,xml.etree.ElementTree as ET
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
root=HERE.parents[3];work=root/'.worktrees/wombo-ui-v2-activities'
inspection=HERE/'inspection';inspection.mkdir(exist_ok=True)
ledger=json.loads((HERE/'case-ledger.json').read_text()) if (HERE/'case-ledger.json').exists() else []
targets=[];small=[];overlays=[];sheets=[]
for case in ledger:
    prefix=f"{case['width']}-font-{case['fontScale']}-{case['language']}-{case['state']}"
    pngs=sorted(HERE.glob(prefix+'-page-*.png'),key=lambda p:int(p.stem.rsplit('-',1)[1]))
    for start in range(0,len(pngs),4):
        sheet=Image.new('RGB',(1600,900),'#eeeeee');draw=ImageDraw.Draw(sheet)
        for i,p in enumerate(pngs[start:start+4]):
            im=Image.open(p).convert('RGB');im.thumbnail((392,830))
            draw.text((i*400+5,6),p.stem,fill='black');sheet.paste(im,(i*400+(400-im.width)//2,45))
        name=prefix+f'-{start//4+1}.jpg';sheet.save(inspection/name);sheets.append(name)
    for p in pngs:
        tree=ET.parse(p.with_suffix('.xml')).getroot()
        ids={n.get('resource-id') for n in tree.iter('node')}
        assert 'batch-9-build-final-4' in ids and 'batch-9-fixture-'+case['state'] in ids, p.name
        if any('configured linking in multiple places' in str(n.attrib) or 'LogBox' in str(n.attrib) for n in tree.iter('node')):overlays.append(p.name)
        density=int(re.findall(r'(?:Override density|Physical density): (\d+)',p.with_suffix('.json').read_text())[-1])
        im=Image.open(p).convert('RGB'); crop=im.crop((0,0,1080,600))
        blue=sum(1 for r,g,b in crop.getdata() if b>150 and b>r*1.6 and g>r*1.6)
        if blue>10000:overlays.append(p.name)
        scrolls=[list(map(int,re.findall(r'\d+',n.get('bounds')))) for n in tree.iter('node') if n.get('class')=='android.widget.ScrollView']
        if not scrolls:continue
        scroll=min(scrolls,key=lambda b:b[3]-b[1])
        for n in tree.iter('node'):
            if n.get('clickable')!='true':continue
            box=list(map(int,re.findall(r'\d+',n.get('bounds'))));x1,y1,x2,y2=box
            if y1<=scroll[1]+2 or y2>=scroll[3]-2:continue
            label=n.get('content-desc') or n.get('text')
            if not label:continue
            size=[(x2-x1)*160/density,(y2-y1)*160/density]
            item={'capture':p.name,'label':label,'dp':size};targets.append(item)
            if min(size)<47.5:small.append(item)
(HERE/'native-target-audit.json').write_text(json.dumps({'cases':len(ledger),'fullyVisibleControls':len(targets),'failures':small,'developmentOverlays':overlays},indent=2)+'\n')
baseline=json.loads((HERE/'baseline.json').read_text())['sourceHashes']
changed=[name for name,hash in baseline.items() if hashlib.sha256((work/name).read_bytes()).hexdigest()!=hash]
(HERE/'scope-audit.json').write_text(json.dumps({'baselineFiles':len(baseline),'changed':changed,'protectedUnchanged':len(baseline)-len(changed)},indent=2)+'\n')
refs=json.loads((HERE/'reference-hashes.json').read_text())
assert all(hashlib.sha256((root/'docs/ui'/name).read_bytes()).hexdigest()==hash for name,hash in refs.items())
print(json.dumps({'cases':len(ledger),'pages':sum(len(list(HERE.glob(f"{c['width']}-font-{c['fontScale']}-{c['language']}-{c['state']}-page-*.png"))) for c in ledger),'sheets':len(sheets),'targetFailures':len(small),'overlays':len(overlays),'changed':changed}))
