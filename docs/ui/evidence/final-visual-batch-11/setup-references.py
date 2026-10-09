from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=Path('F:/Projecten Business/Start23/Code/docs/ui')
files=sorted((ROOT/'reference-screenshots/zones-calibration').glob('*.png'))+[ROOT/'mockups-final/03-zones.png',ROOT/'mockups-final/04-profile-onboarding.png']
for start in range(0,len(files),3):
 sheet=Image.new('RGB',(1080,800),'#eeeeee');draw=ImageDraw.Draw(sheet)
 for i,p in enumerate(files[start:start+3]):
  im=Image.open(p).convert('RGB');im.thumbnail((340,730));draw.text((i*360+4,10),p.name,fill='black');sheet.paste(im,(i*360+(360-im.width)//2,46))
 sheet.save(HERE/('references-'+str(start//3+1)+'.jpg'),quality=92)
