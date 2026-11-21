"""Sequential remaining native evidence; stops at the first failed review step."""
from pathlib import Path
import subprocess,sys,json
here=Path(__file__).parent
completed=json.loads((here/'pipeline-results.json').read_text())['completed'] if (here/'pipeline-results.json').exists() else []
for mode in ['activity-titles','long-lower','pending','gate','reduced-motion','a11y-restore','talkback-enable']:
 if mode in completed:continue
 print('START '+mode,flush=True)
 subprocess.check_call([sys.executable,str(here/'native-review.py'),mode])
 completed.append(mode)
 (here/'pipeline-results.json').write_text(json.dumps({'completed':completed},indent=2)+'\n')
 print('PASS '+mode,flush=True)
