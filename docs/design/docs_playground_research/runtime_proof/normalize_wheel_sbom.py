from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Replace the local workspace path in generated wheel SBOMs.")
    parser.add_argument("unpacked_wheel", type=Path)
    parser.add_argument("source_root")
    args = parser.parse_args()

    unpacked_wheel = args.unpacked_wheel.resolve()
    source_bytes = args.source_root.encode()
    replacement = "/citry/source"
    replacements = 0

    sbom_files = sorted(unpacked_wheel.glob("*.dist-info/sboms/*.json"))
    if not sbom_files:
        raise SystemExit("The wheel contains no generated JSON SBOM")

    for sbom_file in sbom_files:
        original = sbom_file.read_text(encoding="utf-8")
        occurrences = original.count(args.source_root)
        if occurrences == 0:
            continue
        normalized = original.replace(args.source_root, replacement)
        json.loads(normalized)
        sbom_file.write_text(normalized, encoding="utf-8")
        replacements += occurrences

    if replacements == 0:
        raise SystemExit("The generated SBOM did not contain the source root")

    for wheel_file in unpacked_wheel.rglob("*"):
        if wheel_file.is_file() and source_bytes in wheel_file.read_bytes():
            raise SystemExit(f"Source root remains in {wheel_file}")


if __name__ == "__main__":
    main()
