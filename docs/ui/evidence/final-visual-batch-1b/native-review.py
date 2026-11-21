"""Review only the inert Batch 1B native gallery. No athlete callbacks."""
from pathlib import Path
import datetime, json, re, subprocess, sys, time
import xml.etree.ElementTree as ET
HERE = Path(__file__).parent
ADB = 'C:/Users/Adria/AppData/Local/Android/Sdk/platform-tools/adb.exe'
def adb(*args):
    return subprocess.check_output([ADB, '-s', 'emulator-5554', *args], text=True).strip()
def hierarchy():
    adb('shell', 'uiautomator', 'dump', '/sdcard/wombo-primitives.xml')
    return ET.fromstring(adb('shell', 'cat', '/sdcard/wombo-primitives.xml'))
def capture(name):
    root = hierarchy()
    ET.ElementTree(root).write(HERE / (name + '.xml'), encoding='utf-8')
    adb('shell', 'screencap', '-p', '/sdcard/wombo-primitives.png')
    adb('pull', '/sdcard/wombo-primitives.png', str(HERE / (name + '.png')))
    record = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'serial': 'emulator-5554',
      'size': adb('shell','wm','size'), 'density': adb('shell','wm','density'),
      'fontScale': adb('shell','settings','get','system','font_scale'),
      'osLocale': adb('shell','getprop','persist.sys.locale') or adb('shell','getprop','ro.product.locale'),
      'provenance': 'Native development gallery with local state and existing public sourceWorkout fixture; no athlete writes'}
    (HERE/(name+'.json')).write_text(json.dumps(record,indent=2)+'\n')
    print('Captured '+name,flush=True)
def open_review(section,language):
    url = f'wombo:///dev-primitives?section={section}&language={language}'
    adb('shell', f"am start -a android.intent.action.VIEW -d '{url}' com.adrivdbs.wombo")
    time.sleep(3)
def scroll():
    adb('shell','input','swipe','540','1800','540','600','450')
    time.sleep(1)
if __name__ == '__main__':
    mode=sys.argv[1]
    if mode=='open': open_review(sys.argv[2],sys.argv[3])
    elif mode=='capture': capture(sys.argv[2])
    elif mode=='scroll': scroll()
    elif mode=='focus':
      open_review('form','nl')
      field=None
      for _ in range(5):
        field=next((n for n in hierarchy().iter('node') if n.get('class')=='android.widget.EditText' and n.get('text')=='Alex'),None)
        if field is not None: break
        open_review('form','nl')
      assert field is not None, 'Native review form did not settle'
      x1,y1,x2,y2=map(int,re.findall(r'\d+',field.get('bounds')))
      adb('shell','input','tap',str((x1+x2)//2),str((y1+y2)//2)); time.sleep(2)
      capture('form-focused-keyboard')
      adb('shell','input','keyevent','4'); time.sleep(1)
      capture('form-focused-keyboard-dismissed')
    elif mode=='reference':
      try:
        adb('shell','wm','density','439'); adb('shell','settings','put','system','font_scale','1.0'); time.sleep(6)
        for language in ['nl','en']:
          for section in ['form','workout','notices','states']:
            open_review(section,language)
            name=f'{section}-393-font-1-{language}'
            capture(name+'-top'); scroll(); capture(name+'-lower-1')
      finally:
        adb('shell','wm','density','440'); adb('shell','settings','put','system','font_scale','1.0')
    elif mode=='repair-large-nl':
      try:
        adb('shell','wm','density','439'); adb('shell','settings','put','system','font_scale','2'); time.sleep(6)
        for section in ['form','workout','notices','states']:
          open_review(section,'nl'); name=f'{section}-393-font-2-nl'
          capture(name+'-top')
          # Existing lower captures already show the final primitives; repair top framing only.
      finally:
        adb('shell','wm','density','440'); adb('shell','settings','put','system','font_scale','1.0')
    elif mode=='icons-skeleton':
      try:
        adb('shell','wm','density','540'); adb('shell','settings','put','system','font_scale','1.0'); time.sleep(6)
        for language in ['nl','en']:
          open_review('form',language)
          for _ in range(3): scroll()
          capture('form-footer-320-font-1-'+language)
          open_review('states',language)
          for _ in range(3): scroll()
          capture('controls-footer-320-font-1-'+language)
        for density,font,name in [(439,1,'icons-skeleton-reference'),(540,2,'icons-skeleton-320-font-2')]:
          adb('shell','wm','density',str(density)); adb('shell','settings','put','system','font_scale',str(font)); time.sleep(6)
          open_review('form','nl'); open_review('states','nl')
          for _ in range(5): scroll()
          capture(name)
      finally:
        adb('shell','wm','density','440'); adb('shell','settings','put','system','font_scale','1.0')
    elif mode=='restore':
      adb('shell','wm','density','reset'); adb('shell','settings','put','system','font_scale','1.0')
      adb('shell', "am start -a android.intent.action.VIEW -d 'wombo:///planning' com.adrivdbs.wombo")
      time.sleep(3); capture('week-restored')
    elif mode=='matrix':
      try:
        for width,density in [(393,439),(320,540)]:
          for font in [1,2]:
            adb('shell','wm','density',str(density))
            adb('shell','settings','put','system','font_scale',str(font))
            time.sleep(6)
            for language in ['nl','en']:
              for section in ['form','workout','notices','states']:
                open_review(section,language)
                name=f'{section}-{width}-font-{font}-{language}'
                capture(name+'-top')
                # All long sections remain scrollable, including large text.
                for index in range(1, 4 if font==2 else 2):
                  scroll(); capture(name+f'-lower-{index}')
      finally:
        adb('shell','wm','density','440')
        adb('shell','settings','put','system','font_scale','1.0')
