# WOMBO Git Workspace Health Report

Date: 2026-11-03 (Europe/Amsterdam).
Scope: local investigation and non-destructive workspace hygiene only.

## Outcome

**WOMBO GIT WORKSPACE ISSUE DIAGNOSED — SAFE CORRECTION PENDING**

Safe local exclusions are applied. The original root remains above the VS Code
active-change limit because its untracked UI evidence includes required
deliverables. Those files remain visible and untouched. No broad evidence,
documentation, source, or screenshot exclusion was added.

The latest cumulative remediation head is
`e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6` on
`fix/wombo-end-to-end-performance`. Its existing worktree has zero tracked
changes and zero untracked entries. This is the integrated head of the requested
remediation chain, not a merge into `main`.

## Repository identity and root cause

- Root: `F:/Projecten Business/Start23/Code`.
- Root Git directory and common directory:
  `F:/Projecten Business/Start23/Code/.git`.
- Root branch: `fix/pre-ui-beta-blockers`, HEAD
  `6bb3a047139d91c71ac065c35a8af595221b54c5`.
- `main`, local `origin/main`, and `integration/wombo-ui-v2-main` point to
  `aff74558d0a6511286a4a84a44ea25a03ca57549`.
- The A9 linked worktree has its own HEAD/index under
  `.git/worktrees/wombo-end-to-end-performance`, sharing the common object
  database and refs.

VS Code is inspecting the older root checkout with `git status -z -uall`.
Before correction this returns 12,906 change entries: 3 modified tracked files
and 12,903 untracked entries. The main contributor is
`docs/ui/evidence/` (12,446 entries before excluding Python bytecode).
No files under that evidence path are tracked on the root's current branch.
7,485 untracked `docs/ui/` paths also exist in the A9 commit's tree; this is
path overlap, not a claim that every file's contents match. Other branches track
many of these deliverables. The old root checkout therefore sees substantial
evidence from later work as untracked.

The evidence contains accepted PNG/XML/JSON capture triples, audit records,
review helper scripts, and linked inspection images. For example,
`docs/ui/evidence/final-visual-batch-5/README.md` describes hash-bound accepted
captures, and the Batch 9 report generator links inspection images and retained
rejected-run records. They cannot all be classified as disposable build output.
Ignoring the entire evidence tree would violate the instruction to keep required
deliverables visible.

## Counts

Counts use NUL-delimited `git status --porcelain=v1 --untracked-files=all`.

| Measurement | Before | After exclusions | Final, including this report |
| --- | ---: | ---: | ---: |
| Modified tracked files | 3 | 3 | 3 |
| Untracked status entries | 12,903 | 12,607 | 12,608 |
| Untracked regular files listed by root Git | 12,878 | 12,607 | 12,608 |
| Nested repository directory entries | 25 | 0 | 0 |
| Total active change entries | 12,906 | 12,610 | 12,611 |

The 25 directory entries are Git repository boundaries, not counts of every
physical file inside those worktrees. Their independent statuses were inspected
separately. Ignored dependencies and caches still exist on disk and are not
included in these untracked counts.

The three existing modified tracked files remain unchanged by this task:

| Path | Existing diff (+ / -) | SHA-256 of working file, unchanged |
| --- | --- | --- |
| `.vscode/tasks.json` | 15 / 8 | `dec87810c742ea3fb0ca138a0586c6d709d215e921fbe09df96b75ebd1dba7c2` |
| `backend/app/modules/coach/weekly_plan.py` | 1 / 1 | `d54f73c59ad521c8816d18de3e4d04cdde36f56e211400dee7ad57dde0ed5c17` |
| `docs/deployment-tasks.md` | 66 / 0 | `e2d07bac8063432b0bb219bdd4afb823913e4f51e7d002b9adc03b36daef00be` |

No staged changes were present or created.

### Largest contributing directories before correction

| Directory | Untracked entries |
| --- | ---: |
| `docs/` | 12,626 |
| `docs/ui/` (within docs) | 12,622 |
| `docs/ui/evidence/` (within docs/ui) | 12,446 |
| `.worktrees/` | 267 |
| `%SystemDrive%/ProgramData/Microsoft/Windows/Caches/` | 4 |
| `.npm-cache/` | 3 |
| `scripts/` | 3 |

| Evidence batch | Untracked entries before correction |
| --- | ---: |
| final-visual-batch-9 | 2,367 |
| final-visual-batch-5 | 1,845 |
| final-visual-batch-8 | 1,519 |
| final-visual-batch-7 | 1,396 |
| final-visual-batch-11 | 1,353 |
| final-visual-batch-4 | 964 |
| final-visual-batch-12 | 845 |
| final-visual-batch-6 | 738 |
| final-visual-batch-2 | 479 |
| final-visual-batch-3 | 373 |
| final-visual-batch-1b | 364 |
| final-visual-batch-1a | 160 |
| final-visual-batch-0 | 28 |
| ui-v2-main-switch | 13 |
| final-visual-batch-10 | 2 |

After exclusions, evidence still contributes 12,424 files. Other deliverables,
including reference screenshots, mockups, privacy documents, requirements PDFs,
and local scripts, remain visible.

## Changes made

Appended this block to the existing common `.git/info/exclude`, preserving its
original bytes as a prefix:

```gitignore
# WOMBO local workspace hygiene (2026-11-03); preserve all files and histories
/.worktrees/
/.npm-cache/
/%SystemDrive%/ProgramData/Microsoft/Windows/Caches/
/docs/ui/evidence/**/__pycache__/
```

The original exclude file SHA-256 was
`6671fe83b7a07c8932ee89164d1f2793b2318058eb8b98dc5c06ee0a5a3b0ec1`.
The initial sandbox blocked metadata writes; the authorized append succeeded
through the escalation mechanism. No automatic approval rejection remains.

These patterns remove 296 status entries: 267 from the local worktree container,
3 npm cache files, 4 Windows cache files, and 22 generated Python bytecode files.
The worktree container includes 25 registered nested worktrees plus a local
`wombo-ui-v2-final-batch-11-source` copy contributing 242 files. The copy and all
worktrees remain on disk. The root's exclusion of this workspace container does
not remove or alter their independent Git histories.

The common exclude file is local metadata shared by linked worktrees; its
root-anchored patterns are evaluated relative to each checkout. Rechecking each
linked worktree verified that no existing worktree changes were hidden by these
patterns.

Created `docs/audits/WOMBO_GIT_WORKSPACE_HEALTH_REPORT.md`.
No shared `.gitignore`, application code, VS Code setting, branch, or commit
was changed. The local exclusion change will not propagate through a commit.

## Generated artifacts and line endings

Existing ignore rules already cover the observed `mobile/node_modules/`,
`mobile/.expo/`, `mobile/android/`, `mobile/dist/`, `backend/.venv/`,
`backend/.pytest_cache/`, `backend/.mypy_cache/`, `backend/.ruff_cache/`,
`.runtime/`, and `tmp/`. Their presence is not the primary cause.
`git check-ignore -v` verified the matching existing and added rules.
No caches, reports, dependencies, or build output were deleted.

The installed Git system configuration sets `core.autocrlf=true`.
`git ls-files --eol` reports `i/lf w/lf` for all three modified tracked
files. `git diff --ignore-space-at-eol --stat` still reports their substantive
changes (82 insertions, 9 deletions). There is no mass tracked-file modification
or line-ending churn. Git's prospective LF-to-CRLF warnings do not explain the
12,903 untracked entries. No line-ending configuration was changed.

## VS Code findings and remaining verification gate

Inspected the installed built-in Git extension manifests under both local
VS Code version directories, `261c84cb1e` and `e646868227`.
Both specify:

| Setting | Installed default |
| --- | --- |
| `git.statusLimit` | 10,000 |
| `git.untrackedChanges` | `mixed` |
| `git.ignoreLimitWarning` | `false` |
| `git.autoRepositoryDetection` | `true` |
| `git.repositoryScanMaxDepth` | 1 |

No Git overrides were found in the user's VS Code settings. No profile settings
files were found, and root/mobile `.vscode/settings.json` files are absent.
VS Code workspace storage identifies the open workspace as the root folder.
The current-session Git log records the root and the Joren simulator worktree
as opened repositories and confirms use of `git status -z -uall`.

The final root count of 12,611 exceeds the installed default by 2,611.
**Normal root-folder Git functionality is not established; the warning remains
expected.** No setting was raised, untracked files were not globally hidden, and
the warning was not suppressed. A UI refresh/reload was not used to claim
restoration.

The existing clean A9 worktree is below this limit locally. To inspect the latest
cumulative remediation in its own VS Code window without changing the root
checkout, the user can open:

```powershell
code --new-window 'F:\Projecten Business\Start23\Code\.worktrees\wombo-end-to-end-performance'
```

That is an available workflow, not evidence that the original root warning has
been resolved. No editor window was opened or closed by this task.

A complete root correction requires a separate decision on the intended root
branch and the retention/versioning of its untracked UI deliverables. Any later
branch switch requires first safeguarding the existing modified and untracked
work and checking for file collisions. No checkout, staging, commit, move,
deletion, or merge of those deliverables was performed or assumed authorized.
No deletion proposal is required for the corrections made here.

The Git log also contains a historical `getDefaultBranch` lookup warning;
this task did not change remote/upstream configuration.

## Remediation ancestry and preservation

Every consecutive ancestor check below returned exit code 0 with
`git merge-base --is-ancestor`. `git log --all --ancestry-path A9..`
returned no descendants among existing refs. Only
`fix/wombo-end-to-end-performance` contains A9 among local/remote branches.

| Phase | Preserved head | Verified relation |
| --- | --- | --- |
| A10 | `11591b9924ebfd3872314deecb82c57fc278126b` | Base of the requested chain |
| A3 | `b65ea78be1db886586d793f721bb2910ddbc6a41` | Previous row is an ancestor; 2 additional commits |
| A4 | `4bb0cdea8f46242018ad8e5d22fa79a706cbf207` | Previous row is an ancestor; 2 additional commits |
| A5 | `044ecfb59ee00afb91f35b68dc9fa4e5d3e4e9cf` | Previous row is an ancestor; 2 additional commits |
| A6 | `24b27ebd34ccfe662ca57994a736f4f853af8d0b` | Previous row is an ancestor; 2 additional commits |
| A7 | `75f172d4161f71a763247b04c027fd165901afbd` | Previous row is an ancestor; 2 additional commits |
| A8 | `d0e726dfd291ffde12a459ec430b11fdc5cddc7a` | Previous row is an ancestor; 4 additional commits |
| A9 | `e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6` | Previous row is an ancestor; 8 additional commits |

All eight remediation worktrees are clean. Their completed commits remain
reachable through their existing named branches. All 35 local branch refs,
the remote-tracking ref, tag ref, and existing Codex refs match the initial
ref-name/SHA snapshot. `git fsck --connectivity-only --no-dangling` completed
successfully. No fetch or remote-backup verification was performed; preservation
verified here is local.

### Worktree inventory

All 27 registered worktree paths exist and remain available. Paths beginning
`.worktrees/` are relative to the repository root. Counts below are independent
worktree statuses at initial inspection, with the one observed concurrent
addition annotated.

| Worktree | Branch/state | HEAD | Tracked changes | Untracked entries |
| --- | --- | --- | ---: | ---: |
| Root | `fix/pre-ui-beta-blockers` | `6bb3a047139d91c71ac065c35a8af595221b54c5` | 3 | 12903 |
| `.worktrees/audit-wombo-full-system-review` | `audit/wombo-full-system-review` | `aff74558d0a6511286a4a84a44ea25a03ca57549` | 0 | 59 |
| `.worktrees/catalog-capacity-fresh-athlete` | `fix/catalog-capacity-fresh-athlete` | `6b1189b70a6505726fef70c4616a2f3d6dd4c94a` | 0 | 0 |
| `.worktrees/joren-training-engine-simulator` | `docs/joren-training-engine-simulator` | `2cc3dc85fef98edddf4732282e8ebcd1e8c43455` | 0 | 0 → 1 during inspection |
| `.worktrees/wombo-account-scoped-plan-recovery` | `fix/wombo-account-scoped-plan-recovery` | `24b27ebd34ccfe662ca57994a736f4f853af8d0b` | 0 | 0 |
| `.worktrees/wombo-activity-cache-synchronization` | `fix/wombo-activity-cache-synchronization` | `75f172d4161f71a763247b04c027fd165901afbd` | 0 | 0 |
| `.worktrees/wombo-auth-network-recovery` | `fix/wombo-auth-network-recovery` | `d0e726dfd291ffde12a459ec430b11fdc5cddc7a` | 0 | 0 |
| `.worktrees/wombo-checkin-plan-handoff` | `fix/wombo-checkin-plan-handoff` | `4bb0cdea8f46242018ad8e5d22fa79a706cbf207` | 0 | 0 |
| `.worktrees/wombo-checkin-proposal-recovery` | `fix/wombo-checkin-proposal-recovery` | `044ecfb59ee00afb91f35b68dc9fa4e5d3e4e9cf` | 0 | 0 |
| `.worktrees/wombo-checkin-restriction-roundtrip` | `fix/wombo-checkin-restriction-roundtrip` | `b65ea78be1db886586d793f721bb2910ddbc6a41` | 0 | 0 |
| `.worktrees/wombo-end-to-end-performance` | `fix/wombo-end-to-end-performance` | `e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6` | 0 | 0 |
| `.worktrees/wombo-mobile-verification-gate` | `fix/wombo-mobile-verification-gate` | `11591b9924ebfd3872314deecb82c57fc278126b` | 0 | 0 |
| `.worktrees/wombo-ui-v2-active-workout-moves` | `feat/wombo-ui-v2-active-workout-moves` | `7d0b6d6bd8c2c1648b1c7199130801431537e09a` | 0 | 0 |
| `.worktrees/wombo-ui-v2-activities` | `feat/wombo-ui-v2-activities` | `19c23d58f0b71aea01478df2306e2492a515e36e` | 53 | 28 |
| `.worktrees/wombo-ui-v2-activity-controller` | `feat/wombo-ui-v2-activity-controller` | `697f9e82a0c265036fe535674231f2476b9e1435` | 0 | 0 |
| `.worktrees/wombo-ui-v2-final-batch-10` | `feat/wombo-ui-v2-final-batch-10` | `f25379d04dad914a99144d7dab7e005f8ca29b03` | 0 | 0 |
| `.worktrees/wombo-ui-v2-final-batch-11` | `feat/wombo-ui-v2-final-batch-11` | `75fa8916be5a69d0ad4d3ba7a439bcb9e1a3560c` | 0 | 0 |
| `.worktrees/wombo-ui-v2-final-batch-12` | `feat/wombo-ui-v2-final-batch-12` | `569cfc60702f10252f059feaa169c2f07ca4c5cb` | 0 | 0 |
| `.worktrees/wombo-ui-v2-first-plan-provenance` | Detached HEAD | `1a5138f0626460e11558c788083a7aef4cc799f3` | 0 | 0 |
| `.worktrees/wombo-ui-v2-main` | `integration/wombo-ui-v2-main` | `aff74558d0a6511286a4a84a44ea25a03ca57549` | 0 | 0 |
| `.worktrees/wombo-ui-v2-navigation-shell` | `feat/wombo-ui-v2-navigation-shell` | `30a7b6e60697844635f2b58b5fc1a1dab4ae289d` | 0 | 0 |
| `.worktrees/wombo-ui-v2-planning-controller` | `feat/wombo-ui-v2-planning-controller` | `5200d0ce6fd2d267390f4517ccadba4bea1353e6` | 0 | 0 |
| `.worktrees/wombo-ui-v2-planning-creation` | `feat/wombo-ui-v2-planning-creation` | `addaffc7300d745e72017abcadd5cab486b5b8b7` | 0 | 0 |
| `.worktrees/wombo-ui-v2-proposal-review` | `feat/wombo-ui-v2-proposal-review` | `bf10fde0bfa6ced4fb8ebd99d71b4f88acbb57e4` | 0 | 0 |
| `.worktrees/wombo-ui-v2-week` | `feat/wombo-ui-v2-calendar-readonly` | `c68cdf5a9f7e62b6f609f2ae9cf8abfe50600960` | 0 | 0 |
| `.worktrees/wombo-ui-v2-workout-detail` | Detached HEAD | `45e948484f769516ba1d1626641b71a62e50d58c` | 2 | 2 |
| `F:/wv2` | `sync/wombo-ui-v2-first-plan-provenance` | `23243e027b9674308c13d9c946dc03ce90a01c55` | 0 | 0 |

During inspection, the Joren simulator worktree gained the untracked file
`docs/requirements/Specificatie Realized TSS Matrix.pdf`. This task did not
create or modify it. Every other linked worktree's NUL-delimited status snapshot
remained identical before and after the exclusions. Existing uncommitted work
in the Activities and detached Workout Detail worktrees was left untouched.
Detached worktree HEADs remain registered; neither was pruned.

### Complete local branch inventory

All entries below are unchanged from the initial snapshot.

| Branch | Commit |
| --- | --- |
| `audit/wombo-full-system-review` | `aff74558d0a6511286a4a84a44ea25a03ca57549` |
| `backup/wombo-ui-v2-final-batch-10-before-squash` | `7cbe01b3f3d659ab128568146d2024e4fd8421ef` |
| `docs/joren-training-engine-simulator` | `2cc3dc85fef98edddf4732282e8ebcd1e8c43455` |
| `feat/wombo-ui-v2` | `19c23d58f0b71aea01478df2306e2492a515e36e` |
| `feat/wombo-ui-v2-active-workout-moves` | `7d0b6d6bd8c2c1648b1c7199130801431537e09a` |
| `feat/wombo-ui-v2-activities` | `19c23d58f0b71aea01478df2306e2492a515e36e` |
| `feat/wombo-ui-v2-activity-controller` | `697f9e82a0c265036fe535674231f2476b9e1435` |
| `feat/wombo-ui-v2-calendar-readonly` | `c68cdf5a9f7e62b6f609f2ae9cf8abfe50600960` |
| `feat/wombo-ui-v2-final-batch-10` | `f25379d04dad914a99144d7dab7e005f8ca29b03` |
| `feat/wombo-ui-v2-final-batch-11` | `75fa8916be5a69d0ad4d3ba7a439bcb9e1a3560c` |
| `feat/wombo-ui-v2-final-batch-12` | `569cfc60702f10252f059feaa169c2f07ca4c5cb` |
| `feat/wombo-ui-v2-final-batch-7` | `70568a80c0d19a88cd6b47fe1184a16ed7b4a7a1` |
| `feat/wombo-ui-v2-final-batch-8` | `2b5c7753bde1e5dae2446da40c12469a29bf855e` |
| `feat/wombo-ui-v2-final-batch-9` | `5891858fb9fd44fa3f83a636f6e18abc8f39008b` |
| `feat/wombo-ui-v2-navigation-shell` | `30a7b6e60697844635f2b58b5fc1a1dab4ae289d` |
| `feat/wombo-ui-v2-planning-controller` | `5200d0ce6fd2d267390f4517ccadba4bea1353e6` |
| `feat/wombo-ui-v2-planning-creation` | `addaffc7300d745e72017abcadd5cab486b5b8b7` |
| `feat/wombo-ui-v2-proposal-review` | `bf10fde0bfa6ced4fb8ebd99d71b4f88acbb57e4` |
| `feat/wombo-ui-v2-week` | `7a7259125d2a6a907cf9c175379ae6570aabf71b` |
| `feat/wombo-ui-v2-week-refinement` | `43a365b91ceaab2fc030e1ab2bd04f61bcf0964c` |
| `feat/wombo-ui-v2-workout-detail` | `45e948484f769516ba1d1626641b71a62e50d58c` |
| `fix/catalog-capacity-fresh-athlete` | `6b1189b70a6505726fef70c4616a2f3d6dd4c94a` |
| `fix/pre-ui-beta-blockers` | `6bb3a047139d91c71ac065c35a8af595221b54c5` |
| `fix/wombo-account-scoped-plan-recovery` | `24b27ebd34ccfe662ca57994a736f4f853af8d0b` |
| `fix/wombo-activity-cache-synchronization` | `75f172d4161f71a763247b04c027fd165901afbd` |
| `fix/wombo-auth-network-recovery` | `d0e726dfd291ffde12a459ec430b11fdc5cddc7a` |
| `fix/wombo-checkin-plan-handoff` | `4bb0cdea8f46242018ad8e5d22fa79a706cbf207` |
| `fix/wombo-checkin-proposal-recovery` | `044ecfb59ee00afb91f35b68dc9fa4e5d3e4e9cf` |
| `fix/wombo-checkin-restriction-roundtrip` | `b65ea78be1db886586d793f721bb2910ddbc6a41` |
| `fix/wombo-end-to-end-performance` | `e2d450be4a1d5ec3d65037bd6901f2f03d6b14e6` |
| `fix/wombo-mobile-verification-gate` | `11591b9924ebfd3872314deecb82c57fc278126b` |
| `integration/wombo-ui-v2-main` | `aff74558d0a6511286a4a84a44ea25a03ca57549` |
| `main` | `aff74558d0a6511286a4a84a44ea25a03ca57549` |
| `remediation/phase-13-14-r6-entry-audit` | `9c6be883918255a92644a8c69525a2d6cf14b071` |
| `sync/wombo-ui-v2-first-plan-provenance` | `23243e027b9674308c13d9c946dc03ce90a01c55` |

Additional unchanged refs:

- `refs/codex/turn-diffs/captures/1793666620580/bdeca089-038d-4745-bca5-88eb082d9019/base`: `f7d5c9dbafb74a2127de68acebd05ff184f2cf62`.
- `refs/codex/turn-diffs/checkpoints/6d1979203c636e829afc33cd8600d679/64b64218b81d35fb2743a3fae7dbd77e/1793109153358/6abf025e-9f48-4a35-bfbd-5d2c2d3cdfa7`: `09f92006aa457b518b97629c26a5e41a7c887b91`.
- `refs/remotes/origin/main`: `aff74558d0a6511286a4a84a44ea25a03ca57549`.
- `refs/tags/wombo-ui-v1-pre-v2-6bb3a04`: `d39bfcd2cf6dcc17aca231502ac4ab4e46c0465a`.

## Verification and no-data-loss statement

- Inspected normal status and full untracked status, worktree porcelain,
  branches, ancestry, Git/common directories, ignore/exclude rules,
  generated directories, EOL diagnostics, installed VS Code settings, and logs.
- Verified all 27 worktree paths and HEADs, unchanged refs, A9 presence and
  ancestry, clean remediation statuses, and object connectivity.
- Immediately before/after the exclusion append, checked all 12,878 initially
  enumerated untracked regular files: zero missing paths and zero size changes.
  This was a preservation check, not a full content-hash audit of every artifact.
- SHA-256 hashes of the three pre-existing modified root files are unchanged.
- No actual application code changed. Only the local exclude append and this
  audit report were written by this task.
- No files, worktrees, reports, commits, or branches were removed or discarded.
  No reset, clean, prune, history rewrite, force-push, or global Git configuration
  change occurred.
- No push, merge, or deployment occurred. No new commit was created.
- The reported 850 backend tests, 887 mobile tests, TypeScript, unused-code,
  privacy, Ruff, and mypy results are prior A9 verification supplied by the user;
  they were not rerun for this metadata/documentation-only task.
- Open verification gate: the original root remains over the active-change
  limit; application release and database gates in earlier audit reports are
  outside this task and are not declared complete here.

**WOMBO GIT WORKSPACE ISSUE DIAGNOSED — SAFE CORRECTION PENDING**

