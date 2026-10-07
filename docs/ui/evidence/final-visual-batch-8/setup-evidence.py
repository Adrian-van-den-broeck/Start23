from pathlib import Path
import hashlib,json,subprocess
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
root=HERE.parents[3];work=root/'.worktrees/wombo-ui-v2-activities'
commit='70568a80c0d19a88cd6b47fe1184a16ed7b4a7a1'
assert subprocess.check_output(['git','rev-parse','feat/wombo-ui-v2-final-batch-7'],cwd=work,text=True).strip()==commit
sources={str(p.relative_to(work)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['mobile/src','mobile/app'] for p in (work/folder).rglob('*') if p.is_file()}
prior=json.loads((root/'docs/ui/evidence/final-visual-batch-7/final-source-hashes.json').read_text())['sources']
assert sources==prior
(HERE/'baseline.json').write_text(json.dumps({'baselineCommit':commit,'sourceHashes':sources},indent=2)+'\n')
refs=[p for p in (root/'docs/ui/reference-screenshots/placement').glob('*.png') if p.name.startswith(('05-','06-','07-','08-','09-','10-'))]
refs+=list((root/'docs/ui/mockups-final').glob('0[125]-*.png'))
assert len(refs)==10
(HERE/'reference-hashes.json').write_text(json.dumps({str(p.relative_to(root/'docs/ui')):hashlib.sha256(p.read_bytes()).hexdigest() for p in refs},indent=2)+'\n')
for start in range(0,len(refs),6):
    sheet=Image.new('RGB',(1440,1100),'#eeeeee');draw=ImageDraw.Draw(sheet)
    for i,p in enumerate(refs[start:start+6]):
        im=Image.open(p).convert('RGB');im.thumbnail((460,490));x=i%3*480;y=i//3*550
        draw.text((x+8,y+6),p.name,fill='black');sheet.paste(im,(x+(480-im.width)//2,y+45))
    sheet.save(HERE/f'references-{start//6+1}.jpg')
print('Accepted Batch 7 baseline:',len(sources),'sources;',len(refs),'references')
