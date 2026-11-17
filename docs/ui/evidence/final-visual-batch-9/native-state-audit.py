from pathlib import Path
import ast,json,re,xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
root=HERE.parents[3];mobile=root/'.worktrees/wombo-ui-v2-activities/mobile'
source=(mobile/'src/lib/rpe.ts').read_text(encoding='utf-8')
canonical={sport:[ast.literal_eval(line.strip().rstrip(',')) for line in re.search(r'  '+sport+r': \[([\s\S]*?)\n  \]',source).group(1).splitlines() if line.strip()] for sport in ['run','bike','swim']}
ledger=json.loads((HERE/'case-ledger.json').read_text());checks=[]
for case in ledger:
    prefix=f"{case['width']}-font-{case['fontScale']}-{case['language']}-{case['state']}"
    pages=[ET.parse(p).getroot() for p in sorted(HERE.glob(prefix+'-page-*.xml'))]
    assert pages,prefix
    nodes=[n for tree in pages for n in tree.iter('node')]
    ids={n.get('resource-id') for n in nodes}
    texts={n.get('text','') for n in nodes}|{n.get('content-desc','').removesuffix(', busy') for n in nodes}
    assert 'batch-9-end' in ids,prefix
    state=case['state'];language=case['language']
    rpe=state in ['rpe','rpeNoHR','rpeHR','selected','busyRpe','rpeError','bikeRpe','swimRpe','reminderFeedback']
    if rpe:
        sport='bike' if state=='bikeRpe' else 'swim' if state=='swimRpe' else 'run'
        save='Save RPE' if language=='en' else 'RPE opslaan'
        fully_visible={}
        for tree in pages:
            scroll=min([list(map(int,re.findall(r'\d+',n.get('bounds')))) for n in tree.iter('node') if n.get('class')=='android.widget.ScrollView'],key=lambda b:b[3]-b[1])
            for n in tree.iter('node'):
                label=n.get('content-desc','').removesuffix(', busy')
                match=re.search(r'\(RPE (\d+)\)$',label)
                if not match or not label.startswith(save+' · '):continue
                value=int(match.group(1));assert label==f'{save} · {canonical[sport][value-1]} (RPE {value})'
                assert n.get('class')=='android.widget.RadioButton'
                assert n.get('checked')==str(state=='selected' and value==7).lower()
                assert n.get('enabled')==str(state!='busyRpe').lower()
                box=list(map(int,re.findall(r'\d+',n.get('bounds'))))
                if box[1]>scroll[1]+2 and box[3]<scroll[3]-2:fully_visible[value]=label
        assert sorted(fully_visible)==list(range(1,11)),(prefix,sorted(fully_visible))
        assert save not in texts,'No extra RPE Save button'
        if state=='selected':assert ('RPE needed' if language=='en' else 'RPE nodig') in texts,'Checked score does not imply completed activity'
        checks.append({'case':prefix,'tenExactCanonicalRadioLabelsFullyVisible':True,'selectedValue':7 if state=='selected' else None,'disabled':state=='busyRpe','noAddedSave':True})
    if state in ['blocked','pending','reminderDestination']:
        add='Add activity' if language=='en' else 'Activiteit toevoegen'
        matches=[n for n in nodes if n.get('content-desc')==add and n.get('clickable')=='true']
        assert matches and all(n.get('enabled')=='false' for n in matches),prefix
        assert 'activity-pending' in ids
        checks.append({'case':prefix,'pendingBeforeBlockedAdd':True,'disabledAdd':True})
    if state=='after':
        assert 'activity-pending' not in ids
        add='Add activity' if language=='en' else 'Activiteit toevoegen'
        assert any(n.get('content-desc')==add and n.get('enabled')=='true' for n in nodes)
        checks.append({'case':prefix,'suppliedCompletedHistory':True,'allowedAddEnabled':True})
    if state=='longHistory':
        if language=='nl':
            assert 'Exact supplied public activity explanation. '*14 in texts,prefix
            checks.append({'case':prefix,'fullUnshortenedSourceExplanation':True})
        else:
            assert 'The execution differed from the plan, but does not automatically require a correction.' in texts,prefix
            checks.append({'case':prefix,'existingEnglishMapperFallbackRetained':True})
(HERE/'native-state-audit.json').write_text(json.dumps({'result':'PASS','cases':len(ledger),'checks':checks,'rpeDataSource':'unchanged src/lib/rpe.ts'},indent=2)+'\n')
print('Canonical/state checks',len(checks),'PASS')
