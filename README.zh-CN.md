# CoreClaw Agent Skill

[English](README.md) | [简体中文](README.zh-CN.md)

这个仓库把 CoreClaw 的使用方式整理成给 AI Agent 使用的 Skill。Agent 可以按固定流程完成：寻找 scraper、读取 live schema、启动运行、轮询状态、读取结果、导出文件、查看日志、重跑任务、中止任务，以及检查账号额度。

仓库保持精简：

```text
.
├── LICENSE
├── README.md
├── README.zh-CN.md
├── SKILL.md
└── openapi.json
```

## 文件说明

- `SKILL.md`：给 Agent 的操作手册。支持 Skill 的 Agent 会读取它并按流程工作。
- `openapi.json`：接口契约，包含端点、参数和响应结构。
- `README.md` / `README.zh-CN.md`：给人看的安装、使用和维护说明。
- `LICENSE`：仓库许可证。

## 安装 Skill

### Codex

把整个仓库放到 Codex skills 目录：

```bash
~/.codex/skills/coreclaw
```

Windows 常见路径：

```powershell
$env:USERPROFILE\.codex\skills\coreclaw
```

复制后重启 Codex。

### Claude Code 或其他支持 Skill 的 Agent

把整个仓库放到对应 Agent 的 skills 目录，并确保 `SKILL.md` 位于该目录根部。

如果宿主不支持自动发现 Skill，可以手动把以下文件提供给 Agent：

- `SKILL.md`
- `openapi.json`

## 运行条件

- API 基础地址：`https://openapi.coreclaw.com`
- 环境变量：`CORECLAW_API_KEY`
- 请求头：`api-key: $CORECLAW_API_KEY`
- 必需命令行工具：`curl`
- 可选命令行工具：`jq`，用于格式化和过滤 JSON

设置 API Key：

```bash
export CORECLAW_API_KEY="your_api_key"
```

PowerShell：

```powershell
$env:CORECLAW_API_KEY = "your_api_key"
```

不要把真实 API Key 提交到仓库。

## Agent 应该怎么工作

安全流程如下：

1. 用 `/api/store` 搜索 scraper。
2. 用 `/api/scraper` 读取 scraper detail。
3. 读取 `data.version`、`data.parameters.custom` 和 `data.parameters.system`。
4. 根据 live schema 组织 `input.parameters.custom`。
5. 用 `/api/v1/scraper/run` 启动运行。
6. 保存 `run_slug`。
7. 用 `/api/v1/run/detail` 轮询状态。
8. 用 `/api/v1/run/result/list` 读取结果，或用 `/api/v1/run/result/export` 导出文件。
9. 如果失败，用 `/api/v1/run/last/log` 查看日志。

最关键的一点：`data.parameters.custom` 是 schema 描述，不是可以直接复制到 `input.parameters.custom` 的运行 payload。

## 12 个核心 API 能力

| 能力 | 接口 |
| --- | --- |
| 搜索市场中的 scraper | `GET /api/store` |
| 获取 scraper detail 和 live schema | `GET /api/scraper` |
| 启动 scraper 运行 | `POST /api/v1/scraper/run` |
| 中止运行中的任务 | `POST /api/v1/scraper/abort` |
| 查看历史运行列表 | `POST /api/v1/run/list` |
| 获取运行详情和状态 | `POST /api/v1/run/detail` |
| 分页读取结果 | `POST /api/v1/run/result/list` |
| 导出结果文件 | `POST /api/v1/run/result/export` |
| 读取最新日志 | `POST /api/v1/run/last/log` |
| 重跑历史任务 | `POST /api/v1/rerun` |
| 运行已保存任务模板 | `POST /api/v1/task/run` |
| 查询账号额度 | `POST /api/v1/account/info` |

## 示例提示词

- “帮我找一个适合抓 Amazon 商品列表的 CoreClaw scraper，读取 live schema，用关键词 `wireless mouse` 跑一次，并展示前 20 条结果。”
- “异步启动这个 scraper，保存 `run_slug`，持续轮询直到完成；如果结果超过 50 条，就导出 CSV。”
- “这次运行失败了。请查看 run detail 和最新日志，说明真正的失败原因。”
- “用这个历史 `run_slug` 重新运行一次，跟踪新任务，并预览前 10 条结果。”

## MCP 方式

如果 Agent 支持 MCP，可以配置 CoreClaw 远程 MCP 服务，让 Agent 调用命名工具，而不是手写 HTTP 请求：

```json
{
  "mcpServers": {
    "coreclaw": {
      "url": "https://mcp.coreclaw.com/mcp",
      "headers": {
        "api-key": "scraper_api_YOUR_KEY_HERE"
      }
    }
  }
}
```

MCP 提供工具，Skill 提供操作方法：搜索、读取 schema、运行、跟踪、取结果、排错。

## 维护检查

发布变更前先运行：

```bash
git diff --check
node -e "JSON.parse(require('fs').readFileSync('openapi.json','utf8'))"
```

并确认：

- `SKILL.md` frontmatter 是合法 YAML。
- README 链接都指向存在的文件。
- 示例统一使用当前的 `memory` 字段表示 MB 内存配置。
- 启动 scraper 的示例必须先读取 `/api/scraper`，再调用 `/api/v1/scraper/run`。
- Task 和 rerun 示例符合 `openapi.json` 中当前的 `callback_url` 规则。

## 支持边界

提交 issue 时请提供：

- 使用的 Agent 或宿主应用
- 相关 scraper slug 或 run slug
- 脱敏后的请求 payload
- 脱敏后的响应或日志片段
- 复现步骤

不要在 issue 中提交真实 API Key、私有数据或完整凭据。

产品文档请访问 [CoreClaw](https://coreclaw.com)。
