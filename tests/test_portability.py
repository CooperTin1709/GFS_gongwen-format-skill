from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from docx import Document

from scripts.package_skill import build_archive


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / 'samples' / 'browser_input.txt'


def run_deployed_e2e(skill_root: Path, outside_cwd: Path) -> dict[str, object]:
    input_path = outside_cwd / 'browser_input.txt'
    output_path = outside_cwd / 'output'
    input_path.write_text(SAMPLE.read_text(encoding='utf-8'), encoding='utf-8')
    completed = subprocess.run(
        [
            sys.executable,
            '-X',
            'utf8',
            str(skill_root / 'scripts' / 'main.py'),
            '--text-file',
            str(input_path),
            '--output-dir',
            str(output_path),
        ],
        cwd=outside_cwd,
        text=True,
        encoding='utf-8',
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr + completed.stdout)
    result = json.loads((output_path / 'result.json').read_text(encoding='utf-8'))
    Document(output_path / 'formatted.docx')
    return {'summary': json.loads(completed.stdout), 'result': result}


class DeploymentPortabilityTests(unittest.TestCase):
    def test_skill_commands_use_posix_entry_path(self) -> None:
        for name in ('SKILL.md', 'README.md'):
            text = (ROOT / name).read_text(encoding='utf-8')
            self.assertNotIn('scripts' + chr(92) + 'main.py', text)
            self.assertNotIn('.' + chr(92) + 'scripts' + chr(92), text)
        skill_text = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        self.assertIn('python3 scripts/main.py', skill_text)
        self.assertNotIn('/home/runner/', skill_text)

    def test_source_entry_runs_from_non_skill_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            outcome = run_deployed_e2e(ROOT, Path(directory))
            self.assertEqual(outcome['summary']['status'], 'SUCCESS')
            self.assertTrue(outcome['result']['validation_passed'])

    def test_zip_members_and_extracted_chinese_space_path_e2e(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            archive = build_archive(temporary / 'deployment.zip')
            with zipfile.ZipFile(archive) as bundle:
                names = bundle.namelist()
                self.assertTrue(all(chr(92) not in name for name in names))
                self.assertIn('SKILL.md', names)
                self.assertIn('scripts/main.py', names)
                self.assertIn('config/format_rules.json', names)
                deployed_root = temporary / '公文 格式 Skill'
                bundle.extractall(deployed_root)
            outside_cwd = temporary / '非 Skill 工作目录'
            outside_cwd.mkdir()
            outcome = run_deployed_e2e(deployed_root, outside_cwd)
            self.assertEqual(outcome['summary']['status'], 'SUCCESS')
            self.assertTrue(outcome['result']['validation_passed'])
            self.assertTrue(outcome['result']['validation']['text_identical'])


if __name__ == '__main__':
    unittest.main()
