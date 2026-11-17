from pathlib import Path
import datetime,importlib.util,json,re,time
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('review',HERE/'native-review.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
keys=[('secure','enabled_accessibility_services'),('secure','accessibility_enabled'),('global','animator_duration_scale'),('global','window_animation_scale'),('global','transition_animation_scale')]
baseline={f'{ns}/{key}':r.adb('shell','settings','get',ns,key) for ns,key in keys}
def permission():
    return next(line.strip() for line in r.adb('shell','dumpsys','package','com.google.android.marvin.talkback').splitlines() if 'android.permission.POST_NOTIFICATIONS: granted=' in line)
permission_before=permission(); added_flag='USER_FIXED' not in permission_before
def explore(box,name,label):
    # Emulator hardware touchscreen coordinates use 0..32767, not display pixels.
    x=str(round((box[0]+box[2])/2*32767/1080))
    y=str(round((box[1]+box[3])/2*32767/2280))
    try:r.adb('emu','event','mouse',x,y,'0','1');time.sleep(.8)
    finally:r.adb('emu','event','mouse',x,y,'0','0')
    time.sleep(3)
    r.adb('shell','screencap','-p','/sdcard/wombo-batch7-a11y.png');r.adb('pull','/sdcard/wombo-batch7-a11y.png',str(HERE/(name+'.png')))
    data={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'serial':'emulator-5554','provenance':'Actual TalkBack touch exploration focus on public fixture; no accessibility dump during focus capture',
      'requestedTouchLabel':label,'requestedTouchBounds':box,'hardwareCoordinates':[int(x),int(y)],'enabledServices':r.adb('shell','settings','get','secure','enabled_accessibility_services'),
      'focusValidation':'Requires visual inspection; touch coordinates alone do not establish which node received accessibility focus'}
    (HERE/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
try:
    r.adb('shell','wm','density','439');r.adb('shell','settings','put','system','font_scale','1');time.sleep(2)
    (HERE/'fixture-config.json').write_text(json.dumps({'width':393,'fontScale':1,'language':'en','state':'manual','inertActions':True})+'\n')
    for key in ['animator_duration_scale','window_animation_scale','transition_animation_scale']:r.adb('shell','settings','put','global',key,'0')
    r.open_review('manual','en');r.capture('reduced-motion-placement')
    data=json.loads((HERE/'reduced-motion-placement.json').read_text());data['motionScales']={key:r.adb('shell','settings','get','global',key) for key in ['animator_duration_scale','window_animation_scale','transition_animation_scale']}
    assert all(float(v)==0 for v in data['motionScales'].values());(HERE/'reduced-motion-placement.json').write_text(json.dumps(data,indent=2)+'\n')
    r.scroll(r.hierarchy());time.sleep(1)
    tree=r.hierarchy()
    choice=next(n for n in tree.iter('node') if n.get('content-desc','').startswith('Choice 1 ·') and 'Monday' in n.get('content-desc',''))
    box=list(map(int,re.findall(r'\d+',choice.get('bounds'))));label=choice.get('content-desc')
    assert box[1]>90 and box[3]<2200 and choice.get('checked')=='true'
    if added_flag:r.adb('shell','pm','set-permission-flags','com.google.android.marvin.talkback','android.permission.POST_NOTIFICATIONS','user-fixed')
    r.adb('shell','settings','put','secure','enabled_accessibility_services','com.google.android.marvin.talkback/.TalkBackService')
    r.adb('shell','settings','put','secure','accessibility_enabled','1');time.sleep(5)
    resumed=next(line for line in r.adb('shell','dumpsys','activity','activities').splitlines() if 'topResumedActivity' in line)
    if 'com.google.android.marvin.talkback' in resumed:r.adb('shell','input','keyevent','4');time.sleep(2)
    explore(box,'talkback-mode-focus',label)
finally:
    for ns,key in keys:
        value=baseline[f'{ns}/{key}']
        r.adb('shell','settings','delete',ns,key) if value=='null' else r.adb('shell','settings','put',ns,key,value)
    restored={f'{ns}/{key}':r.adb('shell','settings','get',ns,key) for ns,key in keys};assert restored==baseline
    if added_flag:r.adb('shell','pm','clear-permission-flags','com.google.android.marvin.talkback','android.permission.POST_NOTIFICATIONS','user-fixed')
    assert permission()==permission_before
    (HERE/'accessibility-cleanup.json').write_text(json.dumps({'settingsRestored':True,'baseline':baseline,'restored':restored,'notificationPermissionRestored':True},indent=2)+'\n')
print('Reduced motion and TalkBack capture complete; inspect actual focused node; settings restored')
