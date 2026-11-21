"""Remove exactly the two temporary Batch 2 review modules and restore layout."""
from pathlib import Path
import hashlib, json

here = Path(__file__).resolve().parent
root = here.parents[3]
mobile = root / '.worktrees/wombo-ui-v2-activities/mobile'
original = (here / 'root-layout-before-review.txt').read_bytes()
layout = mobile / 'app/_layout.tsx'
assert layout.resolve().is_relative_to(root)
current = layout.read_bytes()
assert current.splitlines(keepends=True)[1:] == original.splitlines(keepends=True)
temporary = ['src/ui-v2/dev/ShellReviewBootstrap.ts', 'app/dev-shell-review.tsx']
for name in temporary:
    path = (mobile / name).resolve()
    assert path.is_relative_to(mobile.resolve()) and path.is_file()
layout.write_bytes(original)
for name in temporary:
    (mobile / name).unlink()
baseline = json.loads((here / 'baseline.json').read_text())
assert hashlib.sha256(layout.read_bytes()).hexdigest() == baseline['app/_layout.tsx']
assert all(not (mobile / name).exists() for name in temporary)
(here / 'source-cleanup.json').write_text(json.dumps({
    'temporaryFilesRemoved': temporary,
    'rootLayoutByteIdenticalToBaseline': True,
    'existingAcceptedDevHostsRetained': True,
}, indent=2) + '\n')
print('Temporary Batch 2 host/bridge removed; root layout restored byte-for-byte.')
