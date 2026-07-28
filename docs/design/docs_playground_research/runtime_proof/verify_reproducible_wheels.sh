#!/bin/sh

set -eu

if [ "$#" -lt 2 ]; then
    echo "Usage: $0 FIRST_WHEEL SECOND_WHEEL [FORBIDDEN_BUILD_PATH ...]" >&2
    exit 2
fi

first_wheel=$1
second_wheel=$2
shift 2

for wheel_path in "$first_wheel" "$second_wheel"; do
    if [ ! -f "$wheel_path" ]; then
        echo "Wheel does not exist: $wheel_path" >&2
        exit 2
    fi
done

if ! cmp -s "$first_wheel" "$second_wheel"; then
    echo "Wheel bytes differ" >&2
    exit 1
fi

for forbidden_path in "$@"; do
    if [ -z "$forbidden_path" ]; then
        echo "Forbidden build paths must not be empty" >&2
        exit 2
    fi
    if unzip -p "$first_wheel" | strings | LC_ALL=C grep -F "$forbidden_path" >/dev/null; then
        echo "Wheel contains a local build path: $forbidden_path" >&2
        exit 1
    fi
done

if command -v sha256sum >/dev/null 2>&1; then
    wheel_sha256=$(sha256sum "$first_wheel" | awk '{print $1}')
else
    wheel_sha256=$(shasum -a 256 "$first_wheel" | awk '{print $1}')
fi

printf 'reproducible=true\nlocal_paths_absent=true\nsha256=%s\n' "$wheel_sha256"
