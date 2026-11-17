from pathlib import Path
import json,re,xml.etree.ElementTree as E
h=Path(__file__).parent
checks=[]
def nodes(name):return list(E.parse(h/(name+'.xml')).iter('node'))
def selected(name,expected):
 ns=nodes(name);nav=[n for n in ns if n.get('clickable')=='true' and n.get('content-desc') in ['Week','Calendar','Activities','Kalender','Activiteiten']][-3:]
 assert len(nav)==3 and [n.get('content-desc') for n in nav if n.get('selected')=='true']==[expected],name
 checks.append({'capture':name,'selected':expected,'pass':True})
for name,dest in [('detail-week-return','Week'),('detail-calendar-return','Calendar'),('profile-return-calendar','Calendar'),('activity-task-return','Activities'),('activity-task-320-font-2-return','Activities'),('pending-rpe-return-activities','Activities')]:selected(name,dest)
for name in ['detail-week-open','detail-calendar-open','profile-from-calendar','onboarding-gate-calendar-deep-entry','onboarding-gate-activities-deep-entry']:
 ns=nodes(name)
 assert not [n for n in ns if n.get('clickable')=='true' and n.get('content-desc') in ['Week','Calendar','Activities']],name
 checks.append({'capture':name,'interactiveRootDestinations':0,'pass':True})
for name in ['pending-rpe-week','pending-rpe-calendar','pending-rpe-activities','pending-rpe-320-font-2-nl-week','pending-rpe-320-font-2-nl-calendar','pending-rpe-320-font-2-nl-activities']:
 ns=nodes(name)
 banner=next(n for n in ns if n.get('clickable')=='true' and ('waiting for RPE' in n.get('content-desc','') or 'wacht op RPE' in n.get('content-desc','')))
 b=list(map(int,re.findall(r'\d+',banner.get('bounds'))))
 scrolls=[list(map(int,re.findall(r'\d+',n.get('bounds')))) for n in ns if n.get('scrollable')=='true']
 assert scrolls and all(s[1]>=b[3] for s in scrolls),name
 checks.append({'capture':name,'bannerAboveScrollingContent':True,'pass':True})
for name in ['keyboard-reference','keyboard-reference-lower','keyboard-320-font-2','keyboard-320-font-2-lower']:
 record=json.loads((h/(name+'.json')).read_text());assert record['keyboard'],name
 ns=nodes(name)
 scroll=next(n for n in ns if n.get('class')=='android.widget.ScrollView')
 sb=list(map(int,re.findall(r'\d+',scroll.get('bounds'))))
 if name.endswith('lower'):
  save=next(n for n in ns if n.get('clickable')=='true' and n.get('content-desc')=='Save activity')
  b=list(map(int,re.findall(r'\d+',save.get('bounds'))));assert b[1]>=sb[1] and b[3]<=sb[3],(name,b,sb)
 checks.append({'capture':name,'keyboardOpen':True,'lowerCtaReachable':name.endswith('lower'),'pass':True})
(h/'native-flow-audit.json').write_text(json.dumps({'checks':checks,'failures':[]},indent=2)+'\n')
print('Native flow/inset checks PASS: '+str(len(checks)))
