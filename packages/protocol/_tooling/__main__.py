"""Print a stable inventory for one protocol schema."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .contracts import inventory_schema, load_json_value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("schema", type=Path)
    parser.add_argument("--schema-id")
    args = parser.parse_args()
    schema = load_json_value(args.schema)
    schema_id = args.schema_id or args.schema.as_posix()
    sys.stdout.write(json.dumps(inventory_schema(schema_id, schema).to_dict(), ensure_ascii=False, indent=2) + "\n")
    return 0


raise SystemExit(main())
