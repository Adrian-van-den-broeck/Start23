"""Batch 2 native review: actual routes with public fixtures and writes disabled."""
from pathlib import Path
import datetime, json, os, re, socket, subprocess, sys, time
import xml.etree.ElementTree as ET
HERE = Path(__file__).parent
ADB = 'C:/Users/Adria/AppData/Local/Android/Sdk/platform-tools/adb.exe'
def adb(*args):
    return subprocess.check_output([ADB, '-s', 'emulator-5554', *args], text=True,encoding='utf-8',errors='replace').strip()
def hierarchy():
    result=adb('shell', 'uiautomator', 'dump', '/sdcard/wombo-shell.xml')
    if 'dumped to' not in result: raise RuntimeError('Native hierarchy unavailable; do not reuse stale XML')
    return ET.fromstring(adb('shell', 'cat', '/sdcard/wombo-shell.xml'))
def capture(name):
    for attempt in range(20):
      try:
        root=hierarchy()
        if len(list(root.iter('node'))) < 8: raise RuntimeError('Unsettled native frame')
        case=re.fullmatch(r'(\d+)-font-(\d+)-(nl|en)-(week|calendar|activities)',name)
        pending_case=re.fullmatch(r'pending-rpe(?:-320-font-2-nl)?-(week|calendar|activities)',name)
        if case or pending_case:
          language,section=(case.group(3),case.group(4)) if case else (json.loads((HERE/'fixture-config.json').read_text())['language'],pending_case.group(1))
          labels=['Week','Kalender','Activiteiten'] if language=='nl' else ['Week','Calendar','Activities']
          nav=[n for n in root.iter('node') if n.get('clickable')=='true' and n.get('content-desc') in labels][-3:]
          expected=labels[['week','calendar','activities'].index(section)]
          if len(nav)!=3 or [n.get('content-desc') for n in nav if n.get('selected')=='true']!=[expected]:
            raise RuntimeError('Root transition did not settle on '+expected)
          if pending_case and not any(n.get('clickable')=='true' and ('waiting for RPE' in n.get('content-desc','') or 'wacht op RPE' in n.get('content-desc','')) for n in root.iter('node')):
            raise RuntimeError('Pending reminder did not settle')
        if name.startswith('onboarding-gate-') and not any(n.get('class')=='android.widget.EditText' for n in root.iter('node')):
          raise RuntimeError('Onboarding form did not settle')
        break
      except RuntimeError:
        if attempt==19: raise
        time.sleep(2)
    ET.ElementTree(root).write(HERE / (name + '.xml'), encoding='utf-8')
    adb('shell', 'screencap', '-p', '/sdcard/wombo-shell.png')
    adb('pull', '/sdcard/wombo-shell.png', str(HERE / (name + '.png')))
    record = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'serial': 'emulator-5554',
      'size': adb('shell','wm','size'), 'density': adb('shell','wm','density'),
      'fontScale': adb('shell','settings','get','system','font_scale'),
      'osLocale': adb('shell','getprop','persist.sys.locale') or adb('shell','getprop','ro.product.locale'),
      'provenance': 'Real integrated routes/controllers with public DTO fixtures; temporary read-only fetch/cache bridge',
      'fixture': json.loads((HERE/'fixture-config.json').read_text()),
      'keyboard': 'mInputShown=true' in adb('shell',"dumpsys input_method | grep 'mInputShown='"),
      'accessibilityServices': adb('shell','settings','get','secure','enabled_accessibility_services'),
      'animatorScale': adb('shell','settings','get','global','animator_duration_scale')}
    (HERE/(name+'.json')).write_text(json.dumps(record,indent=2)+'\n')
    print('Captured '+name,flush=True)

def open_path(path):
    adb('shell', f"am start -a android.intent.action.VIEW -d 'wombo:///{path}' com.adrivdbs.wombo")
    time.sleep(4)
def tap_label(label, cached=None):
    for attempt in range(20):
      try:
        root=ET.parse(HERE/(cached+'.xml')).getroot() if cached else hierarchy()
        nodes=[n for n in root.iter('node') if (n.get('text')==label or n.get('content-desc')==label) and n.get('clickable')=='true' and n.get('enabled')=='true']
        if nodes:break
      except RuntimeError:pass
      time.sleep(2)
    else:raise AssertionError('No settled native target: '+label)
    n=next((n for n in nodes if n.get('clickable')=='true'),nodes[-1])
    x1,y1,x2,y2=map(int,re.findall(r'-?\d+',n.get('bounds')))
    adb('shell','input','tap',str((x1+x2)//2),str((y1+y2)//2));time.sleep(3)

def configure(language='nl',pending=False,gate=False,plan=True):
    (HERE/'fixture-config.json').write_text(json.dumps(dict(language=language,pending=pending,gate=gate,plan=plan))+'\n')
def reload(path='planning'):
    adb('reverse','tcp:8123','tcp:8123')
    adb('shell','am','force-stop','com.adrivdbs.wombo')
    adb('shell',"am start -a android.intent.action.VIEW -d 'wombo://expo-development-client/?url=http%3A%2F%2F127.0.0.1%3A8081' com.adrivdbs.wombo")
    time.sleep(7);open_path(path)
    for _ in range(20):
      try:
        root=hierarchy();text=' '.join(n.get('text','')+' '+n.get('content-desc','') for n in root.iter('node'))
        config=json.loads((HERE/'fixture-config.json').read_text())
        expected='Jouw basis' if config['gate'] else ('Wombo' if path=='planning' else 'Public' if path.startswith('dev-shell') else ('Activiteiten' if config['language']=='nl' else 'Activities'))
        if config['gate']:
          if (expected in text or 'Profiel' in text) and any(n.get('class')=='android.widget.EditText' for n in root.iter('node')):return
        else:
          labels=['Week','Kalender','Activiteiten'] if config['language']=='nl' else ['Week','Calendar','Activities']
          nav=[n for n in root.iter('node') if n.get('clickable')=='true' and n.get('content-desc') in labels][-3:]
          if expected in text and len(nav)==3:return
      except RuntimeError:pass
      time.sleep(2)
    raise AssertionError('Review did not settle: '+path)
def dimensions(density=439,font=1):
    for attempt in range(3):
      try:adb('shell','wm','density',str(density));break
      except subprocess.CalledProcessError:
        if attempt==2:raise
        time.sleep(3)
    adb('shell','settings','put','system','font_scale',str(font));time.sleep(5)
def roots(name,language):
    capture(name+'-week')
    tap_label('Kalender' if language=='nl' else 'Calendar',name+'-week');capture(name+'-calendar')
    tap_label('Activiteiten' if language=='nl' else 'Activities',name+'-calendar');capture(name+'-activities')
    open_path('dev-shell-review?language='+language);capture(name+'-long-labels')

def scroll_in_view(cached=None, reverse=False):
    for attempt in range(20):
      try:
        root=ET.parse(HERE/(cached+'.xml')).getroot() if cached else hierarchy()
        boxes=[list(map(int,re.findall(r'-?\d+',n.get('bounds')))) for n in root.iter('node') if n.get('scrollable')=='true' and n.get('class')=='android.widget.ScrollView']
        if boxes:break
      except RuntimeError:pass
      time.sleep(2)
    else:raise AssertionError('No settled native scroll target')
    b=min(boxes,key=lambda b:b[3]-b[1]);x=b[0]+max(12,(b[2]-b[0])//50)
    adb('shell','input','swipe',str(x),str(int(b[1]+(b[3]-b[1])*(.2 if reverse else .85))),str(x),str(int(b[1]+(b[3]-b[1])*(.85 if reverse else .2))),'450');time.sleep(2)
def tap_partial(label):
    root=hierarchy();n=next(n for n in root.iter('node') if n.get('clickable')=='true' and label in (n.get('content-desc','')+' '+n.get('text','')))
    x1,y1,x2,y2=map(int,re.findall(r'-?\d+',n.get('bounds')));adb('shell','input','tap',str((x1+x2)//2),str((y1+y2)//2));time.sleep(3)

def png_only(name):
    adb('shell','screencap','-p','/sdcard/wombo-shell.png');adb('pull','/sdcard/wombo-shell.png',str(HERE/(name+'.png')))
    data={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'provenance':'Actual TalkBack accessibility focus; public native fixture; no UIAutomation suppression during screenshot',
      'inputMethod':sys.argv[1],
      'accessibilityServices':adb('shell','settings','get','secure','enabled_accessibility_services'),'enabled':adb('shell','settings','get','secure','accessibility_enabled'),
      'density':adb('shell','wm','density'),'fontScale':adb('shell','settings','get','system','font_scale'),'fixture':json.loads((HERE/'fixture-config.json').read_text())}
    (HERE/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n');print('Captured '+name,flush=True)
if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='reduced-motion':
      dimensions(439,1);configure('en');reload()
      for key in ['animator_duration_scale','window_animation_scale','transition_animation_scale']:adb('shell','settings','put','global',key,'0')
      time.sleep(3);capture('reduced-motion-week')
    elif mode=='talkback-enable':
      dimensions(439,1);configure('en');open_path('planning');capture('talkback-before-enable')
      adb('shell','settings','put','secure','enabled_accessibility_services','com.google.android.marvin.talkback/.TalkBackService')
      adb('shell','settings','put','secure','accessibility_enabled','1');time.sleep(5);png_only('talkback-enabled')
    elif mode=='talkback-shot':png_only(sys.argv[2])
    elif mode=='talkback-reload':
      configure('en');adb('shell','am','force-stop','com.adrivdbs.wombo')
      adb('shell',"am start -a android.intent.action.VIEW -d 'wombo://expo-development-client/?url=http%3A%2F%2F127.0.0.1%3A8081' com.adrivdbs.wombo")
      time.sleep(7);open_path('planning');time.sleep(30);png_only('talkback-root-reentered')
    elif mode=='talkback-explore':
      adb('shell','input','motionevent','DOWN',sys.argv[2],sys.argv[3]);time.sleep(.8)
      adb('shell','input','motionevent','UP',sys.argv[2],sys.argv[3]);time.sleep(12);png_only(sys.argv[4])
    elif mode=='talkback-hardware':
      # Emulator console help: device 0 is touch screen, state 1 down / 0 up.
      try:
        adb('emu','event','mouse',sys.argv[2],sys.argv[3],'0','1');time.sleep(.8)
      finally:adb('emu','event','mouse',sys.argv[2],sys.argv[3],'0','0')
      time.sleep(3);png_only(sys.argv[4])
    elif mode=='talkback-hardware-next':
      try:
        for x in [250,400,550,700,850]:adb('emu','event','mouse',str(x),'1000','0','1')
      finally:adb('emu','event','mouse','850','1000','0','0')
      time.sleep(3);png_only(sys.argv[2])
    elif mode=='talkback-hardware-activate':
      # One console connection keeps the double tap within Android's timing window.
      # Console authentication remains local and is never logged or recorded.
      with socket.create_connection(('127.0.0.1',5554),timeout=5) as console:
        def receive():
          result=b''
          while not (result.endswith(b'OK\r\n') or b'KO:' in result):result+=console.recv(4096)
          if b'KO:' in result:raise RuntimeError('Emulator console command rejected')
        def send(command):console.sendall((command+'\n').encode());receive()
        receive();send('auth '+(Path(os.environ['USERPROFILE'])/'.emulator_console_auth_token').read_text().strip())
        for _ in range(2):
          try:send(f'event mouse {sys.argv[2]} {sys.argv[3]} 0 1');time.sleep(.05)
          finally:send(f'event mouse {sys.argv[2]} {sys.argv[3]} 0 0')
          time.sleep(.05)
        console.sendall(b'quit\n')
      time.sleep(5);png_only(sys.argv[4])
    elif mode=='talkback-tap':
      adb('shell','input','tap',sys.argv[2],sys.argv[3]);time.sleep(3);png_only(sys.argv[4])
    elif mode=='talkback-next':
      adb('shell','input','swipe','250','1000','850','1000','150');time.sleep(3);png_only(sys.argv[2])
    elif mode=='talkback-activate':
      adb('shell', 'input tap '+sys.argv[2]+' '+sys.argv[3]+'; input tap '+sys.argv[2]+' '+sys.argv[3]);time.sleep(4);png_only(sys.argv[4])
    elif mode=='a11y-restore':
      baseline=json.loads((HERE/'accessibility-baseline.json').read_text())
      for namespace,key,field in [('secure','enabled_accessibility_services','enabledServices'),('secure','accessibility_enabled','enabled'),('global','animator_duration_scale','animator'),('global','window_animation_scale','window'),('global','transition_animation_scale','transition')]:
        value=baseline[field]
        if value=='null':adb('shell','settings','delete',namespace,key)
        else:adb('shell','settings','put',namespace,key,value)
      print('Accessibility settings restored')
    elif mode=='reload':reload(sys.argv[2]);capture(sys.argv[3])
    elif mode=='open':open_path(sys.argv[2]);capture(sys.argv[3])
    elif mode=='capture':capture(sys.argv[2])
    elif mode=='tap':tap_label(sys.argv[2]);capture(sys.argv[3])
    elif mode=='back':adb('shell','input','keyevent','4');time.sleep(3);capture(sys.argv[2])
    elif mode=='case':
      width=int(sys.argv[2]);font=int(sys.argv[3]);language=sys.argv[4]
      dimensions({320:540,360:480,393:439,412:420}[width],font);configure(language);reload();roots(f'{width}-font-{font}-{language}',language)
    elif mode=='partial':tap_partial(sys.argv[2]);capture(sys.argv[3])
    elif mode=='targets':
      print([(n.get('text'),n.get('content-desc'),n.get('bounds')) for n in hierarchy().iter('node') if n.get('clickable')=='true' or n.get('class')=='android.widget.EditText'])
    elif mode=='scroll-up':
      scroll_in_view(reverse=True);capture(sys.argv[2])
    elif mode=='scroll':
      scroll_in_view();capture(sys.argv[2])
    elif mode=='scenario':
      dimensions(540 if sys.argv[3]=='320' else 439,2 if sys.argv[4]=='2' else 1)
      configure(sys.argv[2],pending=sys.argv[5]=='pending',gate=sys.argv[5]=='gate');reload();capture(sys.argv[6])
    elif mode=='keyboard-320-focus-final':
      tap_label('Add activity');time.sleep(3)
      for _ in range(4):scroll_in_view()
      root=hierarchy();field=next(n for n in root.iter('node') if n.get('class')=='android.widget.EditText')
      x1,y1,x2,y2=map(int,re.findall(r'-?\d+',field.get('bounds')))
      adb('shell','input','tap',str((x1+x2)//2),str((y1+y2)//2));time.sleep(5);capture('keyboard-320-focus-final')
    elif mode=='keyboard-320-finish-final':
      for _ in range(5):scroll_in_view()
      capture('keyboard-320-font-2-lower')
      adb('shell','input','keyevent','4');time.sleep(2)
      for _ in range(8):scroll_in_view(reverse=True)
      tap_label('Back to Activities');capture('activity-task-320-font-2-return')
    elif mode=='keyboard-320-lower':
      tap_label('Add activity');time.sleep(3)
      for _ in range(4):scroll_in_view()
      root=hierarchy();field=next(n for n in root.iter('node') if n.get('class')=='android.widget.EditText')
      x1,y1,x2,y2=map(int,re.findall(r'-?\d+',field.get('bounds')))
      adb('shell','input','tap',str((x1+x2)//2),str((y1+y2)//2));time.sleep(3)
      for _ in range(4):scroll_in_view()
      capture('keyboard-320-font-2-lower')
      adb('shell','input','keyevent','4');time.sleep(2)
      for _ in range(8):scroll_in_view(reverse=True)
      tap_label('Back to Activities');capture('activity-task-320-font-2-return')
    elif mode=='keyboard-reference-finish':
      scroll_in_view();scroll_in_view();capture('keyboard-reference-lower')
      adb('shell','input','keyevent','4');time.sleep(2)
      for _ in range(5):scroll_in_view(reverse=True)
      tap_label('Back to Activities');capture('activity-task-return')
    elif mode=='keyboard-320':
      dimensions(540,2);configure('en');reload()
      tap_label('Activities');time.sleep(5);tap_label('Add activity');capture('activity-task-320-font-2-entry')
      for _ in range(4):scroll_in_view()
      capture('activity-task-320-font-2-fields')
      root=hierarchy();field=next(n for n in root.iter('node') if n.get('class')=='android.widget.EditText')
      x1,y1,x2,y2=map(int,re.findall(r'-?\d+',field.get('bounds')))
      adb('shell','input','tap',str((x1+x2)//2),str((y1+y2)//2));time.sleep(3);capture('keyboard-320-font-2')
      scroll_in_view();capture('keyboard-320-font-2-lower')
      adb('shell','input','keyevent','4');time.sleep(2)
      for _ in range(8):scroll_in_view(reverse=True)
      tap_label('Back to Activities');capture('activity-task-320-font-2-return')
    elif mode=='keyboard':
      root=hierarchy();field=next(n for n in root.iter('node') if n.get('class')=='android.widget.EditText')
      x1,y1,x2,y2=map(int,re.findall(r'-?\d+',field.get('bounds')))
      adb('shell','input','tap',str((x1+x2)//2),str((y1+y2)//2));time.sleep(3);capture(sys.argv[2])
    elif mode=='repair-activities':
      for width in [320,393]:
        dimensions(540 if width==320 else 439,1);configure('nl');reload('activities');capture(f'{width}-font-1-nl-activities')
    elif mode=='activity-titles':
      for language in ([sys.argv[2]] if len(sys.argv)>2 else ['nl','en']):
        configure(language);dimensions(439,1);reload('activities')
        for width,density in [(320,540),(360,480),(393,439),(412,420)]:
          for font in [1,2]:
            dimensions(density,font);time.sleep(5);tap_label('Activiteiten' if language=='nl' else 'Activities');capture(f'{width}-font-{font}-{language}-activities')
    elif mode=='long-lower':
      for width,density in [(320,540),(360,480),(393,439),(412,420)]:
        dimensions(density,2)
        for language in ['nl','en']:
          configure(language);open_path('dev-shell-review?language='+language)
          scroll_in_view();capture(f'{width}-font-2-{language}-long-lower-1')
          scroll_in_view();capture(f'{width}-font-2-{language}-long-lower-2')
    elif mode=='functional':
      dimensions(439,1);configure('en');reload();capture('origin-week-before-detail')
      scroll_in_view();capture('origin-week-workout')
      tap_partial('View workout');capture('detail-week-open')
      tap_label('Close');capture('detail-week-return')
      tap_label('Calendar');scroll_in_view();capture('origin-calendar-scroll')
      for attempt in range(6):
        try:tap_partial('View workout');break
        except StopIteration:scroll_in_view()
      else:raise AssertionError('Calendar fixture workout unreachable')
      capture('detail-calendar-open');tap_label('Close');capture('detail-calendar-return')
      scroll_in_view(reverse=True);scroll_in_view(reverse=True);scroll_in_view(reverse=True);tap_label('Profile');capture('profile-from-calendar')
      adb('shell','input','keyevent','4');time.sleep(3);capture('profile-return-calendar')
      tap_label('Activities');tap_label('Add activity');capture('activity-task-entry')
      scroll_in_view();capture('activity-task-fields')
    elif mode=='pending':
      dimensions(439,1);configure('en',pending=True);reload();capture('pending-rpe-week')
      tap_label('Calendar');capture('pending-rpe-calendar')
      tap_label('Activities');capture('pending-rpe-activities')
      tap_partial('waiting for RPE');capture('pending-rpe-feedback')
      tap_label('Back to Activities');capture('pending-rpe-return-activities')
      dimensions(540,2);configure('nl',pending=True);reload();capture('pending-rpe-320-font-2-nl-week')
      tap_label('Kalender');capture('pending-rpe-320-font-2-nl-calendar')
      tap_label('Activiteiten');capture('pending-rpe-320-font-2-nl-activities')
    elif mode=='gate':
      dimensions(439,1);configure('en',gate=True);reload('calendar');capture('onboarding-gate-calendar-deep-entry')
      open_path('activities');time.sleep(4);capture('onboarding-gate-activities-deep-entry')
    elif mode=='matrix':
      try:
        for language in ['nl','en']:
          configure(language);dimensions(439,1);reload()
          for width,density in [(320,540),(360,480),(393,439),(412,420)]:
            for font in [1,2]:
              dimensions(density,font);open_path('planning')
              for _ in range(10):
                try:
                  if any('Wombo' in n.get('content-desc','') for n in hierarchy().iter('node')):break
                except RuntimeError:pass
                time.sleep(2)
              roots(f'{width}-font-{font}-{language}',language)
      finally:dimensions(440,1)
