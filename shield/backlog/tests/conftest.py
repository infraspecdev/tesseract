"""pytest conftest — put shield_backlog on sys.path so tests work without
installing the package (kept consistent with other in-repo test suites)."""
import sys
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[1]
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))
