"""权限与路径边界，对应源码 utils/permissions/。

输入：候选路径与工作区根目录。输出：规范化绝对路径，越界抛 WorkspaceBoundaryError。
"""

from __future__ import annotations

import os
from pathlib import Path


class WorkspaceBoundaryError(ValueError):
    """路径越出工作区边界时抛出。"""


def resolve_path(root: str | Path, candidate: str | Path) -> Path:
    """把候选路径解析为工作区内的绝对路径。

    输入：root 工作区根、candidate 用户提供路径（绝对或相对）。
    输出：规范化 Path；解析后越界或不存在即拒绝。
    """
    root_path = Path(root).resolve()
    candidate_path = Path(candidate).expanduser()
    if not candidate_path.is_absolute():
        candidate_path = root_path / candidate_path
    resolved = candidate_path.resolve()
    if not is_within(root_path, resolved):
        raise WorkspaceBoundaryError(f"path outside workspace: {resolved}")
    return resolved


def is_within(root: str | Path, path: str | Path) -> bool:
    """判断 path 是否位于 root 之内（含 root 本身）。"""
    root_path = Path(root).resolve()
    target = Path(path).resolve()
    try:
        target.relative_to(root_path)
        return True
    except ValueError:
        return False


def safe_join(root: str | Path, *parts: str) -> Path:
    """拼接并校验路径；越界抛 WorkspaceBoundaryError。"""
    joined = Path(root).resolve().joinpath(*parts)
    if not is_within(root, joined):
        raise WorkspaceBoundaryError(f"path outside workspace: {joined}")
    return joined


def env_path_hint() -> str:
    """返回当前工作目录作为环境提示（供错误信息使用）。"""
    return os.getcwd()
