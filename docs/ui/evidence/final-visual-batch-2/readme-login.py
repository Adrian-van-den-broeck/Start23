"""Native app sign-in; credentials stay in memory and never enter evidence."""
from pathlib import Path
import importlib.util, re, shlex, subprocess, time
here = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('review', here / 'native-review.py')
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)

def tap(node):
    a,b,c,d = map(int,re.findall(r'\d+',node.get('bounds')))
    review.adb('shell','input','tap',str((a+c)//2),str((b+d)//2))
    time.sleep(2)

def target(label):
    return next(n for n in review.hierarchy().iter('node')
                if n.get('clickable') == 'true' and
                label in [n.get('content-desc'), n.get('text')])

tap(target('Profile'))
tap(target('Afmelden'))
raw = (here.parents[3] / 'README.md').read_bytes()
lines = raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig').splitlines()
email = next(s.split(':',1)[1].strip() for s in lines if s.startswith('Email:'))
password = next(s.split(':',1)[1].strip() for s in lines if s.startswith('Password:'))
for index,value in enumerate([email,password]):
    fields = [n for n in review.hierarchy().iter('node') if n.get('class') == 'android.widget.EditText']
    assert len(fields) == 2, 'Expected existing sign-in form'
    tap(fields[index])
    result = subprocess.run([review.ADB,'-s','emulator-5554','shell',
                             'input text '+shlex.quote(value.replace(' ','%s'))],capture_output=True)
    if result.returncode: raise RuntimeError('Native credential input failed')
    review.adb('shell','input','keyevent','4')
    time.sleep(1)
buttons = [n for n in review.hierarchy().iter('node')
           if n.get('clickable') == 'true' and 'Aanmelden' in (n.get('content-desc','')+n.get('text',''))]
assert buttons, 'Existing sign-in action unavailable'
tap(buttons[-1])
for _ in range(25):
    time.sleep(2)
    nodes = list(review.hierarchy().iter('node'))
    if not any(n.get('class')=='android.widget.EditText' for n in nodes) and any(n.get('content-desc')=='Profile' for n in nodes):
        (here/'login-review.json').write_text('{"method":"Existing native password sign-in", "account":"README Athlete A", "authenticated":true, "credentialsRecorded":false}\n')
        print('README Athlete A authenticated through the existing native sign-in form.')
        break
else: raise RuntimeError('Native sign-in did not reach the authenticated fixture shell')
