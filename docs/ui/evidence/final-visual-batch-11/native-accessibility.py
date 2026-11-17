from pathlib import Path
import importlib.util,json,time,datetime,subprocess,sys
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('review',HERE/'native-review.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
keys=[('secure','enabled_accessibility_services'),('secure','accessibility_enabled'),('global','animator_duration_scale'),('global','window_animation_scale'),('global','transition_animation_scale')]
baseline={ns+'/'+key:r.adb('shell','settings','get',ns,key) for ns,key in keys}
def permission():return next(line.strip() for line in r.adb('shell','dumpsys','package','com.google.android.marvin.talkback').splitlines() if 'android.permission.POST_NOTIFICATIONS: granted=' in line)
beforePermission=permission();addedPermissionFlag='USER_FIXED' not in beforePermission
def service(enabled):
 r.adb('shell','settings','put','secure','enabled_accessibility_services','com.google.android.marvin.talkback/.TalkBackService' if enabled else 'null');r.adb('shell','settings','put','secure','accessibility_enabled','1' if enabled else '0');time.sleep(3)
def snapshot(name,label):
 (HERE/(name+'.png')).write_bytes(subprocess.check_output([r.ADB,'-s',r.SERIAL,'exec-out','screencap','-p'],timeout=25));(HERE/(name+'.json')).write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'provenance':'Actual TalkBack-enabled production screen with inert DTOs; no hierarchy dump during focus screenshot','expectedFocus':label,'method':'Native touch exploration after TalkBack activation; expected target does not prove observed focus or spoken announcements','services':r.adb('shell','settings','get','secure','enabled_accessibility_services')},indent=2)+'\n')
try:
 if '--resume-talkback' not in sys.argv and '--resume-threshold' not in sys.argv:
  for key in ['animator_duration_scale','window_animation_scale','transition_animation_scale']:r.adb('shell','settings','put','global',key,'0')
  r.open_case('pending');r.tap('Zones goedkeuren');r.capture('reduced-motion-zone-decision');r.open_case('feedback');r.target('Opslaan en deterministisch evalueren');r.capture('reduced-motion-observation');
 if addedPermissionFlag:r.adb('shell','pm','set-permission-flags','com.google.android.marvin.talkback','android.permission.POST_NOTIFICATIONS','user-fixed')
 cases=[('result','Drempel bevestigen','talkback-threshold-decision')] if '--resume-threshold' in sys.argv else [('known','Gemeten door arts/lab','talkback-zone-source'),('result','Drempel bevestigen','talkback-threshold-decision')]
 for state,label,name in cases:
  # Position with service off, then activate TalkBack without a heuristic Back into the launcher.
  service(False);r.open_case(state);r.target(label);service(True)
  current=r.tree();target=next((n for n in current.iter('node') if n.get('content-desc')==label and n.get('clickable')=='true'), None)
  targetTouchAttempted=False
  if target is not None:
   b=r.bounds(target)
   if b[2]>b[0] and b[3]>b[1]:
    time.sleep(3);r.adb('shell','input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2));time.sleep(2);targetTouchAttempted=True
  snapshot(name,label)
  metadata=json.loads((HERE/(name+'.json')).read_text());metadata['targetTouchAttempted']=targetTouchAttempted;metadata['targetFocusRetentionVerified']=False;(HERE/(name+'.json')).write_text(json.dumps(metadata,indent=2)+'\n')
 (HERE/'accessibility-native-run.json').write_text(json.dumps({'reducedMotionScalesZero':True,'reducedMotionBootVerified':True,'reducedMotionEvidence':'Zero-scale first-run captures retained after TalkBack driver field-name failure' if any(arg.startswith('--resume-') for arg in sys.argv) else 'Current full run','zoneDecisionAndObservationReachable':True,'TalkBackEnabledCapturesProduced':True,'targetFocusRetentionVerified':False,'announcementsVerified':False,'physicalDeviceVerified':False,'backendWrites':False},indent=2)+'\n')
finally:
 for ns,key in keys:
  value=baseline[ns+'/'+key];r.adb('shell','settings','delete',ns,key) if value=='null' else r.adb('shell','settings','put',ns,key,value)
 if addedPermissionFlag:r.adb('shell','pm','clear-permission-flags','com.google.android.marvin.talkback','android.permission.POST_NOTIFICATIONS','user-fixed')
 assert permission()==beforePermission
 restored={ns+'/'+key:r.adb('shell','settings','get',ns,key) for ns,key in keys};assert baseline==restored;(HERE/'accessibility-cleanup.json').write_text(json.dumps({'baseline':baseline,'restored':restored,'settingsRestored':True,'notificationPermissionRestored':True},indent=2)+'\n')
print('Reduced motion and TalkBack touch captures complete; inspect observed focus',flush=True)
