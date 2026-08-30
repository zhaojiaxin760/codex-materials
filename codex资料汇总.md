# Codex 相关资料汇总（初步调研）

> 调研时间：2026-08-30 ｜ 来源：官方 changelog、开发者文档、社区评测

## 1. Codex 是什么

OpenAI 的 AI 编程智能体，形态覆盖：CLI（`@openai/codex`，npm 安装）、桌面应用、ChatGPT 内云端版。核心模式是"委派任务 → 云端沙箱执行 → 产出 PR / 结论"，强调并行、异步、自动化。

- 当前版本：Codex CLI 0.151.0（2026-08）
- 官方 changelog：https://developers.openai.com/codex/changelog

## 2. 近期重要动态（2026-08）

| 动态 | 说明 |
|---|---|
| 持久模式（测试中） | 据《连线》报道，Codex CLI 正在测试"持久模式"：持续工作直到休眠，具备"主动性"——回答后自行安排后续工作，可跨会话执行、必要时主动发消息。权限边界不变，系统外操作仍需批准。OpenAI 确认在测试但无近期上线计划 |
| Agents 仪表盘（0.149） | 多任务管理：搜索/启动/重命名/停止任务，统一界面管理并行 agent |
| codex queue | 向正在运行或休眠的会话发消息，不打断当前流程，适合长任务 |
| @ 提及任务 | 消息中引用其他 Codex 任务，可让 agent 读/创建/发送任务 |
| MCP 增强 | 可配置 MCP 服务器发现宽限期；扩展可检查/替换 MCP 工具结果 |
| 沙箱强化 | 远程沙箱按执行器真实 home 目录/OS/路径规则执行，防止 /cd 弱化沙箱限制 |

## 3. AGENTS.md 自定义指令机制

Codex 开工前自动读取的"工作说明书"，可分层：

- **全局级**：`~/.codex/AGENTS.md`（个人长期规则），可用 `CODEX_HOME` 切换
- **项目级**：仓库根目录 → 当前目录逐级查找，`AGENTS.override.md` 优先于 `AGENTS.md`
- **合并规则**：从根到当前目录拼接，越靠近当前目录优先级越高；总大小默认上限 32KiB（`project_doc_max_bytes` 可调）
- **备用文件名**：`project_doc_fallback_filenames` 可兼容团队已有的 TEAM_GUIDE.md 等规范文件
- 官方指南：https://developers.openai.com/codex/guides/agents-md

## 4. Codex vs Claude Code（社区共识）

| 维度 | Codex | Claude Code |
|---|---|---|
| 定位 | 并行、异步、委派式 | 交互式、单会话、可实时引导 |
| 优势 | 多 agent 并行、token 效率高、沙箱安全、终端任务强（Terminal-Bench 82.7%）、速度快 | 代码质量高（盲评 67% 偏好）、架构推理、深度调试、大上下文（1M） |
| 短板 | 过程偏黑盒、UI/设计实现弱、速度（单任务）较慢 | token 消耗高、配额紧、更贵 |
| 价格 | ChatGPT 订阅（$20 Plus 起，Pro $100/$200） | Claude 订阅（$20 Pro 起，Max $100/$200） |
| 典型比喻 | "靠谱的中级工程师：听话、快、少翻车" | "资深架构师：能讨论、更聪明、但更贵更慢" |

选型经验：Codex 适合"明确任务交给它执行"，Claude Code 适合"模糊需求一起探索"；不少开发者两者并用（Codex 做快速原型和测试生成，Claude Code 做架构决策和复杂重构）。

## 5. 多 Agent（Subagent）配置与并发上限

### 5.1 关键配置参数（config.toml `[agents]` 段）

| 参数 | 默认值 | 作用 | 调参建议 |
|---|---|---|---|
| `agents.max_threads` | **6** | 同时打开的 agent 线程上限（并行宽度） | 决定并行管道宽度；官方默认值即成本/性能折中 |
| `agents.max_depth` | **1** | agent 嵌套深度（root=0） | 默认只允许直接子 agent；调大会引发层层 fan-out，token/延迟/本地资源失控，**官方明确建议保持默认** |
| `agents.job_max_runtime_seconds` | 1800s（30 分钟） | `spawn_agents_on_csv` 每个 worker 的超时 | 批量任务按复杂度调 |

### 5.2 并发数口径差异（需注意）

| 口径 | 数值 | 来源 |
|---|---|---|
| 本地 subagent 线程上限（`max_threads`） | 默认 6 | OpenAI 官方文档 developers.openai.com/codex/subagents |
| 「Subagents GA 支持并行 agent 数」 | 8 | 第三方对比站 morphllm（2026-07 更新） |
| 云端/组织账户并发任务 | 默认 32，可扩展至 128 | 中文综述文章（**待官方核实**） |
| 配额侧硬约束（ChatGPT Plus） | 每 5 小时窗口 5 个 cloud task、5 次 code review | OpenAI 定价页（第三方整理） |

> 结论：**配置层面是 6，产品宣传/云侧是 8～32**，实际能跑多少取决于「本地配置 + 账户等级配额」两者取小。

### 5.3 内置与自定义 agent

- 内置三种：`default`（通用兜底）、`worker`（执行/修复）、`explorer`（只读代码库探索）
- 自定义 agent：TOML 文件放 `~/.codex/agents/`（个人）或 `.codex/agents/`（项目级，可入版本库，团队共享）
- 必填字段：`name` / `description` / `developer_instructions`
- 可选字段：`model`、`model_reasoning_effort`、`sandbox_mode`、`mcp_servers`、`skills`、`nickname_candidates`
- 未设置的字段从父会话继承；同名自定义 agent 覆盖内置 agent
- **Codex 不会自动分身**：只有你明确说「派 N 个 agent / 这块并行处理」时才会 spawn。官方强调子 agent 各自跑模型、用工具，**比单 agent 更费 token**

### 5.4 实践建议（社区共识）

- 按「任务可拆的维度」定数量，而非一味堆并发：PR 评审常见 3～5 个（一个评审点一个 agent）；代码库探索 + 定位 + 修复常见 3 个（explorer / debugger / worker）
- 模型分层省钱：探索类只读任务用轻量快模型（如 spark 档），真正改代码的 worker 用强模型
- 批量同质任务走 `spawn_agents_on_csv`（一行一个 worker，结果汇总导出 CSV），比多轮对话扇出更可控
- 几十上百个 agent 的场景，官方建议改用 **Workflow 脚本** 编排，不要把编排逻辑塞进对话
- 桌面端靠 project / thread / worktree 隔离，多 agent 并行改同一仓库不冲突
- 用 `/agent` 在 CLI 中切换、查看、喊停、关闭正在跑的 agent 线程

## 6. 可延伸的调研方向

- Codex 桌面端 / ChatGPT 云端版与 CLI 的能力差异矩阵
- 持久模式与"主动性"对产品设计的影响（主动型 agent 的权限/通知/成本设计）
- 国内同类产品对标（CodeBuddy、通义灵码、豆包 MarsCode 等）
- 企业侧落地：沙箱、合规、成本模型

## 主要来源

- OpenAI 官方：developers.openai.com/codex（changelog、AGENTS.md 指南）
- vibecompare.dev / agensi.io / freecodecamp.org：横向对比
- 腾讯云开发者社区、claudecode.xyz：中文教程与版本解读
- IT之家/新浪财经：《连线》持久模式报道（2026-08-28）
