from __future__ import annotations

import zipfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = SKILL_ROOT / 'dist' / 'GFSV4_gongwen-format-skill.zip'
ROOT_FILES = ('SKILL.md', 'README.md')
PACKAGE_DIRECTORIES = ('agents', 'config', 'references', 'scripts')
EXCLUDED_PARTS = {'__pycache__'}


def iter_package_files() -> list[Path]:
    files = [SKILL_ROOT / name for name in ROOT_FILES]
    for directory_name in PACKAGE_DIRECTORIES:
        directory = SKILL_ROOT / directory_name
        files.extend(
            path
            for path in directory.rglob('*')
            if path.is_file()
            and not EXCLUDED_PARTS.intersection(path.parts)
            and path.suffix != '.pyc'
        )
    return sorted(files, key=lambda path: path.relative_to(SKILL_ROOT).as_posix())


def build_archive(output: str | Path = DEFAULT_ARCHIVE) -> Path:
    archive = Path(output).resolve()
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in iter_package_files():
            arcname = path.relative_to(SKILL_ROOT).as_posix()
            bundle.write(path, arcname=arcname)
    return archive


if __name__ == '__main__':
    print(build_archive())
