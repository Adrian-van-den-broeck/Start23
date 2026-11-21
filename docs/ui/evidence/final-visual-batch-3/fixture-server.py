"""Reuse the accepted loopback-only fixture API, with Batch 3 evidence isolation."""
from pathlib import Path
import json
here=Path(__file__).resolve().parent
root=here.parents[3]
base=root/'docs/ui/evidence/final-visual-batch-2'
source=(base/'fixture-server.py').read_text()
data=json.loads((base/'public-fixtures.json').read_text())
(here/'public-fixtures.json').write_text(json.dumps(data,indent=2)+'\n')
exec(compile(source,str(here/'fixture-server.py'),'exec'),{'__file__':str(here/'fixture-server.py')})
