# Cafe Agent Skill

[English](README.md) | [简体中文](README.zh-CN.md)

一个面向 AI coding agent 的可复用 Cafe 工作流定义。

## 项目概览

Cafe 通过 REST API 提供 scraper 的搜索与执行能力。这个仓库围绕 `SKILL.md` 和 `openapi.json` 对标准 Cafe 工作流进行了 Skill 化整理。

它面向的 Agent 环境包括：

- Codex
- Claude Code
- 其他可以消费结构化工作流说明的 agent runtime

仓库覆盖的核心操作包括：

- 在 Cafe Store 中找到合适的 scraper
- 读取 scraper 的元数据、版本号和输入 schema
- 发起异步 scraper run
- 安全地轮询 run 状态
- 直接读取分页结果做分析
- 将大结果集导出为 CSV 或 JSON
- 查看日志、重跑任务、终止运行、查询账户信息

## 仓库内容

```text
.
├── README.md         # GitHub 默认展示的英文文档
├── README.zh-CN.md   # 中文说明文档
├── SKILL.md          # Skill 定义、工作流和操作说明
└── openapi.json      # Cafe OpenAPI 规范
```

## 当前能力

当前 Skill 已覆盖 Cafe 的核心工作流：

- 搜索 Cafe Store 中可用的 scraper
- 获取 scraper 详情、参数 schema 和 README 内容
- 发起 scraper run
- 轮询运行状态并带保护机制
- 获取分页结果
- 导出 CSV / JSON 结果
- 运行已保存的 task
- 基于历史 run 重新执行
- 查看最近日志
- 中止运行中的任务
- 查询账户余额和流量使用情况
- 查看历史 run 列表

## 工作方式

这个仓库不是 SDK，而是一个以 `SKILL.md` 为中心的工作流包：

- `SKILL.md` 定义了这个 Skill 在什么情况下触发，以及 Agent 应该如何执行
- `openapi.json` 提供完整的 API 参考
- 当 Skill 被触发后，Agent 会按文档中的流程一步步完成 Cafe 工作流

整体流程可以概括为：

1. 用 `GET /api/store` 查找 scraper
2. 用 `GET /api/scraper` 读取 `version`、系统参数和自定义输入 schema
3. 用 `POST /api/v1/scraper/run` 发起异步任务
4. 用 `POST /api/v1/run/detail` 轮询进度
5. 用 `POST /api/v1/run/result/list` 或 `POST /api/v1/run/result/export` 获取结果
6. 按需继续调用日志、重跑、终止、历史记录、账户信息等接口

## 兼容性

本仓库提供的是工作流定义和 API 参考，具体如何装载或集成取决于目标 Agent 环境。

- Codex：可作为 skill 包使用
- Claude Code：可将 `SKILL.md` 作为工作流说明，将 `openapi.json` 作为接口参考
- 其他 Agent 环境：可按各自的 prompt、tool 或 workflow 机制复用相同内容

## 使用前准备

开始前请确保本地具备：

- `curl`
- `jq`
- 有效的 `CAFE_API_KEY`
- 可以访问 `https://openapi.cafescraper.com`

设置 API Key：

```bash
export CAFE_API_KEY="your_api_key"
```

## 安装方式

对于支持 skills 目录的环境，请按对应环境的约定放置本仓库。

例如在 Codex 风格的目录结构中：

```bash
~/.codex/skills/cafe
```

必需的入口文件是：

```bash
SKILL.md
```

安装后重启你的 Agent 环境，让这个 Skill 被正确加载。

## 示例请求

下面这些请求适合使用这套工作流：

- “帮我找一个适合抓 Amazon 商品列表的 Cafe scraper。”
- “先读取这个 scraper 的参数，然后帮我发起一次运行。”
- “继续轮询这个 `run_slug`，完成后把前 20 条结果展示给我。”
- “把这次 run 的结果导出成 CSV。”
- “看看这次运行为什么失败，把 error log 提取出来。”
- “查询一下我当前的 Cafe 账户余额和流量使用情况。”

## 设计上的关键约束

这个 Skill 有一些明确的工作流约束：

- 发起 scraper run 之前，必须先读取 `/api/scraper`
- `version` 必须来自 scraper detail 响应，不能靠猜
- 小结果集更适合用 `result/list`
- 大结果集更适合用 `result/export`
- 轮询必须带连续错误保护，避免无限循环
- 日志、重跑、终止、账户接口一起保留，保证流程闭环

## 什么时候用 inline result，什么时候用 export

适合用 inline result 的情况：

- 需要让 Agent 直接读取、总结或分析数据
- 数据量较小，适合放进上下文

适合用 export 的情况：

- 用户需要下载文件
- 结果集较大
- 需要拿到独立的 CSV / JSON 文件，而不是塞进上下文

## 注意事项

- 大多数接口都需要 `CAFE_API_KEY`
- 运行接口需要 `callback_url`；当前 Skill 中已经记录了测试回调地址
- 大结果集通常应该优先导出，而不是直接灌进模型上下文
- 轮询逻辑需要先清理异常控制字符，再把 JSON 交给 `jq`

## 参考资料

- Cafe Store: https://cafescraper.com
- Cafe OpenAPI 规范：`openapi.json`
- Skill 入口定义：`SKILL.md`

## 许可证

本项目使用 MIT License，详见 `LICENSE`。

---

本仓库为 Cafe 数据采集流程接入 AI Agent 环境提供了结构化的起点。
