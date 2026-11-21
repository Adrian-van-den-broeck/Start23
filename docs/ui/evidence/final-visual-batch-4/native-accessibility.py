"""Reduced-motion and actual TalkBack focus; always restore device settings."""
from pathlib import Path
import datetime, json, re, time
from native_review_import import review
here = Path(__file__).resolve().parent
base = review.base
keys = [('secure','enabled_accessibility_services'), ('secure','accessibility_enabled'),
        ('global','animator_duration_scale'), ('global','window_animation_scale'), ('global','transition_animation_scale')]
baseline = {f'{namespace}/{key}': base.adb('shell','settings','get',namespace,key) for namespace,key in keys}
def notification_permission():
    return next(line.strip() for line in base.adb('shell','dumpsys','package','com.google.android.marvin.talkback').splitlines() if 'android.permission.POST_NOTIFICATIONS: granted=' in line)
permission_before=notification_permission()
assert 'granted=false' in permission_before and 'USER_FIXED' not in permission_before
(here/'accessibility-baseline.json').write_text(json.dumps({'settings':baseline,'notificationPermission':permission_before},indent=2)+'\n')
def png_only(name):
    base.adb('shell','screencap','-p','/sdcard/wombo-week-accessibility.png')
    base.adb('pull','/sdcard/wombo-week-accessibility.png',str(here/(name+'.png')))
    data = {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'serial':'emulator-5554',
        'provenance':'Actual TalkBack focus on public Week fixture; no UIAutomation accessibility suppression during screenshot',
        'density':base.adb('shell','wm','density'),'fontScale':base.adb('shell','settings','get','system','font_scale'),
        'enabledServices':base.adb('shell','settings','get','secure','enabled_accessibility_services'),
        'accessibilityEnabled':base.adb('shell','settings','get','secure','accessibility_enabled')}
    (here/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
try:
    base.dimensions(439,1)
    (here/'fixture-config.json').write_text(json.dumps({'language':'en','state':'activePending','width':393,'fontScale':1,'inertActions':True})+'\n')
    for key in ['animator_duration_scale','window_animation_scale','transition_animation_scale']:
        base.adb('shell','settings','put','global',key,'0')
    review.open_review('activePending','en','reduced-motion')
    review.capture('reduced-motion-week')
    motion_path=here/'reduced-motion-week.json'
    motion_record=json.loads(motion_path.read_text())
    motion_record['motionScales']={key:base.adb('shell','settings','get','global',key) for key in ['animator_duration_scale','window_animation_scale','transition_animation_scale']}
    assert all(float(value)==0 for value in motion_record['motionScales'].values())
    motion_path.write_text(json.dumps(motion_record,indent=2)+'\n')
    tree = base.hierarchy()
    profile = next(n for n in tree.iter('node') if n.get('content-desc') == 'Profile' and n.get('clickable') == 'true')
    box = list(map(int,re.findall(r'\d+',profile.get('bounds'))))
    # Temporarily keep notification permission denied without a startup prompt.
    base.adb('shell','pm','set-permission-flags','com.google.android.marvin.talkback','android.permission.POST_NOTIFICATIONS','user-fixed')
    base.adb('shell','settings','put','secure','enabled_accessibility_services','com.google.android.marvin.talkback/.TalkBackService')
    base.adb('shell','settings','put','secure','accessibility_enabled','1')
    time.sleep(5)
    # The emulator's hardware touch path preserves touch exploration semantics.
    x,y = str((box[0]+box[2])//2),str((box[1]+box[3])//2)
    try:
        base.adb('emu','event','mouse',x,y,'0','1')
        time.sleep(.8)
    finally: base.adb('emu','event','mouse',x,y,'0','0')
    time.sleep(4)
    png_only('talkback-profile-focus')
finally:
    for namespace,key in keys:
        value = baseline[f'{namespace}/{key}']
        if value == 'null': base.adb('shell','settings','delete',namespace,key)
        else: base.adb('shell','settings','put',namespace,key,value)
    restored = {f'{namespace}/{key}':base.adb('shell','settings','get',namespace,key) for namespace,key in keys}
    assert restored == baseline
    base.adb('shell','pm','clear-permission-flags','com.google.android.marvin.talkback','android.permission.POST_NOTIFICATIONS','user-fixed')
    assert notification_permission()==permission_before
    (here/'accessibility-cleanup.json').write_text(json.dumps({'settingsRestored':True,'baseline':baseline,'restored':restored,'notificationPermissionRestored':True,'notificationPermissionBaseline':permission_before,'notificationPermissionAfter':notification_permission()},indent=2)+'\n')
print('Reduced motion captured; TalkBack Profile focus captured; settings restored.')
