from pathlib import Path
import hashlib
import json
import re
import subprocess

root = Path(__file__).resolve().parents[4]
evidence = Path(__file__).parent
mobile = root / '.worktrees/wombo-ui-v2-activities/mobile'
before = json.loads((evidence / 'dependency-before.json').read_text())['lock']['packages']
after = json.loads((mobile / 'package-lock.json').read_text())['packages']
diff = {
    'added': {key: after[key] for key in sorted(after.keys() - before.keys())},
    'removed': sorted(before.keys() - after.keys()),
    'changed': {key: {'before': before[key], 'after': after[key]} for key in sorted(before.keys() & after.keys()) if before[key] != after[key]},
}
(evidence / 'lock-audit.json').write_text(json.dumps(diff, indent=2) + '\n')
print('Added:', [(key, value.get('version')) for key, value in diff['added'].items()])
print('Removed:', diff['removed'])
print('Changed existing entries:', list(diff['changed']))
notices = []
metadata = {}
for name in ['lucide-react-native', 'react-native-svg']:
    package = mobile / 'node_modules' / name
    manifest = json.loads((package / 'package.json').read_text())
    license_file = next(p for p in package.iterdir() if p.name.lower() in ['license', 'license.txt', 'license.md'])
    notices.append('## ' + name + ' ' + manifest['version'] + '\n\n' + license_file.read_text(encoding='utf-8'))
    metadata[name] = {key: manifest.get(key) for key in ['version', 'license', 'peerDependencies', 'exports', 'main', 'module']}
    metadata[name]['licenseSha256'] = hashlib.sha256(license_file.read_bytes()).hexdigest()
    metadata[name]['lockIntegrity'] = after['node_modules/' + name]['integrity']
lucide = mobile / 'node_modules/lucide-react-native/dist/esm/lucide-react-native.mjs'
source = (mobile / 'src/ui-v2/primitives/Icon.tsx').read_text()
imports = re.findall(r"import (\w+) from 'lucide-react-native/icons/([^']+)';", source)
names = [name for name, _ in imports]
exports = lucide.read_text()
metadata['verifiedNamedExports'] = {name: bool(re.search(r'\bas ' + name + r'\b', exports)) for name in names}
assert all(metadata['verifiedNamedExports'].values()), metadata['verifiedNamedExports']
metadata['verifiedIndividualExports'] = {}
for name, path in imports:
    file = mobile / 'node_modules/lucide-react-native/dist/esm/icons' / (path + '.mjs')
    declarations = mobile / 'node_modules/lucide-react-native/dist/types/icons' / (path + '.d.ts')
    metadata['verifiedIndividualExports'][name] = file.exists() and declarations.exists() and 'as default' in file.read_text()
assert all(metadata['verifiedIndividualExports'].values())
(mobile / 'THIRD_PARTY_NOTICES.md').write_text('# Visual asset dependency notices\n\nThe original local sport and landscape vectors are project artwork. The dependency notices below must accompany redistribution.\n\n' + '\n\n'.join(notices) + '\n', encoding='utf-8')
(evidence / 'package-verification.json').write_text(json.dumps(metadata, indent=2) + '\n')
(evidence / 'package-lock.diff').write_text(subprocess.check_output(['git', 'diff', '--', 'mobile/package.json', 'mobile/package-lock.json'], cwd=mobile.parent, text=True), encoding='utf-8')
print('Verified named exports:', len(names))
