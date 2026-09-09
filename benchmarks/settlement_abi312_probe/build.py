"""Build the explicit-state rendering pipeline against the Python 3.12 stable ABI."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.settlement_state_probe.transform import transform  # noqa: E402

BUILD = Path("/tmp/citry-settlement-abi312")  # noqa: S108 - isolated experiment
TOOLS = Path("/tmp/citry-cython-build")  # noqa: S108 - isolated existing tools
SOURCES = {
    "citry.component_render": "packages/py/citry/citry/component_render.py",
    "citry.nodes": "packages/py/citry/citry/nodes/__init__.py",
    "citry.slots": "packages/py/citry/citry/slots.py",
}
DIRECTIVES = {"language_level": 3, "annotation_typing": False, "infer_types": False, "binding": True}


def main() -> None:
    """Preserve source identity and build diagnostics for all requested modules."""
    BUILD.mkdir(exist_ok=True)
    modules = {}
    extensions = []
    for name, relative in SOURCES.items():
        source = ROOT / relative
        copied = BUILD / f"{name.rsplit('.', 1)[1]}.py"
        transformation = None
        if name == "citry.component_render":
            transformed, transformation = transform(source.read_text())
            copied.write_text(transformed)
        else:
            copied.write_bytes(source.read_bytes())
        modules[name] = {"source": relative, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
        modules[name]["copied_source_sha256"] = hashlib.sha256(copied.read_bytes()).hexdigest()
        modules[name]["transformation"] = transformation
        extensions.append(
            f"Extension({name!r}, [{copied.name!r}], "
            "define_macros=[('Py_LIMITED_API', '0x030C0000')], py_limited_api=True)"
        )
    setup = "\n".join(
        [
            "from setuptools import Extension, setup",
            "from Cython.Build import cythonize",
            "import Cython, setuptools",
            'print(f"Cython={Cython.__version__} setuptools={setuptools.__version__}")',
            f"setup(ext_modules=cythonize([{', '.join(extensions)}], compiler_directives={DIRECTIVES!r}))",
        ]
    )
    (BUILD / "setup.py").write_text(setup)
    result = subprocess.run(
        [sys.executable, "setup.py", "build_ext", "--build-lib", "out", "--build-temp", "temp"],
        cwd=BUILD,
        env={**os.environ, "PYTHONPATH": str(TOOLS)},
        capture_output=True,
        text=True,
        check=False,
    )
    for name, metadata in modules.items():
        generated = BUILD / f"{name.rsplit('.', 1)[1]}.c"
        if generated.exists():
            metadata["generated_c_sha256"] = hashlib.sha256(generated.read_bytes()).hexdigest()
        artifact = BUILD / "out" / (name.replace(".", "/") + ".abi3.so")
        if result.returncode == 0:
            metadata["artifact"] = str(artifact)
            metadata["artifact_sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
    report = {
        "python": sys.version,
        "modules": modules,
        "directives": DIRECTIVES,
        "limited_api": "0x030C0000",
        "setup_sha256": hashlib.sha256(setup.encode()).hexdigest(),
        "returncode": result.returncode,
        "build_log": result.stdout + result.stderr,
        "transform_sha256": hashlib.sha256(
            (ROOT / "benchmarks/settlement_state_probe/transform.py").read_bytes()
        ).hexdigest(),
    }
    (ROOT / "benchmarks/results/performance-render/settlement-abi312-build.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(result.stdout + result.stderr)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
