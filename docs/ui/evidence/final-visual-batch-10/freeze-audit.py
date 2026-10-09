from pathlib import Path
import hashlib,json,re,subprocess
HERE=Path(__file__).resolve().parent
WORK=HERE.parents[3]
BASE='5891858'
def git(*args):return subprocess.check_output(['git',*args],cwd=WORK,text=True,encoding='utf-8')
def original(path):return git('show',BASE+':'+path)
def read(path):return (WORK/path).read_text(encoding='utf-8')
def block(text,start,end):return text[text.index(start):text.index(end,text.index(start))]
def norm(text):return re.sub(r'\s+',' ',text).strip()
old=original('mobile/src/screens/OnboardingScreen.tsx');new=read('mobile/src/screens/OnboardingScreen.tsx');goal=read('mobile/src/ui-v2/screens/GoalForm.tsx');profile=read('mobile/src/ui-v2/components/ProfileForm.tsx');oldprofile=original('mobile/src/screens/ProfileScreen.tsx');newprofile=read('mobile/src/screens/ProfileScreen.tsx')
checks={}
checks['goal_decisions_and_validation_unchanged']=norm(block(old,'  const [validationAttempted','  return ('))==norm(block(goal,'  const [validationAttempted','  return ('))
checks['race_date_parser_unchanged']=norm(block(old,'function normalizeRaceDate','export function GoalStep'))==norm(block(goal,'function normalizeRaceDate','export function GoalStep'))
# Compare the actual payload expression, independently of the additional invalid-field focus.
oldgoal=old[old.index('export function GoalStep'):old.index('type ReviewStepProps')]
def payload(text):
    start=text.index('void onSave({');return text[start:text.index('});',start)+3]
checks['goal_payload_unchanged']=norm(payload(oldgoal))==norm(payload(goal))
oldform=old[old.index('export function ProfileStep'):old.index('type ConfirmationStepProps')]
checks['timezone_detection_and_selection_defaults_unchanged']=norm(block(old,'  const detected = useMemo','  return ('))==norm(block(new,'  const detected = useMemo','  return ('))
checks['history_baselines_and_validation_unchanged']=norm(block(old,"  const initial = (discipline: Discipline)",'  return ('))==norm(block(new,"  const initial = (discipline: Discipline)",'  return ('))
checks['profile_decisions_unchanged']=norm(block(oldform,'  const [firstName','  return ('))==norm(block(profile,'  const [firstName','  return ('))
checks['profile_payload_unchanged']=norm(block(oldform,'void onSave({','})'))==norm(block(profile,'void onSave({','})'))
ownerold=old[old.index('export function OnboardingScreen'):];ownernew=new[new.index('export function OnboardingScreen'):]
checks['onboarding_reads_resumes_mutations_versions_unchanged']=norm(block(ownerold,'  const [state','  if (loading)'))==norm(block(ownernew,'  const [state','  if (loading)'))
checks['physiology_resume_guard_unchanged']=norm(block(ownerold,'  const physiologyProfileComplete','  return ('))==norm(block(ownernew,'  const physiologyProfileComplete','  return ('))
checks['profile_reads_and_state_owner_unchanged']=norm(block(oldprofile,'  const [profile','  return (\n    <SafeAreaView'))==norm(block(newprofile,'  const [profile','  return <'))
def profile_save_body(text):
    start=text.index('=> {',text.index('onSave={async'))+3
    depth=0
    for index in range(start,len(text)):
        if text[index]=='{':depth+=1
        elif text[index]=='}':
            depth-=1
            if depth==0:return text[start:index+1]
    raise AssertionError('Unbalanced profile save callback')
checks['profile_save_reload_and_error_owner_unchanged']=norm(profile_save_body(oldprofile))==norm(profile_save_body(newprofile))
oldpicker=original('mobile/src/components/DurationPicker.tsx');picker=read('mobile/src/components/DurationPicker.tsx')
checks['duration_options_clamping_precision_unchanged']=norm(block(oldpicker,'  const [openUnit','  return ('))==norm(block(picker,'  const [openUnit','  return ('))
protected=['mobile/src/api/client.ts','mobile/src/api/types.ts','mobile/src/lib/onboardingForms.ts','mobile/src/lib/dateInput.ts','mobile/src/lib/runPace.ts','mobile/src/screens/ZoneSetupStep.tsx','mobile/src/screens/ZoneProfileScreen.tsx','mobile/src/navigation/TrainingLayout.tsx','mobile/package.json','mobile/package-lock.json','mobile/jest.config.js','mobile/app/_layout.tsx','mobile/app/index.tsx']
# Root/index temporary fixture overrides must be removed before final verification.
unchanged={p:not bool(git('diff',BASE,'--',p).strip()) for p in protected}
checks.update({'protected:'+p:v for p,v in unchanged.items()})
changed=git('diff',BASE,'--name-only').splitlines()
untracked=git('ls-files','--others','--exclude-standard','mobile/src','mobile/app').splitlines()
allowed={'mobile/src/screens/ProfileScreen.tsx','mobile/src/screens/ProfileScreen.test.tsx','mobile/src/screens/OnboardingScreen.tsx','mobile/src/screens/OnboardingScreen.test.tsx','mobile/src/screens/OnboardingScreen.resume.test.tsx','mobile/src/components/DurationPicker.tsx','mobile/src/components/DurationPicker.test.tsx','mobile/src/ui-v2/components/FormComposition.tsx','mobile/src/ui-v2/components/ProfileForm.tsx','mobile/src/ui-v2/components/StepProgress.tsx','mobile/src/ui-v2/screens/GoalForm.tsx','mobile/src/ui-v2/primitives/Input.tsx','mobile/src/ui-v2/primitives/Icon.tsx'}
checks['only_batch10_mobile_presentation_and_tests']=all(p in allowed or p.startswith('docs/ui/') for p in changed+untracked)
checks['no_other_stack_changes']=not bool(git('diff',BASE,'--','backend','supabase','database').strip())
sources={str(p.relative_to(WORK)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['mobile/src','mobile/app'] for p in (WORK/folder).rglob('*') if p.is_file()}
refs=json.loads((HERE/'reference-hashes.json').read_text())
ROOT=Path('F:/Projecten Business/Start23/Code')
checks['17_reference_hashes_unchanged']=all(hashlib.sha256((ROOT/'docs/ui'/p).read_bytes()).hexdigest()==sha for p,sha in refs.items())
result={'baseline':BASE,'checks':checks,'changed':changed,'newPresentationFiles':untracked,'sourceHashes':sources,'validationFocus':'Added focus of first invalid existing field; no validation predicate, conversion, payload or physiological boundary changed.'}
(HERE/'functional-freeze.json').write_text(json.dumps(result,indent=2)+'\n')
assert all(checks.values()),[k for k,v in checks.items() if not v]
print('Functional and scope freeze:',len(checks),'checks PASS')
