from pathlib import Path
import re,json
HERE=Path(__file__).resolve().parent
archive=HERE/'rejected-header-iteration';archive.mkdir(exist_ok=True)
assert archive.resolve().is_relative_to(HERE.resolve())
files=[p for p in HERE.iterdir() if p.is_file() and re.match(r'^(320|360|393|412)-font-',p.name)]
files += [HERE/'case-ledger.json']
for file in files:
    assert file.resolve().parent==HERE.resolve()
    destination=archive/file.name
    assert destination.resolve().parent==archive.resolve() and not destination.exists()
    file.rename(destination)
for folder in ['inspection','atlases']:
    for file in (HERE/folder).glob('*.jpg'):
        destination=archive/folder/file.name;destination.parent.mkdir(exist_ok=True)
        assert file.resolve().is_relative_to(HERE.resolve()) and destination.resolve().is_relative_to(archive.resolve())
        file.rename(destination)
(archive/'rejection.json').write_text(json.dumps({'accepted':False,'reason':'Header decorative layer overlapped the utility row; fixed with opaque foreground utility layering. Non-CI preview also emitted a dev-client duplicate-linking overlay. Final captures require final-2 marker and a cold-start stable CI preview.','filesMoved':len(files)},indent=2)+'\n')
print('Archived rejected initial evidence',len(files),'files')
