"""Remove precisely the temporary Batch 3 route/bridge and restore root bytes."""
from pathlib import Path
import hashlib,json
here=Path(__file__).resolve().parent;root=here.parents[3];mobile=root/'.worktrees/wombo-ui-v2-activities/mobile'
original=(here/'root-layout-before-review.txt').read_bytes();layout=mobile/'app/_layout.tsx'
assert layout.resolve().is_relative_to(root)
assert layout.read_bytes().splitlines(keepends=True)[1:]==original.splitlines(keepends=True)
names=['app/dev-workout-review.tsx','src/ui-v2/dev/WorkoutReviewBootstrap.ts']
for name in names:
    p=(mobile/name).resolve();assert p.is_relative_to(mobile.resolve()) and p.is_file()
    (here/('temporary-'+p.name+'.txt')).write_bytes(p.read_bytes())
layout.write_bytes(original)
for name in names:(mobile/name).unlink()
assert hashlib.sha256(layout.read_bytes()).hexdigest()==json.loads((here/'baseline.json').read_text())['app/_layout.tsx']
(here/'source-cleanup.json').write_text(json.dumps({'temporaryFilesRemoved':names,
  'rootLayoutByteIdenticalToBatch2':True,'acceptedEarlierDevHostsRetained':True},indent=2)+'\n')
print('Batch 3 temporary host and bridge removed; root layout restored byte-for-byte.')
