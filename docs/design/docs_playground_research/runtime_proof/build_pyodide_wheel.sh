#!/bin/sh

# Build one reproducible citry_core wheel for the runtime tuple recorded in
# runtime_manifest.json. This proof intentionally requires prepared tools and
# explicit output paths; it never installs another nested xbuild environment.

set -eu

script_dir=$(cd "$(dirname "$0")" && pwd -P)

required_variables="
CITRY_CORE_SOURCE CITRY_CORE_VERSION CITRY_CARGO_HOME
PYODIDE_XBUILDENV_PATH PYODIDE_BUILD_OUT CARGO_TARGET_DIR SOURCE_DATE_EPOCH
"
for variable_name in $required_variables; do
    eval "variable_value=\${$variable_name:-}"
    if [ -z "$variable_value" ]; then
        echo "Missing $variable_name" >&2
        exit 2
    fi
done

case "$SOURCE_DATE_EPOCH" in
    *[!0-9]* | "")
        echo "SOURCE_DATE_EPOCH must be a positive integer" >&2
        exit 2
        ;;
esac

if [ "$SOURCE_DATE_EPOCH" -le 0 ]; then
    echo "SOURCE_DATE_EPOCH must be a positive integer" >&2
    exit 2
fi

runtime_entry="$PYODIDE_XBUILDENV_PATH/314.0.3/xbuildenv/pyodide-root/dist/pyodide.mjs"

if [ ! -f "$runtime_entry" ]; then
    echo "PYODIDE_XBUILDENV_PATH must be the parent containing 314.0.3/xbuildenv" >&2
    echo "Expected $runtime_entry" >&2
    exit 2
fi

if [ ! -f "$CITRY_CORE_SOURCE/pyproject.toml" ]; then
    echo "CITRY_CORE_SOURCE must contain pyproject.toml" >&2
    exit 2
fi

if [ ! -d "$CITRY_CARGO_HOME" ]; then
    echo "CITRY_CARGO_HOME must be an existing Cargo home directory" >&2
    exit 2
fi

citry_core_source=$(cd "$CITRY_CORE_SOURCE" && pwd -P)
source_root=$(cd "$citry_core_source/../../.." && pwd -P)
cargo_home=$(cd "$CITRY_CARGO_HOME" && pwd -P)
if [ ! -f "$source_root/Cargo.toml" ]; then
    echo "CITRY_CORE_SOURCE must be packages/py/citry_core in the Citry workspace" >&2
    exit 2
fi

if find "$citry_core_source/citry_core" \
    \( -type d -name __pycache__ -o -type f -name '*.pyc' \) \
    -print -quit | grep -q .; then
    echo "CITRY_CORE_SOURCE contains Python cache artifacts; build from a clean tag archive" >&2
    exit 2
fi

declared_version=$(awk '
    $0 == "[project]" { in_project = 1; next }
    in_project && /^version = / {
        gsub(/^version = "/, "")
        gsub(/"$/, "")
        print
        exit
    }
' "$citry_core_source/pyproject.toml")
if [ "$declared_version" != "$CITRY_CORE_VERSION" ]; then
    echo "Requested core $CITRY_CORE_VERSION but source declares $declared_version" >&2
    exit 2
fi

mkdir -p "$PYODIDE_BUILD_OUT" "$CARGO_TARGET_DIR"
cargo_target_dir=$(cd "$CARGO_TARGET_DIR" && pwd -P)

rustflags="--remap-path-prefix=$source_root=/citry/source"
rustflags="$rustflags --remap-path-prefix=$cargo_target_dir=/citry/target"
rustflags="$rustflags --remap-path-prefix=$cargo_home=/citry/cargo-home"

PYODIDE_XBUILDENV_PATH="$PYODIDE_XBUILDENV_PATH" \
CARGO_HOME="$cargo_home" \
CARGO_TARGET_DIR="$cargo_target_dir" \
RUSTFLAGS="$rustflags" \
SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH" \
RUSTUP_TOOLCHAIN=1.93.0 \
uvx --python 3.14.2 \
    --from pyodide-cli==0.5.0 \
    --with pyodide-build==0.37.0 \
    --with maturin==1.14.1 \
    pyodide build "$citry_core_source" \
    --outdir "$PYODIDE_BUILD_OUT" -v

wheel_count=$(find "$PYODIDE_BUILD_OUT" -maxdepth 1 -type f \
    -name "citry_core-$CITRY_CORE_VERSION-cp314-cp314-pyemscripten_2026_0_wasm32.whl" \
    | wc -l | tr -d ' ')
if [ "$wheel_count" -ne 1 ]; then
    echo "Expected exactly one core $CITRY_CORE_VERSION PyEmscripten wheel, found $wheel_count" >&2
    exit 1
fi

wheel_path=$(find "$PYODIDE_BUILD_OUT" -maxdepth 1 -type f \
    -name "citry_core-$CITRY_CORE_VERSION-cp314-cp314-pyemscripten_2026_0_wasm32.whl" \
    -print)

normalization_root=$(mktemp -d)
trap 'rm -rf "$normalization_root"' EXIT HUP INT TERM
mkdir "$normalization_root/unpacked" "$normalization_root/packed"
uvx --python 3.14.2 --from wheel==0.46.2 \
    wheel unpack "$wheel_path" --dest "$normalization_root/unpacked"
unpacked_wheel=$(find "$normalization_root/unpacked" -mindepth 1 -maxdepth 1 \
    -type d -name "citry_core-$CITRY_CORE_VERSION" -print)
if [ -z "$unpacked_wheel" ]; then
    echo "Could not find the unpacked core wheel" >&2
    exit 1
fi
uv run --python 3.14.2 --no-project \
    python "$script_dir/normalize_wheel_sbom.py" "$unpacked_wheel" "$source_root"
SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH" \
uvx --python 3.14.2 --from wheel==0.46.2 \
    wheel pack "$unpacked_wheel" --dest-dir "$normalization_root/packed"
normalized_wheel=$(find "$normalization_root/packed" -maxdepth 1 -type f \
    -name "citry_core-$CITRY_CORE_VERSION-cp314-cp314-pyemscripten_2026_0_wasm32.whl" \
    -print)
if [ -z "$normalized_wheel" ]; then
    echo "Could not find the normalized core wheel" >&2
    exit 1
fi
mv "$normalized_wheel" "$wheel_path"

wheel_bytes=$(wc -c < "$wheel_path" | tr -d ' ')
if command -v sha256sum >/dev/null 2>&1; then
    wheel_sha256=$(sha256sum "$wheel_path" | awk '{print $1}')
else
    wheel_sha256=$(shasum -a 256 "$wheel_path" | awk '{print $1}')
fi

printf 'wheel=%s\nbytes=%s\nsha256=%s\n' \
    "$wheel_path" "$wheel_bytes" "$wheel_sha256"
