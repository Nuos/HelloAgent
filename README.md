# HelloAgent — Claude Code Python

Claude Code 类 Agent 的 Python 教学/开发实现。**目录命名对齐 `chinasiro-claude-code-sourcemap` 还原源码（v2.1.88）的 `restored-src/src/` 结构**，实现按 R1 范围（最小可运行闭环）重新搭建，不照搬 docs 中的既有实现。

## 目录结构与源码映射

```
src/
├── claude_code/                  # 核心运行时 ← restored-src/src
│   ├── main.py                   #   ← main.tsx（CLI 入口）
│   ├── QueryEngine.py            #   ← QueryEngine.ts（核心查询循环）
│   ├── Tool.py                   #   ← Tool.ts（工具契约）
│   ├── Task.py                   #   ← Task.ts（占位）
│   ├── query/                    #   ← query.ts + query/（config/deps/stopHooks/tokenBudget）
│   ├── tools/                    #   ← tools.ts + tools/（池装配 + 每工具一目录）
│   │   ├── BashTool/  FileReadTool/  FileEditTool/  FileWriteTool/  GlobTool/  GrepTool/
│   ├── context/                  #   ← context.ts + context/（CLAUDE.md 装配）
│   ├── state/                    #   ← state/（会话消息链）
│   ├── types/                    #   ← types/（消息、事件、权限、ID）
│   ├── utils/permissions/        #   ← utils/permissions/（路径边界）
│   ├── cli/  commands/  services/api/  entrypoints/  constants/  schemas/
│   ├── plugins/  skills/  memdir/  coordinator/  remote/  server/  bridge/
│   ├── bootstrap/  assistant/  migrations/  outputStyles/  tasks/  native_ts/
│   └── moreright/  upstreamproxy/  cost_tracker.py  cost_hook.py  history.py  setup.py
└── claude_code_ui/               # UI 独立模块（源码 UI 目录整体占位，与核心隔离）
    └── components/ screens/ ink/ buddy/ hooks/ vim/ voice/ keybindings/ …
```

同名文件与目录冲突（如 `tools.ts` + `tools/`）在 Python 中合并为目录 `__init__.py`；
含连字符的目录名（`native-ts`）转为下划线（`native_ts`）。

## 快速启动

> ⚠️ **前提：必须先激活项目 venv**（`claude_code` 只装在 `.venv` 里，系统 `python3` 看不到）。
> 每个新终端窗口都要执行一次 `source .venv/bin/activate`；
> 或者不激活，全程用 `.venv/bin/python -m claude_code`。

## 启动方式（共 6 种，均实测可用）

### 方式（1）：终端 REPL —— 激活 venv 后启动（推荐）

```bash
cd ~/dev-workspace/agent-dev/HelloAgent
source .venv/bin/activate
python -m claude_code
```

启动后看到横幅 `Claude Code Python REPL — 模型: demo | /help 查看命令，/exit 退出`。
在 `>>>` 提示符输入问题回车即可对话；`/exit` 退出。

### 方式（2）：终端 REPL —— 不激活 venv，直接指定 venv 解释器

```bash
cd ~/dev-workspace/agent-dev/HelloAgent
.venv/bin/python -m claude_code
```

效果与方式（1）相同，无需激活，适合一次性使用。

### 方式（3）：终端单次查询（不进入 REPL，跑完即退）

```bash
cd ~/dev-workspace/agent-dev/HelloAgent
source .venv/bin/activate
```

激活后任选一条（每一条都是完整命令，一次执行一条）：

```bash
# (3a) 文本路径：模型直接回答
python -m claude_code "hello"

# (3b) 工具路径：读取文件（Read → 结果回灌 → 最终响应）
python -m claude_code "/read README.md"

# (3c) 工具路径：执行命令（Bash 默认禁用，须显式 --enable-bash）
python -m claude_code --enable-bash "/bash pwd"

# (3d) 命令：查看帮助
python -m claude_code "/help"

# (3e) 真实模型单次：读取 ~/.hellollm/config.json 自动配置
python -m claude_code --model openai "你好"

# (3f) 真实模型 + 工具：自然语言触发工具调用
python -m claude_code --model openai --max-turns 6 "请读取 README.md 文件，然后告诉我这个项目是做什么的"
```

不激活 venv 时，把上面的 `python` 全部换成 `.venv/bin/python` 即可，例如：

```bash
cd ~/dev-workspace/agent-dev/HelloAgent
.venv/bin/python -m claude_code "/read README.md"
```

### 方式（4）：VS Code 启动 REPL（demo 模型）

1. 打开 VS Code：`code ~/dev-workspace/agent-dev/HelloAgent`
2. 按 `Ctrl+Shift+D` 打开"运行和调试"面板
3. 面板顶部**下拉框**选择配置：`HelloAgent (REPL)`
4. 按 **F5**
5. 集成终端弹出 REPL，`>>>` 提示符输入问题

配置位于 `.vscode/launch.json`：`program` 指向 `src/claude_code/main.py`，
`python` 指向 `.venv/bin/python`，`env` 含 `NO_PROXY=api.deepseek.com`。

### 方式（5）：VS Code 启动 REPL（真实模型）

1. 打开 VS Code：`code ~/dev-workspace/agent-dev/HelloAgent`
2. 按 `Ctrl+Shift+D` 打开"运行和调试"面板
3. 面板顶部**下拉框**选择配置：`HelloAgent (REPL Real Model)`
4. 按 **F5**
5. 集成终端弹出 REPL，横幅显示 `模型: openai:deepseek-v4-flash`，直接对话

⚠️ 注意：**在 `main.py` 文件上直接按 F5 是"当前文件"调试（demo 模型）**，
不会读取 launch.json 配置。要真实模型必须在调试面板下拉框选配置再 F5。

### 方式（6）：运行测试（pytest + 质量门）

```bash
cd ~/dev-workspace/agent-dev/HelloAgent
source .venv/bin/activate

# (6a) 运行全部测试（当前 69 个用例）
python -m pytest

# (6b) 一键质量门（pytest + ruff check + ruff format + mypy，四道全跑）
python -m pytest && ruff check src tests && ruff format --check src tests && mypy src

# (6c) VS Code 任务方式：Ctrl+Shift+P → Tasks: Run Task → Quality Gate
```

VS Code 里也可用测试面板（左侧试管图标）逐个运行用例。

### 交互式 REPL（多轮对话）

```bash
python -m claude_code            # 无参数进入 REPL；或 -i/--interactive
>>> hello
>>> /read README.md
>>> /model openai                # 会话内切换真实模型（读 ~/.hellollm/config.json）
>>> /model demo                  # 切回离线替身
>>> /exit
```

会话跨轮共享上下文；`/help`、`/exit`、`/quit` 为内置命令，Ctrl-D 退出。
模型切换是**会话内换挡**（`/model openai`），启动参数 `--model openai` 是**启动时选档**。

### 真实模型后端

默认 `DemoModelClient` 是离线替身。接入 OpenAI 兼容 API（deepseek / aihub / openai），
配置思路对齐 HelloLLM：**唯一本地来源 `~/.hellollm/config.json`**（chmod 600）：

```bash
python -m claude_code --model openai "你好"          # 自动读取 ~/.hellollm/config.json
python -m claude_code --model openai -i              # 真实模型 REPL（横幅显示模型名）
```

配置格式（`~/.hellollm/config.json`）：

```json
{
  "api_key": "sk-...",
  "api_base": "https://api.deepseek.com",
  "model": "deepseek-chat",
  "timeout": 120
}
```

优先级：`--api-key/--api-base/--llm-model/--timeout` 参数 > 环境变量
（`OPENAI_API_KEY/OPENAI_BASE_URL/OPENAI_MODEL`）> 配置文件
（`--config <path>` 指定或默认 `~/.hellollm/config.json`）。
缺 key 时打印创建引导（mkdir + cat + chmod 600）。

真实模型支持工具调用（自然语言触发 Read/Edit/Write/Bash/Glob/Grep），
工具 schema 自动转换，结果回灌后模型继续推理。

配置加载日志：启动/切换模型时输出 `[config] INFO`（配置文件路径、加载字段、
key 前 4 位打码），供 VS Code 调试排查——看到 `API key 已加载: sk-1...` 即读取成功。

### VS Code 运行与调试

配置位于 `.vscode/`（launch.json / tasks.json / settings.json，风格对齐 HelloLLM）：

| 操作 | 方法 |
|---|---|
| 启动 REPL（demo） | 运行和调试面板（`Ctrl+Shift+D`）→ 下拉选 `HelloAgent (REPL)` → F5 |
| 启动 REPL（真实模型） | 下拉选 `HelloAgent (REPL Real Model)` → F5 |
| 一键质量门 | `Ctrl+Shift+P` → `Tasks: Run Task` → `Quality Gate`（pytest+ruff+mypy） |
| 建环境 | `Tasks: Run Task` → `Bootstrap Python 3.14 Environment` |
| 运行测试 | 测试面板（试管图标）或集成终端 `python -m pytest` |

两个 REPL 配置均指向 `src/claude_code/main.py`（program 方式，同 HelloLLM），
显式 venv 解释器 + `NO_PROXY=api.deepseek.com`（deepseek 直连绕过代理）。
注意：**在 main.py 文件上直接 F5 是"当前文件"调试（demo 模型）**，
要真实模型请在调试面板下拉选 `HelloAgent (REPL Real Model)`。

## 质量门

```bash
pytest
ruff check src tests
ruff format --check src tests
mypy src
```

当前状态：69 个测试用例全绿；ruff / mypy strict 全过。

## R1 范围与边界

已实现：UserRequest → CLI/REPL → QueryEngine → ModelClient（Demo 离线替身 / OpenAI 兼容真实模型）
→ ToolRegistry → Workspace 路径边界 → Read/Edit/Write/Glob/Grep/Bash → tool_result 回灌
→ 最终文本；max_turns 终止；结构化工具错误；真实模型工具调用（自然语言触发）。

明确不做（后续阶段）：deny/ask/allow 权限规则、审批 UI、Hook、沙箱、
JSONL 持久化、上下文压缩、MCP/Plugins/Skills/Subagent、桌面版界面。
