"""工具层测试：Read/Edit/Write/Bash/Glob/Grep 与注册表结构化错误。"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from claude_code.tools import assemble_tool_pool
from claude_code.types.ids import ToolUseId


def _tid() -> ToolUseId:
    return ToolUseId(f"test-{uuid4().hex[:8]}")


def test_read_file_returns_content(tmp_path: Path) -> None:
    target = tmp_path / "x.txt"
    target.write_text("content-1", encoding="utf-8")
    registry = assemble_tool_pool(tmp_path)
    result = registry.execute("Read", {"path": "x.txt"}, _tid())
    assert not result.is_error
    assert result.content == "content-1"


def test_read_rejects_outside_workspace(tmp_path: Path) -> None:
    registry = assemble_tool_pool(tmp_path)
    result = registry.execute("Read", {"path": "/etc/hosts"}, _tid())
    assert result.is_error


def test_edit_requires_unique_match(tmp_path: Path) -> None:
    target = tmp_path / "y.txt"
    target.write_text("dup dup", encoding="utf-8")
    registry = assemble_tool_pool(tmp_path)
    result = registry.execute(
        "Edit", {"path": "y.txt", "old_string": "dup", "new_string": "x"}, _tid()
    )
    assert result.is_error
    assert "exactly once" in result.content


def test_write_creates_file(tmp_path: Path) -> None:
    registry = assemble_tool_pool(tmp_path)
    result = registry.execute("Write", {"path": "new.txt", "content": "hello"}, _tid())
    assert not result.is_error
    assert (tmp_path / "new.txt").read_text(encoding="utf-8") == "hello"


def test_bash_disabled_by_default(tmp_path: Path) -> None:
    registry = assemble_tool_pool(tmp_path)
    assert "Bash" not in registry.names()


def test_bash_executes_when_enabled(tmp_path: Path) -> None:
    registry = assemble_tool_pool(tmp_path, enable_bash=True)
    result = registry.execute("Bash", {"command": "pwd"}, _tid())
    assert not result.is_error
    assert str(tmp_path.resolve()) in result.content


def test_glob_lists_files(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("", encoding="utf-8")
    (tmp_path / "b.txt").write_text("", encoding="utf-8")
    registry = assemble_tool_pool(tmp_path)
    result = registry.execute("Glob", {"pattern": "*.py"}, _tid())
    assert result.content == "a.py"


def test_grep_finds_matches(tmp_path: Path) -> None:
    (tmp_path / "s.py").write_text("def foo():\n    pass\n", encoding="utf-8")
    registry = assemble_tool_pool(tmp_path)
    result = registry.execute("Grep", {"pattern": "foo"}, _tid())
    assert "s.py:1" in result.content


def test_registry_returns_structured_error_for_unknown_tool(tmp_path: Path) -> None:
    registry = assemble_tool_pool(tmp_path)
    result = registry.execute("NoSuchTool", {}, _tid())
    assert result.is_error
    assert "unknown tool" in result.content
