"""路径边界测试：Workspace.resolve_path 的越界拦截。"""

from __future__ import annotations

from pathlib import Path

import pytest

from claude_code.utils.permissions import (
    WorkspaceBoundaryError,
    is_within,
    resolve_path,
)


def test_allows_nested_path(tmp_path: Path) -> None:
    resolved = resolve_path(tmp_path, "sub/dir/file.txt")
    assert resolved == (tmp_path / "sub" / "dir" / "file.txt").resolve()


def test_rejects_parent_escape(tmp_path: Path) -> None:
    with pytest.raises(WorkspaceBoundaryError):
        resolve_path(tmp_path, "../outside.txt")


def test_rejects_absolute_outside(tmp_path: Path) -> None:
    with pytest.raises(WorkspaceBoundaryError):
        resolve_path(tmp_path, "/etc/passwd")


def test_is_within_root_itself(tmp_path: Path) -> None:
    assert is_within(tmp_path, tmp_path)


def test_is_within_sibling_false(tmp_path: Path) -> None:
    sibling = tmp_path.parent / "sibling-dir"
    assert not is_within(tmp_path, sibling)
