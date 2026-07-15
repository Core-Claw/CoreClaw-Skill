# CoreClaw Agent Skill

[English](README.md) | [简体中文](README.zh-CN.md)

本仓库把 CoreClaw OpenAPI v2 的 worker 工作流封装为 AI Agent 可使用的 skill。它以 MCP 为首选入口，仅面向 v2 接口，覆盖 worker 发现、schema 检查、运行、轮询、结果读取、文件导出、日志排查、重跑、停止和账号额度检查。

## 文件结构

```text
.
|-- .claude-plugin/
|   |-- marketplace.json
|   `-- plugin.json
|-- .mcp.json
|-- agents/
|   `-- openai.yaml
|-- openapi.json
|-- skills/
|   `-- coreclaw/
|       |-- SKILL.md
|       `-- references/
|           |-- coreclaw-v2-workflow.md
|           |-- error-handling.md
|           |-- mcp-tools.md
|           `-- rest-api-fallback.md
`-- scripts/
    |-- generate_references.py
    `-- validate_skill.py
```

## 运行入口

- 托管 MCP endpoint：`https://mcp.coreclaw.com/mcp`
- REST API base URL：`https://openapi.coreclaw.com`
- API namespace：`/api/v2`
- REST fallback 环境变量：`CORECLAW_API_KEY`
- 推荐 REST 鉴权：`Authorization: Bearer $CORECLAW_API_KEY`
- 脚本需要 Python 3.9+（仅用标准库，无需安装第三方包）

## 使用 Skill

把本目录安装到支持 skill 的客户端后，可以显式调用，也可以用自然语言触发：

```text
Use $coreclaw to find a worker for coffee shop data, inspect its input schema, run it, and preview the first 20 records.
```

Skill 提供操作流程。要执行真实 CoreClaw 操作，请配置 CoreClaw MCP server，或在 REST fallback 场景设置 `CORECLAW_API_KEY`。

## 作为 Claude Code 插件安装（推荐）

把本仓库作为插件市场添加，两行命令完成安装：

```bash
claude plugin marketplace add Core-Claw/CoreClaw-Skill
claude plugin install coreclaw@coreclaw-skill
```

或在 Claude Code 会话内：

```text
/plugin marketplace add Core-Claw/CoreClaw-Skill
/plugin install coreclaw@coreclaw-skill
```

插件自带 CoreClaw MCP server（`.mcp.json`）和 skill。安装后设置一次 API token，MCP server 才能鉴权：

```bash
export CORECLAW_API_KEY="your-coreclaw-token"        # macOS/Linux
```

```powershell
$env:CORECLAW_API_KEY = "your-coreclaw-token"        # Windows PowerShell
```

通过插件调用时，skill 的命名空间为 `/coreclaw-skill:coreclaw`。

## 配置 MCP

支持 MCP 的 Agent 优先使用托管 MCP 服务：

```json
{
  "mcpServers": {
    "coreclaw": {
      "url": "https://mcp.coreclaw.com/mcp",
      "headers": {
        "api-key": "your-coreclaw-token"
      }
    }
  }
}
```

MCP 服务支持 `api-key`、`X-API-Key` 和 `Authorization: Bearer <token>`，并统一转发为 CoreClaw 上游 Bearer 鉴权。

## 导入 Codex Desktop

Codex 的 skill 布局要求 `SKILL.md` 位于 `<skills-dir>/coreclaw/SKILL.md`。本仓库把 skill 放在 `skills/coreclaw/` 下，因此先把仓库 clone 到工作目录，再把该子目录暴露给 Codex：

```powershell
git clone https://github.com/Core-Claw/CoreClaw-Skill.git "$env:USERPROFILE\CoreClaw-Skill"
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.codex\skills\coreclaw" -Target "$env:USERPROFILE\CoreClaw-Skill\skills\coreclaw"
```

然后重启 Codex Desktop。Codex 看到的 skill 路径为：

```text
%USERPROFILE%\.codex\skills\coreclaw\SKILL.md
```

如果 Codex Desktop 提供从文件夹或 zip 导入的界面，请指向 `skills/coreclaw` 目录（其根目录包含 `SKILL.md`）。不要导入仓库根目录。

更新已安装的 Codex Desktop skill：

```powershell
cd "$env:USERPROFILE\CoreClaw-Skill"
git pull
```

更新后重启 Codex Desktop。

## 作为独立 Claude Code Skill 使用

直接 clone 到 Claude Code skills 目录（无需 manifest、无需安装步骤）：

```bash
git clone https://github.com/Core-Claw/CoreClaw-Skill.git ~/.claude/skills/coreclaw
```

skill 以 `/coreclaw` 加载（无命名空间）。仓库自带的 `.mcp.json` 只有在作为插件安装时才会自动注册 CoreClaw MCP server；独立使用时需自行配置 MCP server 或设置 `CORECLAW_API_KEY`（见 [配置 MCP](#配置-mcp) 与 [REST Fallback](#rest-fallback)）。

## 导入其他支持 Skill 的 Agent

对于 Claude Code 和 Codex Desktop 以外的客户端，遵循同一个结构规则：把 `skills/coreclaw` 目录放到对应 agent 的 skills 目录，且 `SKILL.md` 位于 skill 根目录。如果客户端支持显式 skill 调用，使用 `$coreclaw`。

如果客户端不支持自动发现 skill，可手动附加或引用：

- `skills/coreclaw/SKILL.md`
- `agents/openai.yaml`
- `skills/coreclaw/references/`
- `openapi.json`

## 打包 Skill

打包前先验证仓库：

```bash
python scripts/validate_skill.py
```

如果安装了 Codex skill-creator 工具链，也可以跑它的校验脚本（可选，路径依赖具体机器）：

```bash
python "$USERPROFILE/.codex/skills/.system/skill-creator/scripts/quick_validate.py" .   # Windows
python "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" .           # macOS/Linux
```

在 Windows 的仓库根目录创建 zip 包：

```powershell
New-Item -ItemType Directory -Force dist
$files = @("skills", "agents", "openapi.json", ".mcp.json", ".claude-plugin", "scripts", "LICENSE", "README.md", "README.zh-CN.md")
Compress-Archive -Path $files -DestinationPath dist/coreclaw-skill.zip -Force
```

在 macOS/Linux 的仓库根目录创建 zip 包：

```bash
mkdir -p dist
zip -r dist/coreclaw-skill.zip skills agents openapi.json .mcp.json .claude-plugin scripts LICENSE README.md README.zh-CN.md -x "*/__pycache__/*" "*.pyc"
```

压缩包根目录必须直接包含 `.claude-plugin/` 和 `skills/coreclaw/SKILL.md`。分发前建议解压后再次验证：

```bash
python scripts/validate_skill.py
```

## MCP 能力范围

CoreClaw MCP server 暴露 37 个公开工具，覆盖：

- 发现和预检
- 已保存 worker task 的 CRUD（创建、查看、更新、更新输入、删除）
- 直接运行 worker
- 运行已保存的 worker task
- 批量运行 worker（`run_workers_batch`）
- 查询和轮询 run（`poll_run`）、结构化判定（`verify_run`）
- 预览结果
- 导出 CSV/JSON
- 查看日志（支持 `grep` 进程内过滤）
- 重跑
- 停止运行

Skill 捆绑公开的 34 个 CoreClaw API v2 操作；MCP server 暴露 37 个工具（34 个与这些操作 1:1 对应，另有 `poll_run`、`verify_run`、`run_workers_batch` 三个编排工具）。完整工具矩阵见 `references/mcp-tools.md`。

## Agent 工作流

1. 用 `list_store_workers` 查公开 marketplace worker，或用 `list_workers` 查当前用户的 worker。
2. 在 `run_worker` 前必须调用 `get_worker_input_schema`。
3. 用 `run_worker` 发送符合 schema 的临时输入，或用 `run_worker_task` 运行已保存任务，或用 `run_workers_batch` 一次运行多个 worker。
4. 保存返回的运行标识为 `run_id`。
5. 轮询 run detail 直到终态——`poll_run` 带超时等待，`verify_run` 返回结构化的 `PASS`/`ERROR_RECORD` 判定。
6. 小结果用 list-result 工具预览，大结果用 export 工具导出。
7. run 失败或结果异常时先查 run detail，再查日志。

## REST fallback

只有在 MCP 不可用或用户明确要求 HTTP 示例时才使用 REST。设置 API key 时不要提交真实密钥：

```bash
export CORECLAW_API_KEY="your-coreclaw-token"
```

PowerShell：

```powershell
$env:CORECLAW_API_KEY = "your-coreclaw-token"
```

REST 只使用 `/api/v2` 接口。curl 示例见 `references/rest-api-fallback.md`。

## 维护命令

从同级源码仓库重新生成引用材料：

```bash
python scripts/generate_references.py --copy-openapi
```

验证 skill 包：

```bash
python scripts/validate_skill.py
```

如果安装了 Codex skill-creator 工具链，也可以跑它的 `quick_validate.py`（可选，路径依赖具体机器，见“打包 Skill”一节）。

预期契约：

- bundled public OpenAPI operations：34
- 公开 MCP tools：37
- 排除 operations：3
- skill 文档中不再出现旧 v1 工作流术语

## 示例提示词

- "用 CoreClaw 找一个采集 coffee shop 数据的 worker，读取 schema，运行后预览前 20 条记录。"
- "运行这个已保存的 CoreClaw task，异步轮询到完成，然后导出 CSV。"
- "这个 CoreClaw run 失败了。请查看 run detail 和日志，带 request id 说明原因。"
- "重跑最新一次 CoreClaw worker run，并告诉我新的 run id。"
