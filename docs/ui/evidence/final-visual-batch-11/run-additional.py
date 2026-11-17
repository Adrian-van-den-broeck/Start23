from pathlib import Path
import importlib.util,json
s=importlib.util.spec_from_file_location('review',Path(__file__).with_name('native-review.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
cases=[('incomplete',320,2),('boundaries',320,2),('protocol-run',393,1),('protocol-bike',393,1),('protocol-swim',393,1),('protocol-swim',320,2),('overview',320,1),('overview',360,2),('overview',393,2),('overview',412,2)]
for state,width,font in cases:r.run_case(state,width,font)
print('Additional source-backed/reflow cases complete',flush=True)
