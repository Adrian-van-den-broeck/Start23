from pathlib import Path
import hashlib,json,re,subprocess,xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
root=HERE.parents[3];work=root/'.worktrees/wombo-ui-v2-activities'
atlases=json.loads((HERE/'atlas-index.json').read_text())
review={'result':'PASS','reviewedAtlases':[v['atlas'] for v in atlases],'contactSheets':sum(len(v['contactSheets']) for v in atlases),
 'composition':'M5 sport circles, supplied training facts, source descriptions, ivory cards and forest actions; M3 separate information/status groups',
 'responsive':'All four widths, default and 200% text, both languages; natural wrapping, individual occurrence/date and alternative controls, end actions reachable',
 'stateMeaning':'Explicit pending overview, separate active context, stale/error Notice, supplied warnings, disabled incomplete/busy actions; selection and replacement remain distinct',
 'confirmation':'Reference and 320 dp/200% native captures reviewed; supplied workout name/consequence, destructive confirmation and Keep remain readable and reachable',
 'references':'All 28 placement/proposal originals and both M3/M5 targets were inspected; S055-S061 and S075-S088 are Batch 7; movement is preserved for Batch 8'}
(HERE/'visual-review.json').write_text(json.dumps(review,indent=2)+'\n')
extra=[]
for stem in ['interaction-remove-confirmation','confirmation-320-font-2-en-page-0','confirmation-320-font-2-en-page-1']:
    metadata=json.loads((HERE/(stem+'.json')).read_text());density=int(re.findall(r'(?:Physical density|Override density): (\d+)',metadata['density'])[-1])
    tree=ET.parse(HERE/(stem+'.xml')).getroot()
    scrolls=[list(map(int,re.findall(r'\d+',n.get('bounds')))) for n in tree.iter('node') if n.get('class')=='android.widget.ScrollView']
    scroll=min(scrolls,key=lambda b:b[3]-b[1])
    for n in tree.iter('node'):
        if n.get('content-desc') not in ['Confirm removal from proposal','Keep workout']:continue
        x1,y1,x2,y2=map(int,re.findall(r'\d+',n.get('bounds')))
        if y1<=scroll[1]+2 or y2>=scroll[3]-2:continue
        size=[(x2-x1)*160/density,(y2-y1)*160/density]
        assert min(size)>=47.5
        extra.append({'capture':stem+'.png','label':n.get('content-desc'),'dp':size})
assert {v['label'] for v in extra}=={'Confirm removal from proposal','Keep workout'}
(HERE/'confirmation-target-audit.json').write_text(json.dumps({'pass':True,'controls':extra},indent=2)+'\n')
baseline=json.loads((HERE/'baseline.json').read_text())
protected=['mobile/package.json','mobile/package-lock.json','mobile/jest.config.js','mobile/tsconfig.json']
for name in protected:
    original=subprocess.check_output(['git','show',baseline['baselineCommit']+':'+name],cwd=work)
    assert original.replace(b'\r\n',b'\n')==(work/name).read_bytes().replace(b'\r\n',b'\n'),name
files={name:hashlib.sha256((work/name).read_bytes()).hexdigest() for name in baseline['sourceHashes']}
(HERE/'final-source-hashes.json').write_text(json.dumps({'sources':files,'unchangedManifests':protected},indent=2)+'\n')
print('Visual review recorded; confirmation targets and dependency manifests pass')
