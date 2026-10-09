from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
ROOT=Path('F:/Projecten Business/Start23/Code')
UI=ROOT/'docs/ui'
refs=sorted(p for p in (UI/'reference-screenshots/onboarding-goal').glob('*.png') if not p.name.startswith('availability'))
refs+=sorted((UI/'reference-screenshots/profile-supporting').glob('profile*.png'))
refs+=[UI/'mockups-final/04-profile-onboarding.png']
assert len(refs)==17
(HERE/'reference-hashes.json').write_text(json.dumps({str(p.relative_to(UI)):hashlib.sha256(p.read_bytes()).hexdigest() for p in refs},indent=2)+'\n')
for start in range(0,len(refs),6):
    sheet=Image.new('RGB',(1440,1160),'#eeeeee');d=ImageDraw.Draw(sheet)
    for i,p in enumerate(refs[start:start+6]):
        im=Image.open(p).convert('RGB');im.thumbnail((460,520));x=i%3*480;y=i//3*580
        d.text((x+8,y+8),p.name,fill='black');sheet.paste(im,(x+(480-im.width)//2,y+44))
    sheet.save(HERE/f'references-{start//6+1}.jpg')
print('17 immutable direct and functional references')
