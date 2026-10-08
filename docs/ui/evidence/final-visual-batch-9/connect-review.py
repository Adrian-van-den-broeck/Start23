from pathlib import Path
import importlib.util,json,re,time,xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('review',HERE/'native-review.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
assert (HERE/'device-baseline.json').exists()
r.adb('shell','wm','density','439');r.adb('shell','settings','put','system','font_scale','1')
(HERE/'fixture-config.json').write_text(json.dumps({'width':393,'fontScale':1,'language':'nl','state':'history','build':'final-4','inertActions':True})+'\n')
r.adb('reverse','tcp:8084','tcp:8084');r.adb('shell','am','force-stop','com.adrivdbs.wombo')
r.adb('shell',"am start -a android.intent.action.VIEW -d 'wombo://expo-development-client/?url=http%3A%2F%2F127.0.0.1%3A8084' com.adrivdbs.wombo")
time.sleep(12);r.open_review('history','nl');tree=r.hierarchy();assert r.marker(tree,'history')
message='configured linking in multiple places'
if any(message in str(n.attrib) for n in tree.iter('node')):
    out=HERE/'rejected-startup-overlay-final-4';out.mkdir(exist_ok=True)
    ET.ElementTree(tree).write(out/'startup.xml',encoding='utf-8')
    r.adb('shell','screencap','-p','/sdcard/wombo-batch9.png');r.adb('pull','/sdcard/wombo-batch9.png',str(out/'startup.png'))
    controls=[]
    for parent in tree.iter('node'):
        if not any(message in str(n.attrib) for n in parent):continue
        for n in parent:
            box=list(map(int,re.findall(r'\d+',n.get('bounds'))))
            if n.get('clickable')=='true' and not n.get('content-desc') and not n.get('text') and 0<box[2]-box[0]<80 and 0<box[3]-box[1]<80:controls.append(box)
    assert len(controls)==1,'Only the inspected development toast Close control may be used'
    box=controls[0];r.adb('shell','input','tap',str((box[0]+box[2])//2),str((box[1]+box[3])//2));time.sleep(1)
    (out/'rejection.json').write_text(json.dumps({'accepted':False,'reason':'Known Expo dev-client startup duplicate-linking toast; no production navigation/log changes','visibleCloseNativeBounds':box,'dismissedThroughActualControl':True},indent=2)+'\n')
assert not any(message in str(n.attrib) or 'LogBox' in str(n.attrib) for n in r.hierarchy().iter('node'))
print('Final-4 public fixture connected; no development overlay remains')
