"""拒绝缺失平台、空文件和不完整的 CLI 归档。"""

import io
from pathlib import Path
import tarfile
import tempfile
import unittest

from verify_release_assets import verify


class ReleaseAssetsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        for name in ('Zap-arm64.dmg', 'Zap-intel.dmg', 'ZapSetup.exe',
                     'Zap-x86_64.AppImage', 'zap_2026.10.18.1_amd64.deb'):
            (self.path / name).write_bytes(b'package')
        for platform in ('macos-aarch64', 'macos-x86_64', 'linux-x86_64'):
            with tarfile.open(self.path / f'zap-{platform}.tar.gz', 'w:gz') as archive:
                for name in ('zap-oss', 'resources/THIRD_PARTY_LICENSES.txt'):
                    member = tarfile.TarInfo(name)
                    member.size = 1
                    member.mode = 0o755 if name == 'zap-oss' else 0o644
                    archive.addfile(member, io.BytesIO(b'x'))

    def test_complete_release(self):
        self.assertEqual(len(verify(self.path, 'v2026.10.18.1')), 8)

    def test_missing_platform_is_rejected(self):
        (self.path / 'Zap-intel.dmg').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing release assets'):
            verify(self.path, 'v2026.10.18.1')

    def test_empty_package_is_rejected(self):
        (self.path / 'ZapSetup.exe').write_bytes(b'')
        with self.assertRaisesRegex(ValueError, 'Empty or invalid'):
            verify(self.path, 'v2026.10.18.1')

    def test_incomplete_cli_is_rejected(self):
        with tarfile.open(self.path / 'zap-linux-x86_64.tar.gz', 'w:gz') as archive:
            member = tarfile.TarInfo('zap-oss')
            member.size, member.mode = 1, 0o755
            archive.addfile(member, io.BytesIO(b'x'))
        with self.assertRaisesRegex(ValueError, 'Missing CLI resources'):
            verify(self.path, 'v2026.10.18.1')

    def test_wrong_version_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Missing release assets'):
            verify(self.path, 'v2026.10.18.2')

    def test_unexpected_file_is_rejected(self):
        (self.path / 'release-body.md').write_text('notes')
        with self.assertRaisesRegex(ValueError, 'Unexpected release asset'):
            verify(self.path, 'v2026.10.18.1')
