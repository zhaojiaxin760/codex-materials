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

## 5. 可延伸的调研方向

- Codex 桌面端 / ChatGPT 云端版与 CLI 的能力差异矩阵
- 持久模式与"主动性"对产品设计的影响（主动型 agent 的权限/通知/成本设计）
- 国内同类产品对标（CodeBuddy、通义灵码、豆包 MarsCode 等）
- 企业侧落地：沙箱、合规、成本模型

## 主要来源

- OpenAI 官方：developers.openai.com/codex（changelog、AGENTS.md 指南）
- vibecompare.dev / agensi.io / freecodecamp.org：横向对比
- 腾讯云开发者社区、claudecode.xyz：中文教程与版本解读
- IT之家/新浪财经：《连线》持久模式报道（2026-08-28）
