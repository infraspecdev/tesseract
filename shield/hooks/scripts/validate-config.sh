#!/usr/bin/env bash
set -euo pipefail

# Validate a JSON config file against a JSON schema
# Usage: validate-config.sh <config-file> <schema-file>
# Exit 0 if valid, exit 1 with error message if invalid
# Falls back silently (exit 0) if jsonschema is not installed

CONFIG_FILE="${1:-}"
SCHEMA_FILE="${2:-}"

if [ -z "$CONFIG_FILE" ] || [ -z "$SCHEMA_FILE" ]; then
  echo "Usage: validate-config.sh <config-file> <schema-file>" >&2
  exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
  echo "Config file not found: $CONFIG_FILE" >&2
  exit 1
fi

if [ ! -f "$SCHEMA_FILE" ]; then
  echo "Schema file not found: $SCHEMA_FILE" >&2
  exit 1
fi

python3 -c "
import sys
try:
    import json, jsonschema
    config = json.load(open(sys.argv[1]))
    schema = json.load(open(sys.argv[2]))
    jsonschema.validate(config, schema)
except ImportError:
    sys.exit(0)
except json.JSONDecodeError as e:
    print(f'Invalid JSON in {sys.argv[1]}: {e}', file=sys.stderr)
    sys.exit(1)
except jsonschema.ValidationError as e:
    print(f'Config validation error: {e.message}', file=sys.stderr)
    sys.exit(1)
" "$CONFIG_FILE" "$SCHEMA_FILE"
