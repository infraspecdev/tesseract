"""Tests for shield/scripts/lld_blob_sha.py.

Wraps `git hash-object` for stable computation of the LLD canonical's blob SHA
at /plan-draft time. Used by /implement at milestone close to detect fork drift.
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "shield" / "scripts"))

from lld_blob_sha import blob_sha  # noqa: E402


def test_blob_sha_matches_git_hash_object(tmp_path):
    """The helper output must equal `git hash-object` byte-for-byte."""
    p = tmp_path / "lld-foo.md"
    p.write_text("# LLD foo\n\ncontent here\n")
    expected = subprocess.run(
        ["git", "hash-object", str(p)], capture_output=True, text=True, check=True
    ).stdout.strip()
    assert blob_sha(p) == expected


def test_blob_sha_none_for_missing_file(tmp_path):
    """A missing file returns None (caller distinguishes 'net-new' from 'enhancement')."""
    p = tmp_path / "does-not-exist.md"
    assert blob_sha(p) is None


def test_blob_sha_deterministic_across_runs(tmp_path):
    """Same content => same hash."""
    p = tmp_path / "lld-bar.md"
    p.write_text("identical content\n")
    h1 = blob_sha(p)
    p.write_text("identical content\n")
    h2 = blob_sha(p)
    assert h1 == h2


def test_blob_sha_changes_with_content(tmp_path):
    """Different content => different hash."""
    p = tmp_path / "lld-baz.md"
    p.write_text("content A\n")
    h1 = blob_sha(p)
    p.write_text("content B\n")
    h2 = blob_sha(p)
    assert h1 != h2
