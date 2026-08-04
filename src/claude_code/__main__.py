"""python -m claude_code 入口，对应源码 main.tsx 的启动路径。"""

from __future__ import annotations

import sys

from claude_code.main import main

if __name__ == "__main__":
    sys.exit(main())
