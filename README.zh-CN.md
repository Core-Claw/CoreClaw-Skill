# CoreClaw Agent Skill

[English](README.md) | [简体中文](README.zh-CN.md)

本仓库把 CoreClaw OpenAPI v2 的 worker 工作流封装为 AI Agent 可使用的 skill。它以 MCP 为首选入口，仅面向 v2 接口，覆盖 worker 发现、schema 检查、运行、轮询、结果读取、文件导出、日志排查、重跑、停止和账号额度检查。

## 文件结构

```text
.
├── SKILL.md
├── agents/openai.yaml
├── openapi.json
├── references/
│   ├── coreclaw-v2-workflow.md
│   ├── error-handling.md
│   ├── mcp-tools.md
│   └── rest-api-fallback.md
└── scripts/
    ├── generate_references.py
    └── validate_skill.py
```

## 运行入口

- 托管 MCP endpoint：`https://mcp.coreclaw.com/mcp`
- REST API base URL：`https://openapi.coreclaw.com`
- API namespace：`/api/v2`
- REST fallback 环境变量：`CORECLAW_API_KEY`
- 推荐 REST 鉴权：`Authorization: Bearer $CORECLAW_API_KEY`

## MCP 配置

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

## MCP 能力范围

CoreClaw MCP server 暴露 28 个公开工具，覆盖：

- 发现和预检
- 直接运行 worker
- 运行已保存的 worker task
- 查询和轮询 run
- 预览结果
- 导出 CSV/JSON
- 查看日志
- 重跑
- 停止运行

Skill 只暴露公开的 28 个 CoreClaw MCP/API v2 操作。完整工具矩阵见 `references/mcp-tools.md`。

## Agent 工作流

1. 用 `list_store_workers` 查公开 marketplace worker，或用 `list_workers` 查当前用户的 worker。
2. 在 `run_worker` 前必须调用 `get_worker_input_schema`。
3. 用 `run_worker` 发送符合 schema 的临时输入，或用 `run_worker_task` 运行已保存任务。
4. 保存返回的运行标识为 `run_id`。
5. 轮询 run detail 直到终态。
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
python C:/Users/user/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

预期契约：

- bundled public OpenAPI operations：28
- 公开 MCP tools：28
- 排除 operations：3
- skill 文档中不再出现旧 v1 工作流术语

## 示例提示词

- "用 CoreClaw 找一个采集 coffee shop 数据的 worker，读取 schema，运行后预览前 20 条记录。"
- "运行这个已保存的 CoreClaw task，异步轮询到完成，然后导出 CSV。"
- "这个 CoreClaw run 失败了。请查看 run detail 和日志，带 request id 说明原因。"
- "重跑最新一次 CoreClaw worker run，并告诉我新的 run id。"
