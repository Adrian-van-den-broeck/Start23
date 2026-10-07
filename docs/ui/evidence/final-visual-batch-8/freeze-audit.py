from pathlib import Path
import hashlib,json,subprocess
HERE=Path(__file__).resolve().parent
root=HERE.parents[3];work=root/'.worktrees/wombo-ui-v2-activities'
baseline=json.loads((HERE/'baseline.json').read_text())
expected=['mobile/src/screens/PlanningWorkoutMoveTask.tsx','mobile/src/ui-v2/components/WeekAgenda.tsx',
          'mobile/src/ui-v2/components/WorkoutSummary.tsx','mobile/src/ui-v2/screens/WorkoutMoveScreen.tsx',
          'mobile/src/ui-v2/screens/WorkoutMoveScreen.test.tsx']
changed=sorted(name.replace('\\','/') for name,h in baseline['sourceHashes'].items() if hashlib.sha256((work/name).read_bytes()).hexdigest()!=h)
assert changed==sorted(expected)
task='mobile/src/screens/PlanningWorkoutMoveTask.tsx'
before=subprocess.check_output(['git','show',baseline['baselineCommit']+':'+task],cwd=work,text=True)
after=(work/task).read_text().replace("import { workoutSummaryViewModel } from '../ui-v2/utils/workoutSummaryViewModel';\n",'')
after=after.replace('summary={workoutSummaryViewModel(workout)}','name={workout.name}')
assert before==after,'Move task lifecycle changed beyond the summary presentation binding'
manifests=['mobile/package.json','mobile/package-lock.json','mobile/jest.config.js','mobile/tsconfig.json']
for path in manifests:
    before=subprocess.check_output(['git','show',baseline['baselineCommit']+':'+path],cwd=work)
    assert before.replace(b'\r\n',b'\n')==(work/path).read_bytes().replace(b'\r\n',b'\n'),path
(HERE/'functional-freeze.json').write_text(json.dumps({'result':'PASS','changed':changed,
    'protectedSourcesUnchanged':len(baseline['sourceHashes'])-len(changed),'taskLifecycleOutsideSummaryBindingUnchanged':True,
    'dependencyManifestsUnchanged':manifests,'controllersMappersClientsRoutesV1Unchanged':True},indent=2)+'\n')
print('Functional freeze:',len(changed),'presentation/test files;',len(baseline['sourceHashes'])-len(changed),'protected sources unchanged')
