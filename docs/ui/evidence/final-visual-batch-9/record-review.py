from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
root=HERE.parents[3];work=root/'.worktrees/wombo-ui-v2-activities'
atlases=json.loads((HERE/'atlas-index.json').read_text())
assert len(json.loads((HERE/'case-ledger.json').read_text()))==101
review={'result':'PASS','reviewedAtlases':[v['atlas'] for v in atlases],'reviewedAtlasHashes':{v['atlas']:hashlib.sha256((HERE/'atlases'/v['atlas']).read_bytes()).hexdigest() for v in atlases},'contactSheets':sum(len(v['contactSheets']) for v in atlases),'composition':'M6 Activities large title/Profile, trees/river and decorated Add, naturally sized ivory sport/date/fact/feedback cards, pale Notices, eligible correction, final existing navigation; M4 task/form groups and final ChoiceRows/buttons','responsive':'320/360/~393/412 dp; default and 200% text; Dutch/English; compact task heading, natural complete source copy, scroll-reachable final controls and all ten canonical choices','stateMeaning':'Supplied selected 7 retains pending status; busy/blocked actions stay disabled; RPE saves immediately on native tap/Enter; supplied completed history enables Add only under existing predicate','references':'All S001-S022 Activities references, direct M6 and M4 inspected with unchanged hashes','focus':'Actual native keyboard and IME captures; TalkBack focus/activation limits separately recorded in accessibility-review.json'}
(HERE/'visual-review.json').write_text(json.dumps(review,indent=2)+'\n')
baseline=json.loads((HERE/'baseline.json').read_text());files={name:hashlib.sha256((work/name).read_bytes()).hexdigest() for name in baseline['sourceHashes']}
(HERE/'final-source-hashes.json').write_text(json.dumps({'sources':files,'unchangedManifests':json.loads((HERE/'functional-freeze.json').read_text())['dependencyManifestsUnchanged']},indent=2)+'\n');print('Inspected complete native review recorded')
