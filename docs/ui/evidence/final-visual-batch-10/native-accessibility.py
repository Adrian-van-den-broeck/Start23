from pathlib import Path
import importlib.util,json,time,datetime,subprocess
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('review',HERE/'native-review.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
keys=[('secure','enabled_accessibility_services'),('secure','accessibility_enabled'),('global','animator_duration_scale'),('global','window_animation_scale'),('global','transition_animation_scale')]
baseline={ns+'/'+key:r.adb('shell','settings','get',ns,key) for ns,key in keys}
def permission():return next(line.strip() for line in r.adb('shell','dumpsys','package','com.google.android.marvin.talkback').splitlines() if 'android.permission.POST_NOTIFICATIONS: granted=' in line)
def service(enabled):
    r.adb('shell','settings','put','secure','enabled_accessibility_services','com.google.android.marvin.talkback/.TalkBackService' if enabled else 'null')
    r.adb('shell','settings','put','secure','accessibility_enabled','1' if enabled else '0');time.sleep(3)
def snapshot(name,label):
    (HERE/(name+'.png')).write_bytes(subprocess.check_output([r.ADB,'-s',r.SERIAL,'exec-out','screencap','-p'],timeout=25))
    (HERE/(name+'.json')).write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'provenance':'Actual TalkBack-enabled inert production fixture; no hierarchy dump during focus screenshot','expectedFocus':label,'method':'Native touch exploration using geometry re-read after TalkBack activation; expected target is not proof of observed focus or announcement','services':r.adb('shell','settings','get','secure','enabled_accessibility_services')},indent=2)+'\n')
before=permission();added='USER_FIXED' not in before
try:
    for key in ['animator_duration_scale','window_animation_scale','transition_animation_scale']:r.adb('shell','settings','put','global',key,'0')
    r.open_case('goal-run');r.target('Kies uren voor Totale richttijd');r.capture('reduced-motion-goal')
    r.tap('Kies uren voor Totale richttijd');t=r.tree();assert any(n.get('content-desc')=='Duurkeuze sluiten' for n in t.iter('node'))
    (HERE/'reduced-motion-duration-modal.png').write_bytes(subprocess.check_output([r.ADB,'-s',r.SERIAL,'exec-out','screencap','-p'],timeout=25))
    r.adb('shell','input','keyevent','4');assert not any(n.get('content-desc')=='Duurkeuze sluiten' for n in r.tree().iter('node'))
    if added:r.adb('shell','pm','set-permission-flags','com.google.android.marvin.talkback','android.permission.POST_NOTIFICATIONS','user-fixed')
    for state,label,name in [('profile-editor','Rusthartslag, bpm','talkback-profile-heart-rate'),('goal-run','Richttempo (min/km)','talkback-goal-target-mode')]:
        service(False);r.open_case(state);_,b=r.target(label)
        service(True)
        resumed=next(line for line in r.adb('shell','dumpsys','activity','activities').splitlines() if 'topResumedActivity' in line)
        if 'com.google.android.marvin.talkback' in resumed:r.adb('shell','input','keyevent','4');time.sleep(2)
        # TalkBack activation can shift scrolling to its initial focus. Re-read current native geometry.
        current=r.tree();target=next(n for n in current.iter('node') if n.get('content-desc')==label and n.get('clickable')=='true')
        b=r.bounds(target);x,y=(b[0]+b[2])//2,(b[1]+b[3])//2
        r.adb('shell','input','tap',str(x),str(y));time.sleep(2);snapshot(name,label)
    (HERE/'accessibility-native-run.json').write_text(json.dumps({'reducedMotionScalesZero':True,'durationOpenAndAndroidBackClose':True,'TalkBackTouchCapturesProduced':True,'announcementsVerified':False,'physicalDeviceVerified':False,'backendWrites':False},indent=2)+'\n')
finally:
    for ns,key in keys:
        value=baseline[ns+'/'+key];r.adb('shell','settings','delete',ns,key) if value=='null' else r.adb('shell','settings','put',ns,key,value)
    restored={ns+'/'+key:r.adb('shell','settings','get',ns,key) for ns,key in keys};assert baseline==restored
    if added:r.adb('shell','pm','clear-permission-flags','com.google.android.marvin.talkback','android.permission.POST_NOTIFICATIONS','user-fixed')
    assert permission()==before
    (HERE/'accessibility-cleanup.json').write_text(json.dumps({'baseline':baseline,'restored':restored,'settingsRestored':True,'notificationPermissionRestored':True},indent=2)+'\n')
print('Reduced motion and TalkBack touch captures complete; inspect actual focus',flush=True)
