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

## 4. Codex vs Claude Code 全面对比（2026-08 数据）

> 数据核对时间 2026-08-18 ~ 08-23（Artificial Analysis、官方定价页、各对比站）。**模型代际更新极快，不同来源存在口径冲突（如 Claude 的 Opus 4.8 vs Opus 5），下表已标注。**

### 4.1 定位与工作流

| 维度 | Codex | Claude Code |
|---|---|---|
| 核心模式 | 并行、异步、委派式：派任务 → 等 → 收 PR | 交互式单会话：实时引导、边看边改 |
| 上下文架构 | 每个子任务独立上下文（父会话汇总） | **主上下文连续**，保留已查事实/否掉的假设/共享约束 |
| 并行能力 | 子 agent 并行（配置上限 6，产品侧 8），worktree 隔离线程 | 子 agent + worktree + 实验性 Agent Teams + `/batch`（可拆 5~30 个 worktree） |
| 触发方式 | **不会自动分身**，需你明确说「开 N 个 agent」 | 可自动编排子 agent |
| 开源 | CLI 部分 Apache-2.0 开源（114,493 stars，2026-08-23） | 闭源（142,686 stars，2026-08-23） |
| 生态规模 | OpenAI 称 2026-08-21 达 2,000 万活跃用户 | 覆盖面广：终端 / VS Code / JetBrains / 桌面 / Web / 移动端 / Slack |

### 4.2 模型与上下文

| 维度 | Codex | Claude Code |
|---|---|---|
| 主力模型 | GPT-5.6 Sol（预览）、GPT-5.5；GPT-5.4 于 2026-08-31 退役 | Sonnet（4.6/5，口径冲突）、Opus（4.8/5，口径冲突）、Haiku 4.5 快档 |
| 分档路由 | Sol / Terra / Luna 按难度与体量分流 | Sonnet / Opus / Haiku 三档 |
| 标准上下文 | 256K | 200K |
| 最大上下文 | 1M（GPT-5.5） | 1M（Opus） |
| 单次输出上限 | 64K | 128K |
| 配置文件 | `AGENTS.md`（**厂商中立标准**，其他 agent 也支持） | `CLAUDE.md` |

### 4.3 公开基准（Artificial Analysis，2026-08）

| 指标 | Claude Code + Opus 5 (xhigh) | Codex + GPT-5.6 Sol (max) |
|---|---|---|
| Coding Agent Index | 67 | 67（**打平**） |
| DeepSWE | 60% | **69%** |
| Terminal-Bench v2 | 85% | **88%** |
| SWE-Atlas-QnA | **55%** | 43% |
| 单任务耗时 | 23.6 min | **10.2 min** |
| 单任务 token | 21.8M | **13.2M** |
| 单任务成本 | $8.23 | **$7.08** |

另一组口径（morphllm，2026-07）：SWE-bench Pro Claude 69.2% vs Codex 58.6%；SWE-bench Verified 88.6% vs 88.7%；Terminal-Bench 2.0 69.4% vs 82.7%。

> 结论：**综合评分打平，Codex 在执行效率（时间/token/成本）上明显领先，Claude Code 在探索型/问答型任务上更强。**

### 4.4 价格与配额

| 档位 | Codex（ChatGPT 方案） | Claude Code（Claude 方案） |
|---|---|---|
| 免费 | $0，基础额度 | $0，收紧的限额 |
| 入门 | Go $8 / Plus $20 | Pro $20（年付 $17） |
| 中档 | Pro 5x $100 | Max 5x $100 |
| 顶配 | Pro 20x $200 | Max 20x $200 |
| 团队 | Business ~$20/人（年付）~$25（月付） | Team Standard $25（**不含 Claude Code**）/ Premium $125 |
| 企业 | 定制 | $20/席位自助 + API 用量，或定制 |
| API 价（输入/输出，每百万 token） | GPT-5.5：$5 / $30 | Opus 4.8：$5 / $25 |
| 缓存 | 自动 90% | 90% |

计费与限额机制：

- **Codex**：2026-04-02 起改为 **token 额度制**，滚动 5 小时窗口。Plus 每窗口约 10~100 条 Sol 消息 / 25~200 条 Terra / 250~2000 条 Luna；Pro 为 5x、20x。轻度会话约消耗 $0.50~$2.00 额度
- **Claude Code**：滚动 5 小时窗口 + **周上限**，按模型小时计。Pro 约 40~80 Sonnet 小时/周，Max 5x 约 140~280，Max 20x 约 240~480。2026-05-06 把 5 小时上限翻倍；所有付费档周限额 +50% 的活动至 2026-08-31
- 两者本地与云端共用同一额度池（Codex）；Plus 与 Pro 共用一个 5 小时窗口

### 4.5 选型决策规则

| 场景 | 首选 | 原因 |
|---|---|---|
| 根因分析、架构改动、跨组件修改 | **Claude Code** | 探索过程中任务列表会变，需要主上下文保留判断链 |
| 有明确验收标准和测试的可拆解批量任务 | **Codex** | 独立 worktree 线程 + 按难度路由模型，吞吐高 |
| 高频日常实现 | **Codex** | 单任务 10.2 min vs 23.6 min，token 少 40% |
| 大重构、深度调试 | **Claude Code** | 盲评中代码质量更受偏好（2026 调查约 67%） |
| 成本敏感 / 已在 ChatGPT 生态 | **Codex** | Go $8 起，捆绑现有订阅 |
| 企业合规与管控 | 视生态而定 | Codex 走 ChatGPT 工作区 RBAC/留存策略；Claude 走 Anthropic 侧 |

常见做法：**两者并用**——Codex 跑批量实现与测试生成，Claude Code 做架构决策与复杂重构。

### 4.6 Codex 最擅长 / 不擅长的场景

**最擅长（有基准与官方用例支撑）**

| 场景 | 支撑 |
|---|---|
| 终端/命令行类任务 | Terminal-Bench v2 **88%**，全榜第一 |
| 可拆解的批量体力活 | 依赖升级、跨 50~100 文件 codemod / 迁移、批量修 bug；一次派 10 个任务，只管收 PR |
| 长时无人值守任务 | 云端会话可长时间不掉上下文；开会前下单会后收货、跨时区协作 |
| 测试生成 + 自验证循环 | 写测试 → 跑 → 迭代到全绿，把验证命令写进任务就能自动收尾 |
| 自动化 PR 评审 | GitHub 上 `@codex review`；OpenAI 内部 **100% 的 PR 都过 Codex review** |
| 陌生代码库上手 | 官方推荐的新人第一个用例：讲架构、请求流、关键文件、构建命令 |
| CI / 无头脚本化 | `codex exec` 非交互执行，比 Claude Code 的 `-p` 更贴近 CI 原生设计 |
| 非编码知识工作 | OpenAI 内部 top 10 用例含：SQL 查询、表格分析、PPT 大纲、SOP 草稿、会议纪要 |

**模型路由（GPT-5.6 三档）**：Sol（旗舰，复杂编码/调研/安全/开放性难题，最费时费 token）→ Terra（日常实现、分析、调试）→ Luna（清晰可重复的高体量任务，最快最省）。

**用得好的关键：把任务写成「契约」而不是「对话」**

一份好契约四要素：
1. **子系统**——指明改哪个模块/目录，别让它猜
2. **期望行为**——输入输出、边界条件、不变量
3. **验证命令**——它自己跑通再交回，你只看绿不绿
4. **收尾动作**——通过则开 PR（可指定标题前缀），不通过则报告失败原因

配套：`AGENTS.md` 要**精炼**（架构一句话 + 构建/测试命令 + 别碰的目录），因为它会被整段带进上下文，越啰嗦额度消耗越快。

**不擅长**

- 目标中途会变、需要边探索边改的活（异步节奏打断心流）
- 需要你频繁修正方向——每轮等待成本高
- 依赖本机环境 / 本地数据库的任务
- 想看清「思考过程」——相对黑盒，只看最终结果
- UI / CSS 精细调整（公认弱项）

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

## 6. 使用 Codex 的前置要求

### 6.1 账号与订阅（硬性）

| 项目 | 要求 |
|---|---|
| 账号 | ChatGPT 账号（Free / Go / Plus / Pro / Business / Edu / Enterprise 各档均含 Codex，额度不同）或 OpenAI Platform API Key |
| 云端版 | **必须 ChatGPT 账号登录**，API Key 方式不支持/受限 |
| GitHub | 使用云端任务需把 ChatGPT 与 GitHub 账号绑定 |
| MFA | 官方要求 Codex 云端账号开启多因素认证 |
| 企业 | 工作区成员与席位决定可用面；RBAC 控制功能权限；Enterprise 可签发 Codex access token 做非交互自动化；支持 workload identity federation |

两种登录方式的取舍：

- **ChatGPT 登录**：走订阅额度，能用云端 + 工作区集成，适合个人/团队日常
- **API Key 登录**：按 token 计费（标准 API 价），只覆盖本地 CLI / 桌面 / IDE，云端和 ChatGPT 工作区功能受限或不可用，**适合 CI/CD 与程序化调用**

命令参考：`codex login`（浏览器流）、`printenv OPENAI_API_KEY | codex login --with-api-key`、`codex login --device-auth`（无浏览器/远程机）、`codex login status` / `codex logout`。

### 6.2 本地环境（CLI）

| 依赖 | 最低 | 推荐 |
|---|---|---|
| 操作系统 | macOS 12+；Ubuntu 20.04+ / Debian 10+；Windows 11（原生 PowerShell 或 WSL2） | macOS 14+；Ubuntu 22.04+ |
| Node.js | 16+（仅 npm 安装路径需要） | 22 LTS |
| Git | 2.23+（可选，PR helper / worktree 需要） | 2.30+ |
| 内存 | 4 GB | 8 GB+ |
| 磁盘 | ~200 MB | 500 MB+ |

- 用官方安装脚本 / Homebrew cask / 预编译二进制安装时**不需要 Node**（自带运行时）
- 安装方式：`npm i -g @openai/codex`、`brew install --cask codex`、`curl -fsSL https://chatgpt.com/codex/install.sh | sh`、GitHub Releases 下载二进制
- 禁止 `sudo npm install -g`，应修 npm 权限

### 6.3 网络与沙箱（企业落地要评估）

- 需能访问 OpenAI 服务；企业要评估代码出境、数据留存策略（ChatGPT 登录受工作区留存/驻留设置约束，API Key 受 API 组织设置约束）
- macOS 12+ 用 Apple Seatbelt 包裹命令，默认**完全禁止出网**，仅 `$PWD`、`$TMPDIR`、`~/.codex` 等少数路径可写
- **Linux 默认无沙箱**，官方建议用 Docker（`run_in_container.sh`）+ iptables 脚本，只放行 OpenAI API 出网
- 审批模式三档：`suggest`（默认，写文件/执行命令都要问）、`auto-edit`（自动改文件，命令仍要问）、`full-auto`（自动执行，但断网 + 限制在当前目录）

## 7. 成本模型与 token 控制（一人公司视角）

### 7.1 计费机制（2026-04-02 起改版）

- 从「按消息计数」改为 **token 额度制**：1 credit ≈ **$0.04**，与 API 价格 1:1 对齐
- 滚动 **5 小时窗口**补额，**不是月度封顶**——可以在一个高强度的 2 小时里烧光整窗
- 本地任务与云端任务**共用同一额度池**
- Plus / Pro 撞到上限后可加购额度、等窗口重置、或改用 API key

Credit 费率（每百万 token）：

| 模型 | 输入 | 缓存输入 | 输出 |
|---|---|---|---|
| GPT-5.5 | 125（$5） | 12.5 | 750（$30） |
| GPT-5.4 | 62.5 | 6.25 | 375 |
| GPT-5.4-mini | 18.75 | 1.875 | 113 |
| GPT-5.3-Codex | 43.75 | — | 350 |

单任务消耗参考：小 bug 修复 ≈ 10 credits（~$0.40）；多文件重构 ≈ 60 credits（~$2.40）；典型会话 $0.50~$2.00。

### 7.2 能不能控制 token？

**订阅制没有用户可设的支出上限**（5 小时窗口只是节流，不是封顶）。能做的是压单价和压轮次：

| 手段 | 效果 |
|---|---|
| 模型分档路由 | 最直接。GPT-5.5 与 GPT-5.4-mini 单价差 **6.7 倍**；日常用 mini/Terra，难任务才切 Sol |
| 推理强度（reasoning effort） | 默认起步，只在真需要时提高 |
| 复用会话上下文 | 缓存输入只有新鲜输入的 **1/10**，同一仓库接着聊远便宜过冷启动 |
| `AGENTS.md` 精炼 | 会被整段带进上下文，写 500 行等于每次任务都烧一遍 |
| 任务写成契约 | 减少返工轮次——每多一轮就是整份上下文重发 |
| 压输出 | 输出 token 单价约为输入的 6 倍，别让它长篇解释 |
| **改用 API key** | 唯一能做**硬性预算上限**的路径（OpenAI 平台设 budget cap） |

### 7.3 一人公司月度花费估算

| 使用强度 | 建议档位 | 月成本 |
|---|---|---|
| 轻度（偶尔小任务） | Go $8 或 Free | $0~8 |
| 中度（每天 2~3 个会话，日常用 mini/Terra） | **Plus $20** | $20~40（含偶尔加购额度） |
| 重度（整天挂云端任务、并行多开） | Pro 5x $100 | $100+ |

OpenAI 官方口径：把 Codex 当主力工程工具的重度用户约 **$100~200/开发者/月**。

**一人公司推荐路径**：Plus $20 起步 → 默认模型压到 mini/Terra → 一个月后看用量面板决定是否升 Pro 5x。批量/CI 类任务单独走 API key 并设预算上限，避免和日常额度互相挤占。

## 8. 可延伸的调研方向

- Codex 桌面端 / ChatGPT 云端版与 CLI 的能力差异矩阵
- 持久模式与"主动性"对产品设计的影响（主动型 agent 的权限/通知/成本设计）
- 国内同类产品对标（CodeBuddy、通义灵码、豆包 MarsCode 等）
- 企业侧落地：沙箱、合规、成本模型

## 主要来源

- OpenAI 官方：developers.openai.com/codex（changelog、AGENTS.md 指南）
- vibecompare.dev / agensi.io / freecodecamp.org：横向对比
- 腾讯云开发者社区、claudecode.xyz：中文教程与版本解读
- IT之家/新浪财经：《连线》持久模式报道（2026-08-28）
