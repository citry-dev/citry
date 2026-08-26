"""Build deterministic archives of Citry's standalone example projects."""

from __future__ import annotations

import argparse
import gzip
import io
import stat
import tarfile
from hashlib import sha256
from pathlib import Path

from .catalog import ExampleProject, select_projects

EXCLUDED_PARTS = {".venv", ".pytest_cache", "__pycache__", "_build"}


def project_files(project: ExampleProject) -> tuple[Path, ...]:
    return tuple(
        path
        for path in sorted(project.source.rglob("*"))
        if path.is_file()
        and not any(part in EXCLUDED_PARTS for part in path.relative_to(project.source).parts)
        and path.suffix not in {".pyc", ".pyo"}
    )


def build_archive(project: ExampleProject, destination: Path) -> tuple[Path, Path]:
    destination.mkdir(parents=True, exist_ok=True)
    archive_path = destination / f"{project.id}.tar.gz"
    raw_tar = io.BytesIO()
    with tarfile.open(fileobj=raw_tar, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for source in project_files(project):
            relative = Path(project.id) / source.relative_to(project.source)
            contents = source.read_bytes()
            info = tarfile.TarInfo(relative.as_posix())
            info.size = len(contents)
            info.mtime = 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mode = 0o755 if source.stat().st_mode & stat.S_IXUSR else 0o644
            archive.addfile(info, io.BytesIO(contents))

    with archive_path.open("wb") as output:
        with gzip.GzipFile(fileobj=output, mode="wb", filename="", mtime=0) as compressed:
            compressed.write(raw_tar.getvalue())

    checksum_path = archive_path.with_suffix(archive_path.suffix + ".sha256")
    digest = sha256(archive_path.read_bytes()).hexdigest()
    checksum_path.write_text(f"{digest}  {archive_path.name}\n", encoding="ascii")
    return archive_path, checksum_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build deterministic Citry example archives")
    parser.add_argument("--project", action="append", dest="projects")
    parser.add_argument("--output", type=Path, default=Path("dist/examples"))
    args = parser.parse_args()
    for project in select_projects(args.projects):
        archive, checksum = build_archive(project, args.output)
        print(f"Built {archive} ({checksum.name})")


if __name__ == "__main__":
    main()
