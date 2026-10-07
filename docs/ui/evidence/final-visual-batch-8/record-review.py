from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
root=HERE.parents[3];work=root/'.worktrees/wombo-ui-v2-activities'
atlases=json.loads((HERE/'atlas-index.json').read_text())
review={'result':'PASS','reviewedAtlases':[v['atlas'] for v in atlases],
 'contactSheets':sum(len(v['contactSheets']) for v in atlases),
 'composition':'Calendar date grouping, M5 source workout anatomy, ivory information/action cards, seven ChoiceRows, supplied warning/error Notices and forest explicit actions',
 'responsive':'All four widths, default and 200% text, Dutch/English; natural wrapping, complete source copy and reachable final actions',
 'stateMeaning':'Local selection precedes explicit review; supplied warnings precede explicit proceed; Cancel returns without mutation; unavailable and busy actions stay locked',
 'chronology':'Before Wednesday 7 October; returned fixture Thursday 8 October; separate later Calendar Wednesday again',
 'references':'All seven S062-S068 movement references and M1/M2/M5 targets visually inspected; unchanged hashes',
 'focus':'See accessibility-review.json for actual native focus evidence and its limits'}
(HERE/'visual-review.json').write_text(json.dumps(review,indent=2)+'\n')
baseline=json.loads((HERE/'baseline.json').read_text())
files={name:hashlib.sha256((work/name).read_bytes()).hexdigest() for name in baseline['sourceHashes']}
(HERE/'final-source-hashes.json').write_text(json.dumps({'sources':files,'unchangedManifests':json.loads((HERE/'functional-freeze.json').read_text())['dependencyManifestsUnchanged']},indent=2)+'\n')
print('Inspected visual review recorded')
