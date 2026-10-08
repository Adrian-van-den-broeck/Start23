from pathlib import Path
import hashlib,json,subprocess
HERE=Path(__file__).resolve().parent
root=HERE.parents[3];work=root/'.worktrees/wombo-ui-v2-activities'
baseline=json.loads((HERE/'baseline.json').read_text())
expected=['mobile/src/ui-v2/components/ActivitySummary.tsx','mobile/src/ui-v2/screens/ActivitiesScreen.tsx','mobile/src/ui-v2/primitives/Notice.tsx',
 'mobile/src/ui-v2/screens/ActivityEntryScreen.tsx','mobile/src/ui-v2/screens/ActivityFeedbackScreen.tsx','mobile/src/ui-v2/components/RpeChoices.tsx',
 'mobile/src/ui-v2/primitives/ChoiceRow.tsx','mobile/src/ui-v2/screens/ActivitiesScreens.test.tsx']
actual={str(p.relative_to(work)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['mobile/app','mobile/src'] for p in (work/folder).rglob('*') if p.is_file() and p.name!='dev-batch9-review.tsx'}
assert actual.keys()==baseline['sourceHashes'].keys()
changed=sorted(n.replace('\\','/') for n,h in actual.items() if h!=baseline['sourceHashes'][n])
assert changed==sorted(expected),changed
manifests=['mobile/package.json','mobile/package-lock.json','mobile/jest.config.js']
for name in manifests:
    stored=subprocess.check_output(['git','show',baseline['baselineCommit']+':'+name],cwd=root)
    assert stored.replace(b'\r\n',b'\n')==(work/name).read_bytes().replace(b'\r\n',b'\n'),name
owners=['mobile/src/features/activities/useActivityController.ts','mobile/src/features/activities/ActivityFlowProvider.tsx','mobile/src/ui/ActivityBoundary.tsx',
 'mobile/src/api/client.ts','mobile/src/api/types.ts','mobile/src/lib/rpe.ts','mobile/src/ui-v2/utils/activityViewModel.ts','mobile/src/navigation/TrainingLayout.tsx',
 'mobile/src/navigation/TrainingFlowHost.tsx','mobile/src/ui-v2/components/PendingRpeBanner.tsx']
assert all(actual[name.replace('/', '\\')]==baseline['sourceHashes'][name.replace('/', '\\')] for name in owners)
data={'result':'PASS','baselineCommit':baseline['baselineCommit'],'changed':changed,'protectedUnchanged':len(actual)-len(changed),
 'unchangedOwners':owners,'dependencyManifestsUnchanged':manifests,'canonicalRpeUnchanged':True,'createIdentityValidationRetryStaleAndHrOwnershipUnchanged':True,
 'rpeInteraction':'Same immediate onSelect callback, per-choice ref lock/local pending until promise settles, supplied selection; no staged choice or Save button'}
(HERE/'functional-freeze.json').write_text(json.dumps(data,indent=2)+'\n')
(HERE/'final-source-hashes.json').write_text(json.dumps({'sources':actual,'unchangedManifests':manifests},indent=2)+'\n')
print('Freeze PASS:',len(changed),'presentation/test files;',len(actual)-len(changed),'protected sources unchanged')
