from pathlib import Path
import datetime,importlib.util,json,re,time
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('review',HERE/'native-review.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
keys=[('secure','enabled_accessibility_services'),('secure','accessibility_enabled'),('global','animator_duration_scale'),('global','window_animation_scale'),('global','transition_animation_scale')]
baseline={f'{ns}/{key}':r.adb('shell','settings','get',ns,key) for ns,key in keys}
def permission():
    return next(line.strip() for line in r.adb('shell','dumpsys','package','com.google.android.marvin.talkback').splitlines() if 'android.permission.POST_NOTIFICATIONS: granted=' in line)
permission_before=permission();added_flag='USER_FIXED' not in permission_before

def snapshot(name,expected):
    r.adb('shell','screencap','-p','/sdcard/wombo-batch8-a11y.png')
    r.adb('pull','/sdcard/wombo-batch8-a11y.png',str(HERE/(name+'.png')))
    data={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'serial':'emulator-5554',
      'provenance':'Actual TalkBack-enabled public fixture; no accessibility dump during focus screenshot',
      'expectedFocus':expected,'method':'Native touch exploration; no keyboard activation or hierarchy dump during focus capture',
      'enabledServices':r.adb('shell','settings','get','secure','enabled_accessibility_services'),
      'visualFocusValidation':'Inspect actual focus rectangle; expected target alone is not evidence of accessibility focus'}
    (HERE/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')

def service(enabled):
    r.adb('shell','settings','put','secure','enabled_accessibility_services','com.google.android.marvin.talkback/.TalkBackService' if enabled else 'null')
    r.adb('shell','settings','put','secure','accessibility_enabled','1' if enabled else '0');time.sleep(3)

def explore(box):
    x,y=(box[0]+box[2])//2,(box[1]+box[3])//2
    r.adb('shell','input','swipe',str(x),str(y),str(x),str(y),'600');time.sleep(2)
    return x,y

try:
    r.adb('shell','wm','density','439');r.adb('shell','settings','put','system','font_scale','1');time.sleep(2)
    (HERE/'fixture-config.json').write_text(json.dumps({'width':393,'fontScale':1,'language':'en','state':'warning','inertActions':True})+'\n')
    for key in ['animator_duration_scale','window_animation_scale','transition_animation_scale']:r.adb('shell','settings','put','global',key,'0')
    r.open_review('warning','en');r.capture('reduced-motion-warning')
    data=json.loads((HERE/'reduced-motion-warning.json').read_text());data['motionScales']={key:r.adb('shell','settings','get','global',key) for key in ['animator_duration_scale','window_animation_scale','transition_animation_scale']}
    assert all(float(v)==0 for v in data['motionScales'].values());(HERE/'reduced-motion-warning.json').write_text(json.dumps(data,indent=2)+'\n')
    if added_flag:r.adb('shell','pm','set-permission-flags','com.google.android.marvin.talkback','android.permission.POST_NOTIFICATIONS','user-fixed')
    for state,label,name in [('before','Move RUN-013 · Wisselduur','talkback-move-touch-focus'),
                             ('chooser','Thursday 8 October 2026','talkback-date-touch-focus')]:
        service(False)
        (HERE/'fixture-config.json').write_text(json.dumps({'width':393,'fontScale':1,'language':'en','state':state,'inertActions':True})+'\n')
        r.open_review(state,'en');_,box=r.target(label)
        service(True)
        resumed=next(line for line in r.adb('shell','dumpsys','activity','activities').splitlines() if 'topResumedActivity' in line)
        if 'com.google.android.marvin.talkback' in resumed:r.adb('shell','input','keyevent','4');time.sleep(2)
        x,y=explore(box);snapshot(name,label)
    r.adb('shell','input','tap',str(x),str(y));time.sleep(.1)
    r.adb('shell','input','tap',str(x),str(y));time.sleep(2)
    snapshot('talkback-date-selected','Thursday 8 October 2026')
    tree=r.hierarchy();assert r.marker(tree,'chooser')
    assert any(r.label_of(n)=='Thursday 8 October 2026' and n.get('checked')=='true' for n in tree.iter('node')),'TalkBack date activation did not select the date'
    assert any(n.get('resource-id')=='batch-8-action-none' for n in tree.iter('node')),'Date selection must stay local'
    (HERE/'talkback-date-activation.json').write_text(json.dumps({'pass':True,'observedExactDateChecked':True,'dateSelectionLocal':True,'pointerInjectionWithTalkBackEnabled':True,'talkbackGestureActivationNotProven':True,'focusScreenshotsRequireVisualInspection':True},indent=2)+'\n')
finally:
    for ns,key in keys:
        value=baseline[f'{ns}/{key}']
        r.adb('shell','settings','delete',ns,key) if value=='null' else r.adb('shell','settings','put',ns,key,value)
    restored={f'{ns}/{key}':r.adb('shell','settings','get',ns,key) for ns,key in keys};assert restored==baseline
    if added_flag:r.adb('shell','pm','clear-permission-flags','com.google.android.marvin.talkback','android.permission.POST_NOTIFICATIONS','user-fixed')
    assert permission()==permission_before
    (HERE/'accessibility-cleanup.json').write_text(json.dumps({'settingsRestored':True,'baseline':baseline,'restored':restored,'notificationPermissionRestored':True},indent=2)+'\n')
print('Reduced-motion and TalkBack touch/date captures complete; visually verify focus; settings restored')
