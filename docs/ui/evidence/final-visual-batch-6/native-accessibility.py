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
def png_only(name, target_box):
    base.adb('shell','screencap','-p','/sdcard/wombo-creation-accessibility.png')
    base.adb('pull','/sdcard/wombo-creation-accessibility.png',str(here/(name+'.png')))
    data = {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'serial':'emulator-5556',
        'provenance':'Actual TalkBack focus on public Selection fixture; no UIAutomation accessibility suppression during screenshot',
        'nativeTargetBoundsBeforeTalkBack':target_box, 'density':base.adb('shell','wm','density'),'fontScale':base.adb('shell','settings','get','system','font_scale'),
        'enabledServices':base.adb('shell','settings','get','secure','enabled_accessibility_services'),
        'accessibilityEnabled':base.adb('shell','settings','get','secure','accessibility_enabled')}
    (here/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
try:
    base.dimensions(439,1)
    (here/'fixture-config.json').write_text(json.dumps({'language':'en','state':'selection','width':393,'fontScale':1,'inertActions':True})+'\n')
    for key in ['animator_duration_scale','window_animation_scale','transition_animation_scale']:
        base.adb('shell','settings','put','global',key,'0')
    review.open_review('selection','en','reduced-motion')
    review.capture('reduced-motion-selection')
    motion_path=here/'reduced-motion-selection.json'
    motion_record=json.loads(motion_path.read_text())
    motion_record['motionScales']={key:base.adb('shell','settings','get','global',key) for key in ['animator_duration_scale','window_animation_scale','transition_animation_scale']}
    assert all(float(value)==0 for value in motion_record['motionScales'].values())
    motion_path.write_text(json.dumps(motion_record,indent=2)+'\n')
    tree = base.hierarchy()
    profile = next(n for n in tree.iter('node') if n.get('content-desc') == 'Back to Week' and n.get('clickable') == 'true')
    box = list(map(int,re.findall(r'\d+',profile.get('bounds'))))
    choose=next(n for n in tree.iter('node') if n.get('content-desc','').startswith('Choose \u00b7'))
    today_box=list(map(int,re.findall(r'\d+',choose.get('bounds'))))
    today_label=choose.get('content-desc')
    assert 'RUN-013' in today_label
    # Temporarily keep notification permission denied without a startup prompt.
    base.adb('shell','pm','set-permission-flags','com.google.android.marvin.talkback','android.permission.POST_NOTIFICATIONS','user-fixed')
    base.adb('shell','settings','put','secure','enabled_accessibility_services','com.google.android.marvin.talkback/.TalkBackService')
    base.adb('shell','settings','put','secure','accessibility_enabled','1')
    time.sleep(5)
    activities=base.adb('shell','dumpsys','activity','activities')
    resumed=next(line for line in activities.splitlines() if 'topResumedActivity' in line)
    if 'com.google.android.marvin.talkback' in resumed:
        base.adb('shell','input','keyevent','4');time.sleep(3)
    # The emulator's hardware touch path preserves touch exploration semantics.
    x,y = str((box[0]+box[2])//2),str((box[1]+box[3])//2)
    try:
        base.adb('emu','event','mouse',x,y,'0','1')
        time.sleep(.8)
    finally: base.adb('emu','event','mouse',x,y,'0','0')
    time.sleep(4)
    png_only('talkback-back-focus', box)
    x,y=str((today_box[0]+today_box[2])//2),str((today_box[1]+today_box[3])//2)
    try:
        base.adb('emu','event','mouse',x,y,'0','1');time.sleep(.8)
    finally:base.adb('emu','event','mouse',x,y,'0','0')
    time.sleep(4)
    png_only('talkback-choose-focus', today_box)
    path=here/'talkback-choose-focus.json'
    record=json.loads(path.read_text(encoding='utf-8'));record['nativeChooseLabelBeforeTalkBack']=today_label
    path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
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
print('Reduced motion captured; TalkBack Back/Choose focus captured; settings restored.')
