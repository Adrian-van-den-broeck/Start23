from pathlib import Path
import importlib.util,json,sys,time
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('review',HERE/'native-review.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
keys=['enabled_accessibility_services','accessibility_enabled']
baseline={key:r.adb('shell','settings','get','secure',key) for key in keys}
assert baseline['accessibility_enabled']=='0'
permission=lambda:next(line.strip() for line in r.adb('shell','dumpsys','package','com.google.android.marvin.talkback').splitlines() if 'android.permission.POST_NOTIFICATIONS: granted=' in line)
permission_before=permission();added_flag='USER_FIXED' not in permission_before
modifier='117' if '--action-key' in sys.argv else '57'
prefix='talkback-action-next' if modifier=='117' else 'talkback-next'
try:
    (HERE/'fixture-config.json').write_text(json.dumps({'width':393,'fontScale':1,'language':'en','state':'chooser','inertActions':True})+'\n')
    r.open_review('chooser','en');r.target('Thursday 8 October 2026')
    if added_flag:r.adb('shell','pm','set-permission-flags','com.google.android.marvin.talkback','android.permission.POST_NOTIFICATIONS','user-fixed')
    r.adb('shell','settings','put','secure','enabled_accessibility_services','com.google.android.marvin.talkback/.TalkBackService')
    r.adb('shell','settings','put','secure','accessibility_enabled','1');time.sleep(4)
    for step in range(1,17):
        r.adb('shell','input','keycombination','-t','100',modifier,'22');time.sleep(.8)
        resumed=next(line for line in r.adb('shell','dumpsys','activity','activities').splitlines() if 'topResumedActivity' in line)
        assert 'com.adrivdbs.wombo/' in resumed,'Refuse capture outside the fixture app'
        r.adb('shell','screencap','-p','/sdcard/wombo-batch8-a11y.png')
        name=f'{prefix}-{step:02}'
        r.adb('pull','/sdcard/wombo-batch8-a11y.png',str(HERE/(name+'.png')))
        (HERE/(name+'.json')).write_text(json.dumps({'method':'Actual documented TalkBack modifier+Right native shortcut; no accessibility dump during focus capture','modifierKeyCode':modifier,
          'step':step,'state':'chooser','services':r.adb('shell','settings','get','secure','enabled_accessibility_services'),
          'source':'https://support.google.com/accessibility/android/answer/6110948?hl=en-GB','visualFocusInspectionRequired':True},indent=2)+'\n')
    assert r.marker(r.hierarchy(),'chooser')
finally:
    for key,value in baseline.items():
        r.adb('shell','settings','delete','secure',key) if value=='null' else r.adb('shell','settings','put','secure',key,value)
    assert all(r.adb('shell','settings','get','secure',key)==value for key,value in baseline.items())
    if added_flag:r.adb('shell','pm','clear-permission-flags','com.google.android.marvin.talkback','android.permission.POST_NOTIFICATIONS','user-fixed')
    assert permission()==permission_before
    (HERE/'talkback-navigation-cleanup.json').write_text(json.dumps({'settingsRestored':True,'notificationPermissionRestored':True},indent=2)+'\n')
print('Native TalkBack navigation captured; inspect actual green focus rectangles; settings restored')
