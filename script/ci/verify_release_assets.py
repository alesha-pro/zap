#!/usr/bin/env python3
"""校验跨平台发布产物，并记录源码版本和 SHA-256。"""

import hashlib
import json
import os
from pathlib import Path
import sys
import tarfile


def verify(directory, tag):
    required = {
        'Zap-arm64.dmg', 'Zap-intel.dmg', 'ZapSetup.exe',
        'Zap-x86_64.AppImage', f'zap_{tag.removeprefix("v")}_amd64.deb',
        'zap-macos-aarch64.tar.gz', 'zap-macos-x86_64.tar.gz',
        'zap-linux-x86_64.tar.gz',
    }
    files = {p.name: p for p in directory.iterdir()}
    missing = required - files.keys()
    if missing:
        raise ValueError(f'Missing release assets: {sorted(missing)}')
    for name, path in files.items():
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f'Empty or invalid asset: {name}')
        if name not in required and not name.endswith(('.rpm', '.pkg.tar.zst')):
            raise ValueError(f'Unexpected release asset: {name}')
        if name.endswith('.tar.gz'):
            with tarfile.open(path, 'r:gz') as archive:
                binary = archive.getmember('zap-oss')
                if not binary.isfile() or binary.size == 0 or not binary.mode & 0o111:
                    raise ValueError(f'Missing executable CLI in {name}')
                if not any(m.name.startswith('resources/') for m in archive.getmembers()):
                    raise ValueError(f'Missing CLI resources in {name}')
    return sorted(files.values())


def main():
    directory = Path(sys.argv[1])
    assets = verify(directory, os.environ['RELEASE_TAG'])
    metadata = directory / 'BUILD_INFO.json'
    metadata.write_text(json.dumps({
        'tag': os.environ['RELEASE_TAG'],
        'commit': os.environ['RELEASE_COMMIT'],
        'repository': os.environ['GITHUB_REPOSITORY'],
        'run_id': os.environ['GITHUB_RUN_ID'],
        'macos_signing': 'ad-hoc; not notarized',
        'windows_signing': 'unsigned',
    }, indent=2) + '\n')
    assets.append(metadata)
    lines = []
    for path in sorted(assets):
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
        lines.append(f'{digest.hexdigest()}  {path.name}\n')
    (directory / 'SHA256SUMS').write_text(''.join(lines))
    print(f'Verified {len(assets) - 1} release assets; generated BUILD_INFO.json and SHA256SUMS')


if __name__ == '__main__':
    main()
