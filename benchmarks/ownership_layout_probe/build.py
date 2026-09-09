"""Build the ownership collector with native offsets for Python-object fields."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
import sysconfig
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = Path("/tmp/citry-ownership-layout")  # noqa: S108 - isolated local experiment directory
TOOLS = Path("/tmp/citry-cython-build")  # noqa: S108 - existing isolated build tools
SOURCE = ROOT / "packages/py/citry/citry/ownership.py"
DIRECTIVES = {"language_level": 3, "annotation_typing": False, "infer_types": False, "binding": True}


def main() -> None:
    """Retain build provenance before any compiled worker imports the artifact."""
    BUILD.mkdir(exist_ok=True)
    copied = BUILD / "ownership.py"
    source = SOURCE.read_text()
    tree = ast.parse(source)
    graph = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "OwnershipGraph")
    init = next(node for node in graph.body if isinstance(node, ast.FunctionDef) and node.name == "__init__")
    fields = sorted(
        {
            node.attr
            for node in ast.walk(init)
            if isinstance(node, ast.Attribute)
            and isinstance(node.ctx, ast.Store)
            and isinstance(node.value, ast.Name)
            and node.value.id == "self"
        }
    )
    if len(fields) != 30:
        raise RuntimeError(f"Unexpected collector field count: {len(fields)}")
    declarations = "\n".join(f"    {name} = cython.declare(object, visibility='public')" for name in fields)
    header = "@cython.cclass\nclass OwnershipGraph:"
    source = source.replace("class OwnershipGraph:", header, 1)
    source = source.replace(
        "    def __init__(self) -> None:",
        "    __dict__ = cython.declare(dict)\n    __weakref__ = cython.declare(object)\n"
        + declarations
        + "\n\n    def __init__(self) -> None:",
        1,
    )
    # Import after future directives, retaining every original method body.
    source = source.replace(
        "from __future__ import annotations", "from __future__ import annotations\n\nimport cython", 1
    )
    copied.write_text(source)
    setup = """from setuptools import Extension, setup
from Cython.Build import cythonize
import Cython
import setuptools
print(f"Cython={Cython.__version__} setuptools={setuptools.__version__}")
setup(ext_modules=cythonize(
    [Extension("citry.ownership", ["ownership.py"])],
    compiler_directives=DIRECTIVES,
))
""".replace("DIRECTIVES", repr(DIRECTIVES))
    (BUILD / "setup.py").write_text(setup)
    result = subprocess.run(
        [sys.executable, "setup.py", "build_ext", "--build-lib", "out", "--build-temp", "temp"],
        cwd=BUILD,
        env={**os.environ, "PYTHONPATH": str(TOOLS)},
        capture_output=True,
        text=True,
        check=False,
    )
    report = {
        "python": sys.version,
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "copied_source_sha256": hashlib.sha256(copied.read_bytes()).hexdigest(),
        "setup_sha256": hashlib.sha256(setup.encode()).hexdigest(),
        "directives": DIRECTIVES,
        "native_object_fields": fields,
        "returncode": result.returncode,
        "build_log": result.stdout + result.stderr,
    }
    generated = BUILD / "ownership.c"
    if generated.exists():
        report["generated_c_sha256"] = hashlib.sha256(generated.read_bytes()).hexdigest()
    artifact = BUILD / "out/citry" / f"ownership{sysconfig.get_config_var('EXT_SUFFIX')}"
    if result.returncode == 0:
        report["artifact"] = str(artifact)
        report["artifact_sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
    (ROOT / "benchmarks/results/repeat-render/ownership-layout-build.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(result.stdout + result.stderr)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
