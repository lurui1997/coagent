from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass


@dataclass
class ClaudeResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def combined(self) -> str:
        return f"{self.stdout}\n{self.stderr}".strip()

    @property
    def is_rate_limited(self) -> bool:
        text = self.combined.lower()
        return self.returncode != 0 and any(
            k in text for k in ("429", "rate limit", "rate_limit", "too many requests", "overloaded")
        )


def resolve_claude_bin() -> str:
    explicit = os.environ.get("CLAUDE_BIN", "").strip()
    if explicit:
        return explicit
    for name in ("claude", "tclaude"):
        path = shutil.which(name)
        if path:
            return path
    return "claude"


def claude_print(prompt: str, *, timeout_s: float | None = None) -> ClaudeResult:
    """非交互调用本地 Claude Code CLI（-p / --print）。"""
    bin_path = resolve_claude_bin()
    timeout = timeout_s or float(os.environ.get("CLAUDE_TIMEOUT_S", "120"))
    proc = subprocess.run(
        [bin_path, "-p", prompt],
        capture_output=True,
        text=True,
        timeout=timeout,
        stdin=subprocess.DEVNULL,
    )
    return ClaudeResult(proc.returncode, proc.stdout or "", proc.stderr or "")
