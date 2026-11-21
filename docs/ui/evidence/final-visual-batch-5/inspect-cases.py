"""Labeled contact sheets of complete native viewport sequences, no compositing."""
from pathlib import Path
import json, sys
from PIL import Image, ImageDraw
here = Path(__file__).resolve().parent
out = here/'inspection'
out.mkdir(exist_ok=True)
cases = json.loads((here/'case-ledger.json').read_text())
if len(sys.argv)>1:
    cases=[c for c in cases if f"{c['width']}-font-{c['fontScale']}-{c['language']}-{c['state']}".startswith(sys.argv[1])]
for case in cases:
    prefix = f"{case['width']}-font-{case['fontScale']}-{case['language']}-{case['state']}"
    for old in out.glob(prefix+'-*.jpg'):
        assert old.resolve().parent == out.resolve()
        old.unlink()
    paths = sorted(here.glob(prefix+'-page-*.png'), key=lambda p: int(p.stem.rsplit('-', 1)[1]))
    for start in range(0, len(paths), 4):
        group = paths[start:start+4]
        canvas = Image.new('RGB', (len(group)*320, 740), '#eeeeee')
        draw = ImageDraw.Draw(canvas)
        for i, path in enumerate(group):
            im = Image.open(path).convert('RGB')
            im.thumbnail((310, 695))
            canvas.paste(im, (i*320+(320-im.width)//2, 40))
            draw.text((i*320+5, 5), path.stem, fill='black')
        name = f'{prefix}-{start//4+1}.jpg'
        canvas.save(out/name, quality=90)
print('Contact sheets generated for', len(cases), 'cases.')
