from pathlib import Path
HERE=Path(__file__).resolve().parent
mobile=HERE.parents[3]/'.worktrees/wombo-ui-v2-activities/mobile'
for name in ['ActivityEntryScreen.tsx','ActivityFeedbackScreen.tsx']:
    file=mobile/'src/ui-v2/screens'/name
    lines=file.read_text(encoding='utf-8').splitlines()
    inside=False
    for i,line in enumerate(lines):
        if line.startswith('      <Card') and '</Card>' not in line:inside=True;continue
        if line.startswith('      </Card>'):inside=False;continue
        if inside:lines[i]='  '+line
    file.write_text('\n'.join(lines)+'\n',encoding='utf-8')
