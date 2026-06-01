#!/usr/bin/env python3
"""Emit manifest.js and copy static page assets into the Shield output dir.

manifest.js is a JS-loadable mirror of manifest.json (assigned to
window.SHIELD_MANIFEST) so pages can build nav/dashboard without a fetch()
(which browsers block over file://). The four static assets are copied from
shield/templates/ so the output dir is self-contained.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
STATIC_ASSETS = ["shield.css", "shield-nav.js", "shield-dashboard.js", "index.html"]


def write_assets(output_dir: Path) -> None:
    manifest_path = output_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"manifest.json not found in {output_dir}")
    manifest = json.loads(manifest_path.read_text())
    (output_dir / "manifest.js").write_text(
        "window.SHIELD_MANIFEST = " + json.dumps(manifest, indent=2) + ";\n"
    )
    for name in STATIC_ASSETS:
        shutil.copyfile(TEMPLATES_DIR / name, output_dir / name)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", required=True, type=Path,
                    help="Shield output dir (contains manifest.json)")
    args = ap.parse_args()
    try:
        write_assets(args.output_dir)
    except FileNotFoundError as e:
        print(f"write_shield_assets: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
