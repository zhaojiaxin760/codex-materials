# Codex 工作流落地手册

> 面向一人公司的可操作手册：契约式派单、AGENTS.md 写法、验证循环、省钱配置
>
> 调研时间：2026-08-31 ｜ 检索范围：2026-03 至今 ｜ 并行 5 组 agent，覆盖 15 个章节
>
> 说明：字段值若标注 `[不确定]` 或列入「待核实」，表示多个来源冲突或未找到官方依据，已跳过正文展示。

## 目录

1. [契约式派单模板](#契约式派单模板) — 几乎是为一人公司量身定做的。无同事 review → 四要素把「人肉 review」换成「命令 review」；成本敏感…
2. [派单验收门禁](#派单验收门禁) — 极高，而且是三个前提里「无同事 review」唯一的替代方案。没有同事帮你过 diff，就只能靠可 replay 的 t…
3. [AGENTS.md 写法与长度控制](#agents-md-写法与长度控制) — 高，尤其契合「成本敏感」这一条。没有团队帮你分摊维护成本，AGENTS.md 就必须极简——它同时是「每次请求都重复付的…
4. [Goal Mode 长任务自治](#goal-mode-长任务自治) — 极高，尤其契合「无同事 review、成本敏感、需要异步杠杆」三前提。无同事 review → 完成审计机制替你把「什么…
5. [config.toml 核心配置](#config-toml-核心配置) — 极高，是「成本敏感」的直接解药。无同事 review → on-request + workspace-write 给你…
6. [权限新体系](#权限新体系) — 高，且是「无同事 review」的直接补偿。没有第二个人在 PR 里拦住你，permission profiles 的文…
7. [Hooks 强制验证](#hooks-强制验证) — 极高，直击「无同事 review」这个最痛前提。Stop 钩子强制「测试通过才交回」= 让机器当那个永远在线、绝不疲劳的…
8. [验证循环设计](#验证循环设计) — 极高。无同事 review → Stop 钩子「测试不过不许交回」让机器替代那个永远在线的 reviewer；成本敏感 …
9. [上下文与会话治理](#上下文与会话治理) — 高。成本敏感 → tool_output_token_limit + 早压缩是直接省钱（cache 命中率、返工减少）；…
10. [成本与额度可视化](#成本与额度可视化) — 极高。无同事 review → 没有第二双眼睛帮你盯成本，必须靠 /status + /statusline + CI …
11. [并行与自定义 agent 分档](#并行与自定义-agent-分档) — 高，精准命中三个前提。无同事 review → 并行多维只读审查是「没有 review 团队却有 review 效果」的…
12. [模型弃用与迁移时点](#模型弃用与迁移时点) — 高。无同事 review → 没有第二个人提醒你模型下线了，只能靠 grep 脚本主动守护；成本敏感 → 迁移到 gpt…
13. [国内环境适配](#国内环境适配) — 极高，是国内一人公司的唯一解。无同事 review → 没有第二个人帮你调协议，所以优先选「厂商原生支持 respons…
14. [任务模板库与 Skills 打包](#任务模板库与-skills-打包) — 极高。无同事 review → PR review 模板 + security-reviewer 代理就是你的「虚拟同事…
15. [故障排查](#故障排查) — 高。无同事 review → 没有第二个人帮你盯着报错，这份按症状定位的清单就是你的「救火队友」；成本敏感 → 区分「网…

---

## 1. 契约式派单模板

### 核心做法

四要素的本质是：把「是否做完」的判定权从模型的自觉，移交给一条可执行的命令。

【官方口径与本手册四要素的映射】  
OpenAI 官方 Best practices 推荐每条 prompt 含四件事：Goal（要改什么）/ Context（哪些文件相关）/ Constraints（遵守什么约定）/ Done when（什么条件算完）。本手册的四要素是它在「无人值守、次日验收」场景下的落地映射：

| 四要素    | 官方对应                  | 回答的问题            | 缺失后的后果                      |
| ------ | --------------------- | ---------------- | --------------------------- |
| ① 子系统  | Context + Constraints | 我能碰哪些文件，绝对不能碰哪些  | 过度重构、误改迁移文件 / 公开 API / 依赖版本 |
| ② 期望行为 | Goal                  | 改完之后「可观测的事实」是什么  | 模型自由发挥，交付物与你的预期不是一回事        |
| ③ 验证命令 | Done when             | 谁说了算（命令，不是模型的自述） | 模型自称完成，早上起来发现是假的            |
| ④ 收尾动作 | Done when + Report    | 交回时必带哪几样证据       | 无法 review，只能自己全盘重跑，异步杠杆归零   |

【操作步骤】

1. 先只读探查，再写契约。陌生模块先发一条只读单（`--sandbox read-only`），拿到文件清单与调用链后，再写真正的实现单。
2. 划子系统：写死「可编辑」白名单 + 「禁止改」黑名单两行。绝不能写「相关文件酌情修改」。
3. 写期望行为：用「输入 X → 得到 Y」或「之前 / 之后」的可观测句式。禁止使用「优化」「改进」「完善」「提升性能」这类没有判定标准的词。
4. 给验证命令：必须是能原样粘进 shell 的一条完整命令（含过滤参数），不是「跑一下测试」。
5. 定收尾动作：固定三项——可 replay 的 transcript 片段、PR 范围回执（`git status --short` + `git diff --stat`）、结构化结论块。
6. 加边界条款（Do NOT）：禁止改迁移文件、禁止改公开响应格式、禁止顺手重构、禁止升级依赖、禁止 commit / push。
7. 加熔断条款：同一条命令连续失败 3 次后停下并报告，不要无限循环烧钱。
8. 加反作弊条款：明确「不允许修改现有测试来使其通过」——否则模型会改测试而不是改代码。
9. 事后沉淀：同一个坑踩第二次，就把规则写进 AGENTS.md，而不是每次在 prompt 里重述。

【为什么四要素能一次做对】  
模型出错的三种来源分别是「猜边界」「猜目标」「猜验收」。子系统消灭第一种，期望行为消灭第二种，验证命令消灭第三种，收尾动作则让你在无人值守时依然能判定成败。四要素齐全的单，第一次命中率显著高于靠追问补救。

### 可直接复制的模板命令配置

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【模板 1｜主契约模板（中文，可直接复制填写）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 子系统

- 可编辑：<精确到文件的白名单，例如 src/auth/login.ts, tests/auth/login.test.ts>
- 禁止改：<迁移文件 / 公开 API 响应格式 / 依赖版本 / 其他模块>
- 参考实现：<照抄哪个文件的模式，例如 src/validators/order.ts>

## 期望行为

- 现状：<当前可观测的行为，最好贴一段原始报错或输出>
- 目标：<改完之后可观测的行为，用「输入 X → 得到 Y」句式>
- 不要求：<明确不属于本次目标的事>

## 验证命令（唯一权威，命令说了算）

<可直接粘贴执行的完整命令，含参数，例如 pnpm vitest run tests/auth/login.test.ts -t 'plus'>

## 收尾动作（交回时必带，缺一不可）

1. 贴出验证命令的原始输出（不要总结，要原文，含 exit code）
2. 贴出 PR 范围回执：  
   git status --short  
   git diff --stat
3. 按下面格式写结论块：

### 结论

- 结果：通过 / 失败 / 阻塞
- 改动文件：<逐行列出>
- 验证：<命令> → exit <码>
- 残留风险：<一句话>
- 我未做的事：<一句话>

## 熔断

同一条验证命令连续失败 3 次后停止，按上面「结论」格式报告，不要再继续改。

## 禁止

- 不要重构无关代码
- 不要升级依赖
- 不要动数据库迁移与公开响应格式
- 不要 git commit / git push
- 不要修改现有测试来使其通过

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【模板 2｜三个高频场景的填好版】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

▸ 场景 A：修 bug

## 子系统

- 可编辑：src/auth/login.ts, tests/auth/login.test.ts
- 禁止改：prisma/migrations/**, src/api/responses/**, package.json
- 参考实现：src/validators/order.ts

## 期望行为

- 现状：email 含加号（<a+b@x.com>）时 POST /api/login 返回 500，日志报 URIError
- 目标：<a+b@x.com> 登录成功返回 200，且响应体结构与不含加号的 email 完全一致
- 不要求：不做 email 规范化、不改数据库字段

## 验证命令

pnpm vitest run tests/auth/login.test.ts -t 'plus sign'

## 收尾动作

（同主模板，照抄）

## 熔断 / 禁止

（同主模板，照抄）

▸ 场景 B：重构（行为不变）

## 子系统

- 可编辑：src/billing/\*\*
- 禁止改：public API 签名、prisma/migrations/\*\*、其他模块

## 期望行为

- 现状与目标：对外行为完全不变；src/billing 内部从 callback 改为 async/await
- 不要求：不做性能优化、不调整目录结构

## 验证命令

pnpm vitest run src/billing && pnpm tsc --noEmit && pnpm lint

## 收尾动作 / 熔断 / 禁止

（同主模板；「禁止」再加一条：不要借机清理无关代码）

▸ 场景 C：补测试

## 子系统

- 可编辑：tests/payments/\*\*（只新增，不改现有测试文件）
- 禁止改：src/\*\*（发现 bug 就报告，不要自己改实现）

## 期望行为

- 现状：src/payments/refund.ts 无任何测试
- 目标：覆盖 正常退款 / 超额退款 / 重复退款 三条路径，全部通过

## 验证命令

pnpm vitest run tests/payments/refund.test.ts --coverage

## 收尾动作

（同主模板；结论块再加一项：覆盖率 <数字>%）



━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【模板 3｜反例对照（这几条踩中必返工）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ 反例 1｜没有子系统  
「修一下登录的 bug。」  
问题：没说哪个文件、没说现象、没说怎么验证、没说交回什么。Codex 只能全仓搜索加猜测。

❌ 反例 2｜验证命令是描述而不是命令  
「改完后跑一下相关测试确认没问题。」  
问题：「相关」由模型定义，「没问题」由模型判定，等于没有门禁。  
✅ 改成：pnpm vitest run tests/auth/login.test.ts -t 'plus sign'

❌ 反例 3｜期望行为写成了实现方案  
「把 src/auth/login.ts 里的 email 解析改成用 zod 校验。」  
问题：这是 How 不是 What。模型会照做，但可能根本不解决你的问题。  
✅ 改成：「email 含加号时返回 200 而不是 500。（实现方案由你决定，我只验收行为。）」

❌ 反例 4｜一单多目标（Kitchen Sink）  
「重构整个 auth 模块，顺便补测试、更新文档、修掉所有 lint。」  
问题：五个目标，五个都做不好，且 diff 大到无法 review。  
✅ 改成：拆成 5 条独立的单，每个线程一条。

❌ 反例 5｜占位符过载  
「给 [ENDPOINT] 加 [TYPE] 校验，用 [LIBRARY]，照 [PATTERN] 写。」  
✅ 改成：把占位符全部替换成真实路径与技术名。

❌ 反例 6｜没有收尾动作  
「……改完告诉我。」  
问题：早上醒来只看到「已完成」三个字，无法判断真假，只能自己重跑——异步杠杆归零。

❌ 反例 7｜隐性期望  
「Fix the bug.」  
✅ 改成：写清现象、定位、复现步骤与回归测试要求。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【模板 4｜机器契约：--output-schema（让回执可被脚本解析）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
保存为 ~/.codex/schemas/handoff.json：

{  
"$schema": "<https://json-schema.org/draft/2020-12/schema>",  
"type": "object",  
"additionalProperties": false,  
"required": ["result", "changed_files", "verify", "residual_risk", "not_done"],  
"properties": {  
"result": { "enum": ["pass", "fail", "blocked"] },  
"changed_files": { "type": "array", "items": { "type": "string" } },  
"verify": {  
"type": "object",  
"additionalProperties": false,  
"required": ["command", "exit_code", "output_tail"],  
"properties": {  
"command": { "type": "string" },  
"exit_code": { "type": "integer" },  
"output_tail": { "type": "string" }  
}  
},  
"residual_risk": { "type": "string" },  
"not_done": { "type": "string" }  
}  
}

注意：OpenAI Structured Outputs 强制要求每个 object 都写 "additionalProperties": false，缺了会报错。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【模板 5｜睡前下单脚本（cron / launchd / 手动都能跑）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#!/usr/bin/env bash

# ~/bin/codex-order —— 睡前下单，早上收回执

# 用法：codex-order ./tasks/fix-login-plus.md ~/repos/myapp

set -uo pipefail  
TASK_FILE="$1"
REPO="${2:-$PWD}"
STAMP="$(date +%Y%m%d-%H%M%S)"  
OUT_DIR="$HOME/codex-orders/$STAMP"  
mkdir -p "$OUT_DIR"

cd "$REPO" || exit 1

codex exec   
--cd "$REPO" \   --sandbox workspace-write \   --ask-for-approval never \   --json \   --output-schema "$HOME/.codex/schemas/handoff.json"   
-o "$OUT_DIR/handoff.json" \
  "$(cat "$TASK_FILE")" \
  2> "$OUT_DIR/stderr.log"   
| tee "$OUT_DIR/events.jsonl"   
| jq -r --unbuffered 'select(.type=="item.completed" and .item.type=="command_execution") | "(.item.status)\t(.item.exit_code)\t(.item.command)"'

# 早上第一件事：看回执

echo "===== 回执 $STAMP ====="
if [ -s "$OUT_DIR/handoff.json" ]; then  
jq . "$OUT_DIR/handoff.json"
else
  echo "[!] 无结构化回执，请检查 $OUT_DIR/events.jsonl 与 stderr.log"  
jq -r 'select(.type=="turn.failed" or .type=="error") | tojson' "$OUT_DIR/events.jsonl"
fi
echo "===== 实际改动 ====="
git -C "$REPO" status --short  
git -C "$REPO" diff --stat

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【模板 6｜把契约写进 AGENTS.md，一劳永逸】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 派单契约（每次任务默认遵守）

- 任何任务开始前，先复述：可编辑范围、禁止改动范围、验证命令、收尾动作四项；缺少任一项先问，不要开工。
- 验证命令必须原样执行并贴出原始输出与 exit code，不允许用「应该没问题」代替。
- 同一条命令连续失败 3 次后停下并报告，不要继续尝试。
- 不允许修改现有测试来使其通过。
- 交回时必带：验证输出原文、git status --short、git diff --stat、结论块（结果 / 改动文件 / 验证 / 残留风险 / 我未做的事）。
- 不要 git commit、git push、升级依赖、重构无关代码。

### 关键参数

官方默认值 → 一人公司推荐值（★=必须改）

| 参数                                     | 官方默认                               | 一人公司推荐值                         | 说明                              |
| -------------------------------------- | ---------------------------------- | ------------------------------- | ------------------------------- |
| sandbox_mode                           | read-only                          | workspace-write ★               | 默认只读根本写不了文件，派单必须显式放开            |
| approval_policy                        | on-request（另有资料称 untrusted，二者口径不一） | 睡前无人值守单：never ★；日常交互：on-request | 非 TTY 下不设 never 会挂死等确认          |
| model_reasoning_effort                 | medium                             | 睡前长单 high；机械单（重命名 / 补测试）low     | 按任务难度配，不要一律拉满                   |
| --output-schema 的 additionalProperties | 无（需自己写）                            | 每个 object 都写 false ★            | OpenAI Structured Outputs 的硬性要求 |
| hooks timeout                          | 600 秒                              | 30–120 秒                        | 默认太长，失败单会空转                     |
| project_doc_max_bytes                  | 32768（32 KiB）                      | 保持 32768                        | 别调大，先拆文件（见 AGENTS.md 条目）        |
| 熔断轮次                                   | 无内置参数                              | 在 prompt 里写「连续 3 次」★            | Codex 没有 max_iterations，只能靠提示词  |
| web_search                             | cached                             | 涉及外部文档时改 live                   | 平时保持 cached 省钱                  |
| -o / --output-last-message             | 无                                  | 必配，落盘回执                         | 否则只能从 JSONL 里掏                  |
| sandbox_workspace_write.network_access | false                              | 保持 false，需要装依赖时临时 -c 打开         | 验证命令依赖网络时会莫名失败                  |
| CODEX_API_KEY                          | 无                                  | CI / cron 场景必配                  | 避免 runner 读 ~/.codex/auth.json  |

### 常见坑

1. 【最高频】网上大量教程仍在用 `codex exec --full-auto`。该 flag 已在 v0.147.0（2026-08-07）彻底移除，脚本会直接报未知参数。必须改写成 `--sandbox workspace-write --ask-for-approval never`。
2. `codex exec` 运行在无 TTY 环境，若 approval_policy 不是 never，进程会一直等待人工确认，cron / launchd 任务挂死到第二天你才发现什么都没跑。
3. 验证命令里混入中文全角符号（：" '' ——）会导致 shell 报错。命令块务必用半角，中文说明放在命令块外面。
4. 沙箱默认断网（workspace-write 的 network_access=false）。验证命令若需要拉依赖 / 连数据库，必然失败且报错信息往往看不出是网络问题。要么临时放开网络，要么换成本地可跑的子集。
5. 输出被静默截断：command_execution 的 aggregated_output 只保留 64 KiB，超长日志末尾是 `...(truncated)`。别把这段当完整证据存证。
6. Schema drift：v0.44.0 之前 item 类型字段叫 `item_type`，助手消息叫 `assistant_message`（现在是 `type` / `agent_message`）。解析脚本要做双字段兼容，且事件流里没有 schema version 字段可供判断。
7. 模型会「绕过」验证——最常见的作弊是修改测试本身让它通过。必须在「禁止」里显式写死。
8. 期望行为写成「提升性能 / 优化体验」这类无判定标准的词，等于没有验收标准，模型只能自我认定完成。
9. 你写在 AGENTS.md 里的规则可能根本没加载：项目级文件总大小超过 project_doc_max_bytes（32 KiB）会被静默前缀截断，且不报错、不提示。症状看起来像「模型突然变笨」。
10. 一单多目标（同时重构 + 补测试 + 修 lint + 改文档），五个目标每个做到 60%，且 diff 大到无法 review——这比只做一件事更贵。
11. 只给目录不给文件（「改 src/auth 下的东西」），模型会把整个目录翻一遍再动手，上下文和 token 先烧一轮。
12. 忘了写「禁止 git commit / push」。无人值守下单时这条特别危险——你会收到一个已经提交甚至推送的分支。
13. 以为 `codex exec` 和 TUI 共享同一套会话语义。`codex exec resume` 默认只找当前工作目录下起的会话，跨目录要加 `--all`。
14. 中文 prompt 配英文代码库时，路径大小写 / 拼写错误率明显上升。路径一律从 `ls` 输出里复制，不要手写。

### 降级与回退路径

1. 模型被弃用：四要素模板本身不写模型 id（模型放在 config.toml 或 --model / --profile 里），弃用时只改一处，契约文件不用动。
2. 额度耗尽 / 要省钱：reasoning_effort 逐级降（high → medium → low）；把一条长单拆成「只读探查单（low）+ 实现单（medium）」两步；用 --output-schema 减少来回澄清的轮次。
3. --output-schema 不被支持或模型填不出合法 JSON：退到「标记法」——在 prompt 里要求回执夹在 `=== BEGIN_JSON ===` 与 `=== END_JSON ===` 之间，再用 awk/sed 剥 ANSI 色码后提取，最后 jq 校验。
4. 协议不匹配（429 / 404 / 空流）：先用 `--sandbox read-only` 跑一条最小命令定位，确认走的是 Responses API 还是 Chat Completions，再决定是换 provider 还是加转换网关。
5. 验证命令在本机跑不了（缺依赖 / 需要外网 / 需要数据库）：降级为「类型检查 + 目标单测」的本地子集，并在契约里明写「若命令无法运行，报告原因并停下，不要猜测结果」。
6. Hooks 未授权：新加的 hook 必须先 `/hooks` 授权，未授权的 hook 会被静默跳过——门禁看起来在跑其实没生效。改动后务必故意造一次失败验证它真会拦。
7. 契约太长导致 AGENTS.md 超 32 KiB：把场景模板移出 AGENTS.md，改成 skills（按需加载）或独立的 tasks/*.md 文件。

### 版本与生效时间

四要素结构源自官方 Best practices 页的 Goal / Context / Constraints / Done when，2026-03 至今稳定未变；配套的 `codex exec --json` 与 `--output-schema` 长期可用；`--full-auto` 于 v0.147.0（2026-08-07）移除；`codex exec fork` 与 `/export` 于 v0.148.0（2026-08-18）加入。

### 可自动化程度

高。这是四要素里 ROI 最高的部分：`codex exec --json` 把过程变成 JSONL 事件流，`--output-schema` 强制回执结构，`-o` 落盘，cron / launchd / GitHub Actions 可直接跑；成功判定统一看 `type=="turn.completed"`（出现 `turn.failed` 或 `error` 即失败）。不想自己写 cron 时可用 Automations（2026-03 GA，自带 worktree 隔离与 Triage 收件箱）。

### 优先级

P0。排在 AGENTS.md、Hooks、并行分档之前——没有合格的单，后面所有自动化都是在放大错误。

### 对一人公司的适用性

几乎是为一人公司量身定做的。无同事 review → 四要素把「人肉 review」换成「命令 review」；成本敏感 → 明确的 Done when 与熔断条款直接砍掉无效迭代轮次，这是最省钱的一档；需要异步杠杆 → 收尾动作让你早上第一眼就能判定成败，不必重跑一遍。唯一代价是派单前多花 3–5 分钟写契约，而这 3–5 分钟换回的是整个睡眠时段。

### 信息来源

1. OpenAI 官方 Best practices（四要素 Goal/Context/Constraints/Done when、AGENTS.md 分层）：<https://developers.openai.com/codex/learn/best-practices>
2. codex exec JSONL Reference（事件 schema、全部 flag、--output-schema、CI 模式）：<https://codex.danielvaughan.com/2026/04/08/codex-exec-jsonl-reference>
3. Codex CLI Non-Interactive Pipelines（exec / resume / fork、结构化输出）：<https://codex.danielvaughan.com/2026/05/03/codex-cli-non-interactive-pipelines-exec-resume-structured-output>
4. Codex CLI Automations and Scheduled Tasks（无人值守、沙箱基线、CODEX_API_KEY）：<https://codex.danielvaughan.com/2026/03/27/codex-cli-automations-scheduled-tasks>
5. OpenAI Codex changelog（v0.147.0 移除 --full-auto 等）：<https://help.openai.com/en/articles/11428266-codex-changelog>
6. Codex CLI Prompting Guide（沙箱 / 审批 / profile / /init 后要人工改）：<https://sureprompts.com/blog/codex-cli-prompting-guide>
7. Shipyard Codex CLI Cheatsheet（config 默认值表）：<https://qa.shipyard.build/blog/codex-cli-cheat-sheet/>
8. OpenAI Cookbook — Iterating Development Workflows with Codex（GOALS.md / PROMPTS.md / PLANS.md 约定）：<https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex>

### 待核实

- Automations GA 的确切日期仅能确认在 2026-03，具体日不详 [不确定]
- PostToolUse / PreToolUse 的 matcher 是否支持 Edit|Write（有来源称仅 Bash 生效，另有示例写 apply_patch|write）[不确定]
- approval_policy 官方默认值究竟是 untrusted 还是 on-request，不同来源口径冲突（另有资料称 untrusted 已退役）[不确定]
- sandbox_mode 官方默认值一处记为 read-only、一处记为 workspace-write [不确定]
- 熔断轮次「连续 3 次」没有官方依据，来自社区实践建议 [不确定]

## 2. 派单验收门禁

### 核心做法

验收门禁要解决的唯一问题是：你不在场时，怎么判断 Codex 到底做没做完。答案是把「收尾动作」从一句软约定（「改完告诉我」）升级成三件可核对的硬证据 + 一道自动拦截。

【三件证据】

① 可 replay 的 transcript 片段  
每次 codex 调用都会自动往 ~/.codex/sessions/<年>/<月>/<日>/rollout-<UTC 时间>-<session-id>.jsonl 追加一份 append-only 的 JSONL transcript，逐行记录模型看到、想了、执行、产出的全部事件。它与 `codex exec --json` 输出的事件同构，所以同一套 jq 脚本两边都能用。  
三种用法：

- 事后取证：jq 抽出「跑了哪些命令 / 退出码 / 改了哪些文件 / 每轮 token」。
- 断点续跑：`codex resume --last` 或 `codex exec resume --last "新指令"` 重放 transcript 恢复完整上下文（含已批准的计划与命令输出，不会重新问一遍权限）。
- 降噪复盘：`codex debug trace-reduce <rollout>` 把长 trace 压成工具 / 子 agent / 审批边界的摘要（v0.125.0 起）。

② PR 范围回执  
两道口径互相印证，缺一不可：

- 模型自述：结论块里的 changed_files 清单。
- 客观事实：`git status --short` + `git diff --stat`，以及 JSONL 里的 file_change 事件（changes[].path + kind: add/update/delete）。  
  两者必须对齐。模型说改了 3 个文件而 git 显示 7 个，就是越界信号，直接打回。

③ 失败时的报告格式  
用 `--output-schema` 把回执约束成固定 JSON（result / changed_files / verify{command,exit_code,output_tail} / residual_risk / not_done），脚本可解析、可归档、可 diff。模型填不出合法 JSON 时，降级为标记法（=== BEGIN_JSON === / === END_JSON ===）再加 awk 提取。

【一道拦截：把门禁从软约定变成硬执行】  
靠提示词要求「跑测试再交回」是软的，模型赶工时会跳过。用 hooks 把它变硬：

- PostToolUse（matcher 命中写文件的工具）+ exit 2：写完就跑检查，不合格就把错误输出替换掉工具结果，模型当场看到并自修，一轮内闭环。
- Stop（turn 结束时触发）：`{"decision":"block","reason":"…"}` 不是拒绝，而是让 Codex 生成一条续跑提示，逼它回去补验证再交。
- 关键：新加的 hook 必须先 `/hooks` 授权，未授权的 hook 被静默跳过；改完务必故意造一次失败，确认它真的会拦。

【早间验收的四个动作（5 分钟内完成）】

1. 看 handoff.json 的 result 字段：pass / fail / blocked。
2. 看 git diff --stat，和 changed_files 对齐，扫一眼有没有越界文件。
3. 看 verify.command 与 exit_code——必须是你在契约里指定的那条命令，不是它自己临时想出来的。
4. 只在 result=pass 时才读代码细节；fail / blocked 直接把 events.jsonl 里的 turn.failed 贴回去续跑。

### 可直接复制的模板命令配置

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【1｜回执 schema：~/.codex/schemas/handoff.json】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{  
"$schema": "<https://json-schema.org/draft/2020-12/schema>",  
"type": "object",  
"additionalProperties": false,  
"required": ["result", "changed_files", "verify", "residual_risk", "not_done"],  
"properties": {  
"result": { "enum": ["pass", "fail", "blocked"] },  
"changed_files": { "type": "array", "items": { "type": "string" } },  
"verify": {  
"type": "object",  
"additionalProperties": false,  
"required": ["command", "exit_code", "output_tail"],  
"properties": {  
"command": { "type": "string" },  
"exit_code": { "type": "integer" },  
"output_tail": { "type": "string" }  
}  
},  
"residual_risk": { "type": "string" },  
"not_done": { "type": "string" }  
}  
}

配套要求（写进 prompt 末尾）：  
「最终回复必须是符合上述 schema 的单个 JSON 对象，不要加 Markdown 代码围栏，不要加解释文字。output_tail 填验证命令最后 40 行原文。」

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【2｜门禁脚本：~/bin/codex-gate（无人值守跑单 + 自动验收）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#!/usr/bin/env bash

# 用法：codex-gate ./tasks/xxx.md ~/repos/myapp

set -uo pipefail  
TASK_FILE="$1"; REPO="${2:-$PWD}"
STAMP="$(date +%Y%m%d-%H%M%S)"  
OUT="$HOME/codex-orders/$STAMP"; mkdir -p "$OUT"
cd "$REPO" || exit 1

# ① 跑单：JSONL 全量留痕 + 结构化回执落盘

codex exec   
--cd "$REPO" \   --sandbox workspace-write \   --ask-for-approval never \   --json \   --output-schema "$HOME/.codex/schemas/handoff.json"   
-o "$OUT/handoff.json" \
  "$(cat "$TASK_FILE")" \
  2> "$OUT/stderr.log" > "$OUT/events.jsonl"
EXEC_RC=$?

# ② 门禁 A：turn 级别有没有失败

echo "== 门禁 A：turn 状态 =="  
if jq -e 'select(.type=="turn.failed")' "$OUT/events.jsonl" >/dev/null 2>&1; then
  echo "[FAIL] 存在 turn.failed"
  jq -c 'select(.type=="turn.failed" or .type=="error")' "$OUT/events.jsonl"  
fi  
if [ "$EXEC_RC" -ne 0 ]; then echo "[FAIL] codex exec 退出码 $EXEC_RC"; fi

# ③ 门禁 B：有没有非 0 退出的命令

echo "== 门禁 B：命令退出码 =="  
jq -r 'select(.type=="item.completed" and .item.type=="command_execution" and .item.exit_code!=0)  
| "[非0] exit=(.item.exit_code)\t(.item.command)"' "$OUT/events.jsonl"

# ④ 门禁 C：模型自述的改动 vs git 实际改动，必须对齐

echo "== 门禁 C：范围回执对齐 =="  
git status --short > "$OUT/git-status.txt"
git diff --stat  > "$OUT/git-diff-stat.txt"  
jq -r '.changed_files[]?' "$OUT/handoff.json" 2>/dev/null | sort > "$OUT/claimed.txt"  
git status --porcelain | awk '{print $NF}' | sort > "$OUT/actual.txt"  
if diff -u "$OUT/claimed.txt" "$OUT/actual.txt" > "$OUT/scope-diff.txt"; then
  echo "[OK] 自述与实际一致"
else
  echo "[WARN] 自述与实际不一致，疑似越界："
  cat "$OUT/scope-diff.txt"  
fi

# ⑤ 门禁 D：token 计量（成本敏感必看）

echo "== 门禁 D：用量 =="  
jq -s '[.[] | select(.type=="turn.completed") | .usage.input_tokens] | add' "$OUT/events.jsonl" | xargs -I{} echo "input_tokens={}"
jq -s '[.[] | select(.type=="turn.completed") | .usage.cached_input_tokens] | add' "$OUT/events.jsonl" | xargs -I{} echo "cached_input_tokens={}"  
jq -s '[.[] | select(.type=="turn.completed") | .usage.output_tokens] | add' "$OUT/events.jsonl" | xargs -I{} echo "output_tokens={}"

# ⑥ 汇总

echo "== 回执 =="  
if [ -s "$OUT/handoff.json" ]; then jq . "$OUT/handoff.json"; else  
echo "[FAIL] 无结构化回执，见 $OUT/events.jsonl / stderr.log"
fi
echo "产物目录：$OUT"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【3｜transcript 取证：jq 片段集（rollout 与 exec --json 通用）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 今天的 rollout 目录

D=~/.codex/sessions/$(date +%Y/%m/%d)

# 事件类型分布（快速判断单子跑得顺不顺）

cat $D/rollout-*.jsonl | jq -r '.type' | sort | uniq -c | sort -rn

# 模型实际跑了哪些命令 + 退出码（最关键的一条）

cat $D/rollout-*.jsonl | jq -r 'select(.item.type=="command_execution")  
| "(.item.exit_code)\t(.item.command)"'

# 改了哪些文件（add / update / delete）

cat $D/rollout-*.jsonl | jq -r 'select(.item.type=="file_change") | .item.changes[] | "(.kind)\t(.path)"'

# 审批决策（有没有绕过你的授权）

cat $D/rollout-*.jsonl | jq -r 'select(.item.type=="approval_decision") | "(.item.action)\t(.item.decision)"'

# 每轮 token（成本归因）

cat $D/rollout-*.jsonl | jq -r 'select(.type=="turn.completed") | .usage'

# 长 trace 压成摘要（v0.125.0+，排查子 agent 分支极好用）

codex debug trace-reduce $D/rollout-*.jsonl

# 拿到 session id，用于精确 replay

cat $D/rollout-*.jsonl | jq -r 'select(.type=="thread.started") | .thread_id'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【4｜replay 三件套】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 交互式续跑最近的会话（保留完整审批历史，不会重复问权限）

codex resume --last

# 按 session id 精确续跑

codex resume 0199a213-81c0-7800-8aa1-bbab2a035a53

# 非交互式续跑，并追加新指令（CI / 定时任务的正确姿势）

codex exec resume --last "现在给你刚才改的文件补单元测试，然后重跑验证命令"

# 跨目录找会话（默认只筛当前工作目录）

codex resume --all  
codex resume --cd /path/to/other/project --last

# 分叉：保留原 transcript 不动，另起一条线程探索（v0.148.0+）

codex exec fork --last "试试另一种实现，不要动我之前那版"

# 把整段 TUI 会话导出成 Markdown 归档（v0.148.0+）

/export ~/codex-orders/2026-08-31-login-fix.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【5｜硬拦截：hooks 配置（两种写法，二选一）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

▸ 写法 A：config.toml（较新，推荐）

# ~/.codex/config.toml

[features]  
codex_hooks = true

[[hooks.PostToolUse]]  
matcher = "Edit|Write"

[[hooks.PostToolUse.hooks]]  
type = "command"  
command = 'npx tsc --noEmit >&2 || exit 2'  
timeout = 120

▸ 写法 B：hooks.json（项目级 .codex/hooks.json 或全局 ~/.codex/hooks.json，两者叠加）

{  
"hooks": {  
"PostToolUse": [  
{  
"matcher": "apply_patch|write",  
"hooks": [  
{  
"type": "command",  
"command": "./scripts/verify-fast.sh",  
"statusMessage": "门禁：跑类型检查与受影响单测...",  
"timeout": 120  
}  
]  
}  
],  
"Stop": [  
{  
"hooks": [  
{  
"type": "command",  
"command": "python3 ~/.codex/hooks/stop-gate.py",  
"timeout": 180  
}  
]  
}  
]  
}  
}

配套脚本 ./scripts/verify-fast.sh（exit 0 放行 / exit 2 阻断并把 stderr 喂回模型）：

#!/usr/bin/env bash  
set -uo pipefail  
npx tsc --noEmit || { echo "类型检查失败，请先修好再继续"; exit 2; }  
pnpm vitest run --changed --passWithNoTests || { echo "受影响单测失败"; exit 2; }  
exit 0

配套 ~/.codex/hooks/stop-gate.py（turn 结束时检查回执齐不齐，不齐就续跑）：

#!/usr/bin/env python3  
import json, sys, subprocess  
payload = json.load(sys.stdin)  
msg = payload.get("last_assistant_message", "")  
need = ["git diff --stat", "exit"]  
if not all(k in msg for k in need):  
print(json.dumps({  
"decision": "block",  
"reason": "交回前必须补：验证命令原文 + exit code + git diff --stat。补齐后重新交回。"  
}))  
sys.exit(0)  
print(json.dumps({"continue": True}))

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【6｜失败报告格式（写进契约，要求模型照填）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 结论

- 结果：失败
- 失败阶段：实现 / 验证 / 环境（三选一）
- 复现命令：<原样可粘贴>
- 原始报错：<贴最后 20 行原文，不要总结>
- exit code：<数字>
- 改动文件：<逐行列出；未改就写「无」>
- 已尝试：<1. … 2. … 3. …>
- 我的判断：<根因推测，标注是推测>
- 需要你决定：<具体选项，不要开放式提问>
- 我未做的事：<一句话>

配套的 blocked（阻塞）分支另加两条：

- 阻塞原因：缺权限 / 缺密钥 / 缺外网 / 需人工决策
- 解锁条件：<做完这一步我就能继续>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【7｜可观测：把门禁接到 OTel（可选，进阶）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ~/.codex/config.toml

[otel]  
log_user_prompt = false

exporter = { otlp-grpc = {  
endpoint = "<http://localhost:4317>"  
}}

开启后 Codex 会输出会话生命周期、API 请求 span、工具审批决策、工具执行结果的结构化 trace，可直接进 Jaeger / Grafana Tempo。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【8｜审计归档脚本（合规 / 留档场景）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#!/usr/bin/env bash

# ~/bin/codex-audit <rollout.jsonl>

F="$1"
echo "=== Codex 会话审计报告 ==="
echo "Session: $(jq -r 'select(.type=="thread.started") | .thread_id' "$F")"
echo "--- 执行的命令 ---"
jq -r 'select(.item.type=="command_execution")   | "\(.item.status) exit=\(.item.exit_code) \(.item.command)"' "$F"  
echo "--- 改动的文件 ---"  
jq -r 'select(.item.type=="file_change") | .item.changes[] | "(.kind) (.path)"' "$F"
echo "--- 审批决策 ---"
jq -r 'select(.item.type=="approval_decision") | "\(.item.action): \(.item.decision)"' "$F"

### 关键参数

官方默认值 → 一人公司推荐值（★=必须改）

| 参数 / 机制                            | 官方默认                           | 一人公司推荐值               | 说明                           |
| ---------------------------------- | ------------------------------ | --------------------- | ---------------------------- |
| rollout 落盘                         | 每次调用都写                         | 保持（不要加 --ephemeral）   | 唯一例外是处理敏感数据                  |
| --ephemeral                        | 关闭                             | 保持关闭 ★                | 加了就没有 transcript，门禁第①件证据直接消失 |
| rollout 路径                         | ~/.codex/sessions/<年>/<月>/<日>/ | 保持                    | session id 服务端生成，不能用 CLI 覆写  |
| aggregated_output 截断               | 64 KiB                         | 知道即可，别当完整证据           | 超长日志末尾是 `...(truncated)`     |
| hooks timeout                      | 600 秒                          | 30–180 秒 ★            | 默认太长，无人值守失败单会空转              |
| hook 退出码                           | 0 通过 / 2 阻断 / 其他仅告警            | 门禁用 2 ★               | exit 2 时 stderr 作为原因喂回模型     |
| Stop 事件输出                          | 必须 JSON                        | 必须 JSON ★             | 纯文本在 Stop 事件上无效              |
| [features] codex_hooks             | false（实验特性）                    | true ★                | 不开就没有硬拦截                     |
| CODEX_SESSION_ID 环境变量              | v0.148.0 起可用                   | hook 里用它关联 transcript | 便于回执与 rollout 对账             |
| history.persistence                | none                           | save-all（想做周回顾时）      | 与 rollout 是两套东西              |
| --output-schema                    | 无                              | 必配 ★                  | 回执能否被脚本解析的分水岭                |
| approval_policy                    | on-request                     | 无人值守 never ★          | 非 TTY 下不设会挂死                 |
| --ask-for-approval never + sandbox | —                              | workspace-write ★     | 二者必须成对显式写                    |

必须改的四项：--ephemeral 不加、codex_hooks=true、门禁脚本 exit 2、--output-schema 配好。这四项缺一项，门禁就退化回「模型的自述」。

### 常见坑

1. 你以为有 transcript，其实根本没有跑单时加了 `--ephemeral`。这是最隐蔽的一个：加了之后一切正常，只是出事时没有任何证据可查。
2. 归档时用 `zstd --rm` 或 mv 压缩 / 移动了 rollout 文件，之后 `codex resume` 对这批会话全部失效。要归档就只归档确认不会续跑的，且保留 30 天原始 JSONL 不压缩。
3. 回执只写「改了 3 个文件」，没有 `git diff --stat`。无法核对，等于没有 PR 范围回执。必须两道口径互相对齐。
4. 相信模型的自述而不看 `exit_code`。模型说「测试通过」但命令 exit 1 的情况非常常见，一定要用 `item.exit_code` 判定，不要用 `agent_message` 的自然语言。
5. file_change 事件只发 `item.completed`，没有 `item.started`；web_search 同样。按 started 去过滤会什么都捞不到。
6. `codex exec` 与 TUI 的会话语义不同：`codex exec resume` 默认只筛当前工作目录下起的会话，跨目录必须加 `--all`。
7. 未授权的 hook 被静默跳过。新加 hook 后必须 `/hooks` 授权，并且故意造一次失败验证它真会拦——否则门禁形同虚设，你会以为自己在被保护。
8. Stop 事件必须返回 JSON，纯文本 stdout 无效。这一点和 SessionStart / UserPromptSubmit 不一样，容易踩。
9. PreToolUse / PostToolUse 的 matcher 覆盖范围在不同版本和不同资料里说法不一：有来源称仅 Bash 生效，也有示例写 `Edit|Write` 或 `apply_patch|write`。用之前先实测，别假设。
10. 同一事件的多个 hook 并发执行，没有顺序保证，且一个 hook 拦不住另一个。不要写互相依赖的 hook 链。
11. `codex exec --full-auto` 已在 v0.147.0（2026-08-07）移除，仍在大量教程里出现，脚本会直接报未知参数。
12. 沙箱默认断网（workspace-write 的 network_access=false），验证命令依赖装包或连库时会失败，且报错常常看不出是网络原因。
13. `type=="error"` 不全是致命错误：断线重连时会发 `"Reconnecting... 1/5"` 这类瞬时通知，判断失败要排除它们，否则会误杀成功的单。
14. JSONL 没有 schema 版本字段。`item_type`→`type`、`assistant_message`→`agent_message` 的改名（v0.44.0）意味着老脚本会静默失效——解析要做双字段兼容，并在 CI 里锁死 Codex 版本。
15. Automations 里 pin 住（收藏）已完成的 run 会阻止对应 worktree 被清理，worktree 会堆积。
16. hook 目前在 Windows 上不可用（实验特性，官方说明 Windows 支持暂时关闭）。

### 降级与回退路径

1. hooks 在你的版本上不生效 / 不支持目标工具：退回到「软约定 + 硬校验」——提示词里照旧要求三件证据，早上用 codex-gate 脚本离线核对 events.jsonl 与 git diff，不合格就打回续跑。可靠性下降但可用。
2. `--output-schema` 不支持或模型填不出合法 JSON：降级为标记法，要求回执夹在 `=== BEGIN_JSON ===` / `=== END_JSON ===` 之间，用 sed 剥 ANSI 色码后 awk 提取，再 jq 校验。
3. rollout 文件丢失或被压缩：`codex exec --json` 的 tee 出来的 events.jsonl 就是等价物，日常跑单务必 tee 一份到自己的目录，别只依赖 ~/.codex/sessions。
4. `codex resume` 因归档失效：还有 `codex exec resume <session-id>` 和 `codex exec fork --last`；两条都不行就只能从 events.jsonl 手工重建上下文（把关键 file_change 与结论块粘进新单）。
5. 门禁本身太贵（每次写完文件都跑全量测试，token 暴涨）：把 PostToolUse 的检查换成最快的那条（tsc --noEmit 或 --changed 单测），全量测试留给 Stop 钩子和 CI。
6. 沙箱 / 协议问题导致验证命令必失败：先 `--sandbox read-only` 跑最小命令定位，确认 Responses API 还是 Chat Completions；只支持 Chat Completions 的 provider 需要转换网关。
7. 额度耗尽：把门禁降级为「只跑类型检查」，并在契约里明写「无法验证时必须声明未验证，不得声称通过」。

### 版本与生效时间

rollout JSONL 与 `codex exec --json` 事件同构，长期可用；v0.125.0（2026-04）在 turn.completed 中引入 reasoning_tokens 细分并加入 `codex debug trace-reduce`；v0.141.0（2026-06-18）修复了 hook 信任在 `codex exec` 续跑时的保持问题，以及阻断型 PostToolUse 对 code-mode 工具调用的拦截；v0.148.0（2026-08-18）加入 `/export`、codex exec fork、异步 hooks 与 hooks 调 MCP 工具、`/status` 显示 credits 估算，并新增 CODEX_SESSION_ID 环境变量；v0.149.0（2026-08-20）加入 codex queue 与 agents 仪表盘；v0.150.0 加入 Interrupt hooks。

### 可自动化程度

高，且这是本手册中自动化收益最高的一环。`codex exec --json` 全量留痕、`--output-schema` 结构化回执、`-o` 落盘、jq 判定成功失败、git diff 核对范围，全部可无人值守；接 cron / launchd / GitHub Actions 都行。硬拦截靠 hooks（PostToolUse exit 2、Stop 续跑）真正把「跑测试再交回」变成不可跳过的步骤。不想自建 cron 时用 Automations（2026-03 GA，带 worktree 隔离与 Triage 收件箱）。

### 优先级

P0。与契约式派单模板并列为第一优先级：契约负责「下单对」，门禁负责「收货准」，二者缺一，异步杠杆就不成立。

### 对一人公司的适用性

极高，而且是三个前提里「无同事 review」唯一的替代方案。没有同事帮你过 diff，就只能靠可 replay 的 transcript + 客观命令退出码 + 范围对齐这三件证据来代替人眼；成本敏感则要求门禁必须便宜（用最快的检查拦在最前面，全量测试只在 Stop 和 CI 跑）；异步杠杆的全部价值都押在「早上第一眼就能判定成败」上，而这正是收尾动作的意义。投入产出比是整本手册里最高的一处。

### 信息来源

1. Codex CLI Rollout Files: Session Recording, Replay, and Audit Trails（路径结构、事件类型、jq 取证、resume / fork、审计脚本、OTel）：<https://codex.danielvaughan.com/2026/04/29/codex-cli-rollout-files-session-recording-replay-audit-trails>
2. codex exec --json event cheatsheet（完整事件 schema、字段、退出码语义、64 KiB 截断）：<https://littlebearapps.com/help/untether/exec-json-cheatsheet>
3. codex exec JSONL Reference（flag 全表、--output-schema、CI 模式、schema drift 警告）：<https://codex.danielvaughan.com/2026/04/08/codex-exec-jsonl-reference>
4. Codex CLI Non-Interactive Pipelines（exec / resume / fork、结构化输出）：<https://codex.danielvaughan.com/2026/05/03/codex-cli-non-interactive-pipelines-exec-resume-structured-output>
5. Codex CLI Hooks Reference（事件表、stdin/stdout schema、退出码、限制）：<https://symposium.dev/design/agent-details/codex-cli.html>
6. Codex CLI Best Practice: Hooks（hooks.json 结构、各事件输入输出、Stop 的 block 语义）：<https://github.com/shanraisshan/codex-cli-best-practice/blob/main/best-practice/codex-hooks.md>
7. Codex CLI v0.148.0 Release Notes（/export、exec fork、异步 hooks、成本估算）：<https://codex.danielvaughan.com/2026/08/19/codex-cli-v0148-release-markdown-export-async-hooks-mcp-cost-visibility-bedrock-runtime-session-fork>
8. OpenAI Codex changelog（v0.147.0 移除 --full-auto、v0.150.0 Interrupt hooks）：<https://help.openai.com/en/articles/11428266-codex-changelog>
9. Codex CLI Automations and Scheduled Tasks（无人值守、Triage 收件箱、worktree）：<https://codex.danielvaughan.com/2026/03/27/codex-cli-automations-scheduled-tasks>

### 待核实

- PreToolUse / PostToolUse 的 matcher 实际支持的工具名集合（Bash / Edit|Write / apply_patch|write 三种说法并存，版本差异未确认）[不确定]
- `codex exec fork` 的具体调用语法（v0.148.0 引入，官方示例不完整）[不确定]
- approval_decision 是否确实作为 item.completed 的一种 item.type 稳定出现在 exec --json 流中（rollout 文档列出，cheatsheet 未列）[不确定]
- hook 在 Windows 上是否仍完全不可用 [不确定]
- hooks.json 与 config.toml 的 [[hooks.*]] 两种写法是否在所有版本都并行支持，还是后者为新版首选 [不确定]
- plan_update 与 todo_list 两个 item 类型的关系与现状（cheatsheet 只列 todo_list，rollout 文档只列 plan_update）[不确定]

## 3. AGENTS.md 写法与长度控制

### 核心做法

AGENTS.md 是 Codex 每次会话自动加载的项目说明书。它的价值不在「写全」，而在「每一条都在改变模型的行为」。

【加载机制（决定了写法）】  
Codex 在会话启动时一次性构建指令链，顺序是：

1. 全局层：~/.codex/AGENTS.override.md（存在就用它），否则 ~/.codex/AGENTS.md
2. 项目层：从 Git 根目录一路向下走到你的当前工作目录，每个目录里按 AGENTS.override.md → AGENTS.md → project_doc_fallback_filenames 里的备用名（如 CODEX.md、.agents.md、TEAM_GUIDE.md）的顺序取**第一个存在的文件**，每个目录最多取一个
3. 合并：按「根 → 叶」顺序拼接。越靠近你工作目录的文件排在越后面，因此优先级越高

三个必须记住的细节：

- 全局文件作为 user instructions 单独传入，**不占用** project_doc_max_bytes 预算。精简全局文件换不来项目层的空间，但它照样吃上下文窗口，所以还是要短。
- 项目层文件累计超过 project_doc_max_bytes（默认 32768 字节 / 32 KiB）时，**越过预算的那个文件被前缀截断，它之后的所有文件被整个跳过**。这一过程只写一条 tracing::warn，TUI 里看不到，是彻底的静默失败（openai/codex#7138）。
- 因为是「根 → 叶」拼接，越深、越具体、你最近才写的文件排在越后面，也就**越先被砍掉**。症状是：模型遵守你含糊的根级规则，却无视你刚加的详细服务级规则——看起来像模型退步了，其实是字节预算超了。

【为什么啰嗦会烧钱】

1. 每一条规则都是每次请求都重复付的税。AGENTS.md 在系统提示里，每个 turn 都要重发一遍；一个 8000 token 的 AGENTS.md，跑 40 轮就是 32 万 token 的输入成本。命中缓存能打折，但缓存命中的部分照样计费，且长会话 compact 后还要重付。
2. 无效规则是纯亏损。模型已经知道的东西（`export default function` 是 React 组件、pytest 怎么跑）写进去不会让它更聪明，只会挤掉上下文。
3. 挤掉的是真正稀缺的东西——对话窗口。规则越长，留给代码、报错、diff 的空间越小，模型越容易在长任务里失忆，进而需要更多轮次补救。
4. 最贵的是含糊。一句「遵循最佳实践」不如「用 Vitest 不用 Jest」。前者不产生任何行为约束，却同样收费。
5. 叠加效应：MCP server 的 tool schema 也吃上下文，长 AGENTS.md + 一堆 MCP server 会一起把窗口吃穿。

【必写项（只写这些）】

- 仓库布局与关键目录
- 怎么跑起来 / 构建 / 测试 / lint 的**确切命令**
- 工程约定（命名、错误处理模式、测试框架选型）
- PR 期望与「怎么算做完、怎么验证」
- 约束与 do-not 规则
- Codex 从代码里推断不出来的项目特有行为

【禁忌】

- 不写模型已知的通识
- 不放长示例（只留规则，示例放 skills 或 docs）
- 不写「遵循最佳实践」这类无约束力的软话
- 不把所有服务的规则堆进一个根文件
- 不留空的 AGENTS.override.md（空文件也会遮蔽同级 AGENTS.md，导致该目录贡献为零）
- 不写会随代码腐化的内容（具体函数名、行号）

【维护节奏】  
`/init` 生成脚手架 → 人工删掉一半 → 之后只在「同一个错误出现第二次」时追加一条。每加一条，就想清楚它换掉了哪一条。

### 可直接复制的模板命令配置

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【1｜三层结构模板（推荐长度：20 / 50 / 30 行）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

▸ Layer 1 · ~/.codex/AGENTS.md（全局个人偏好，控制在 20 行内）

# Working Agreements

- 修改源码后必须跑测试
- 装依赖优先用 pnpm
- 新增生产依赖前先问我
- 新文件一律 TypeScript strict 模式
- 不要 git commit / git push，除非我明确要求

▸ Layer 2 · 仓库根 AGENTS.md（项目约定，控制在 50 行内）

# Repository Rules

- 测试用 Vitest，不要用 Jest
- 错误处理照抄 src/lib/errors.ts 的模式
- 提 PR 前跑 pnpm lint && pnpm test
- 新增 API 端点必须带 OpenAPI 注解
- 数据库变更必须在 migrations/ 下放迁移文件
- 测试文件与源码同目录：foo.ts -> foo.test.ts

▸ Layer 3 · 子目录 AGENTS.md（模块特有规则，控制在 30 行内）

# Payments Service Rules

- 一律走统一错误处理器，不要裸 throw
- 所有公开端点必须加限流
- 必须走 payments 专用连接池
- 绝不许 print / log 卡号、CVV

▸ 覆盖层 · 子目录 AGENTS.override.md（临时规则，用完即删）

# TEMPORARY: v3 迁移完成后删除（目标 2026-09-30）

- 新端点一律用 src/routes/v3/ 的 v3 router
- 不要动任何 v1 / v2 路由
- 迁移跟踪文档：docs/v3-migration.md
- 新中间件统一用 src/lib/auth-v3.ts 的 AuthContext

注意：同目录下同时存在 AGENTS.override.md 与 AGENTS.md 时，**只有 override 生效**，普通 AGENTS.md 被完全忽略。全局层同理。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【2｜完整中文范例（一人公司 / 单体 Web 项目，可直接抄）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 项目说明

个人独立开发的 Next.js + FastAPI 单体项目。目标是低成本、可异步验收。

## 目录

- apps/web        前端，Next.js + TypeScript
- apps/api        后端，FastAPI（Python 3.12）
- migrations      数据库迁移，改动需显式批准
- tests           端到端测试

## 常用命令

- 前端单测：pnpm --filter web vitest run <文件路径>
- 后端单测：cd apps/api && uv run pytest -q <文件路径>
- 类型检查：pnpm --filter web tsc --noEmit
- lint：pnpm lint
- 全量本地校验：pnpm lint && pnpm test

## 约定

- TypeScript 用 camelCase，Python 用 snake_case
- 错误处理统一走 apps/api/src/lib/errors.py 的 AppError
- 新增 API 必须在 apps/api/src/routes/ 下注册并补一条 e2e
- 不要引入新依赖；确实需要就先问我

## 派单契约（默认遵守）

- 开工前先复述：可编辑范围 / 禁止改动范围 / 验证命令 / 收尾动作
- 验证命令必须原样执行并贴原始输出与 exit code
- 同一条命令连续失败 3 次就停下报告
- 不允许修改现有测试来使其通过
- 交回必带：验证输出原文、git status --short、git diff --stat、结论块

## 禁止

- 不要重构无关代码
- 不要动 migrations/ 与公开 API 响应格式
- 不要 git commit / git push
- 不要升级依赖版本

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【3｜配置片段：~/.codex/config.toml 相关项】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 项目级 AGENTS.md 的累计字节预算，默认 32768（32 KiB）

project_doc_max_bytes = 32768

# 若团队已有文档，可让 Codex 也认这些文件名（按序回退）

project_doc_fallback_filenames = ["AGENTS.md", "CODEX.md", ".agents.md", "TEAM_GUIDE.md"]

# 万不得已才调大；优先拆文件

# project_doc_max_bytes = 65536

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【4｜体积体检：一行命令看有没有超预算】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 列出从 Git 根到当前目录，每层实际会加载的那个文件及其字节数

# （人工版：先看有哪些候选文件）

find . -name "AGENTS.md" -o -name "AGENTS.override.md" | sort

# 全局文件（不计入 project_doc_max_bytes，但照样吃上下文）

wc -c ~/.codex/AGENTS.md ~/.codex/AGENTS.override.md 2>/dev/null

# 项目层累计字节（判断是否逼近 32768）

find . -name "AGENTS*.md" -not -path "*/node_modules/*" -exec wc -c {} + | tail -1

# 有没有被遗忘的 override（最常见的「规则莫名其妙不生效」元凶）

find . -name "AGENTS.override.md" -type f

# 有没有空文件在遮蔽同级 AGENTS.md

find . -name "AGENTS*.md" -type f -empty

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【5｜诊断 prompt：让 Codex 自己报告加载了什么】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

用法：`codex --sandbox read-only --ask-for-approval on-request "<下面这段>"`

「读一下我 config.toml 里的 project_doc_max_bytes，用那个值而不是假设的 32 KiB。然后从本仓库根目录一路走到我的工作目录，逐层报告 Codex 实际会加载的那一个文件（AGENTS.override.md，否则 AGENTS.md，否则配置的备用名）。注意规则是取第一个『存在』的文件而不是第一个非空文件——空的 AGENTS.override.md 依然会遮蔽同级的 AGENTS.md，让整个目录贡献为零，请把发现的空候选文件标出来。（取第一个非空那条规则只适用于全局 ~/.codex 文件。）请排除全局 ~/.codex/AGENTS.md：它作为 user instructions 加载，不计入这个预算。给我每个文件的字节数和按加载顺序的累计值。如果累计从未触顶就明说；如果触顶了，指出是哪个文件越线、以及在它内部的哪个字节偏移——那个文件只加载到该偏移，之后的文件会被整个跳过；正好卡在边界上的文件不会被截断但仍会阻断后面的文件。最后列出我当前实际丢失了哪些具体指令。」

▸ 精简版（日常快速检查用）：

codex --sandbox read-only --ask-for-approval on-request   
"Summarize the current instructions and list all instruction files you loaded."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【6｜让 Codex 帮你生成初稿（/init 之后再人工砍一半）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

「分析本仓库的结构、测试模式、lint 配置和编码约定，生成一份 AGENTS.md，包含：测试命令、lint 命令、命名约定、文件组织模式，以及你能从代码里推断出的项目特有规则。只写从代码推断不出来的东西，通识不要写。控制在 50 行以内。」

生成后必做：/init 或上面这段生成的是起点不是成品，官方明确说过要人工改成团队真实的构建 / 测试 / review / 发布方式。第一刀通常能砍掉一半。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【7｜瘦身决策表（AGENTS.md 太长时的处置顺序）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| 症状           | 先做                         | 再做              | 最后才做                     |
| ------------ | -------------------------- | --------------- | ------------------------ |
| 根文件 >50 行    | 删掉模型已知的通识                  | 拆到子目录 AGENTS.md | 调大 project_doc_max_bytes |
| 深层规则不生效      | 查 project_doc_max_bytes 累计 | 拆文件 / 缩短根文件     | 调大到 65536                |
| 规则多但都想留      | 按服务拆成 <30 行的子文件            | 把长示例移进 skills   | —                        |
| 临时规则         | 放 AGENTS.override.md，用完删   | —               | —                        |
| 硬约束（安全 / 合规） | 移进 .rules / execpolicy     | —               | —                        |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【8｜顺手关掉别的上下文大户】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ~/.codex/config.toml

# 不用的 MCP server 直接禁用——每个 server 的 tool schema 都常驻上下文

[mcp_servers.some-unused]  
enabled = false

# 不需要推理摘要时关掉，省输出

hide_agent_reasoning = true  
model_reasoning_summary = "none"

自查命令：/status（看剩余上下文与生效配置）、/mcp（看连了几个 server）

### 关键参数

官方默认值 → 一人公司推荐值（★=必须改）

| 参数                             | 官方默认                        | 一人公司推荐值                        | 说明                                 |
| ------------------------------ | --------------------------- | ------------------------------ | ---------------------------------- |
| project_doc_max_bytes          | 32768（32 KiB）               | 保持 32768，不调大                   | 触顶是静默截断，调大只是掩盖拆分问题                 |
| project_doc_fallback_filenames | ["AGENTS.md"]               | 团队已有文档时加 CODEX.md / .agents.md | 否则不动                               |
| 全局文件是否计入预算                     | 否（作为 user instructions 单独传） | —                              | 精简它换不来项目层空间，但仍省上下文                 |
| Layer 1 全局行数建议                 | 无官方规定                       | ≤ 20 行                         | 社区共识                               |
| Layer 2 根文件行数建议                | 无官方规定                       | ≤ 50 行                         | 社区共识；另有中文资料给「≤100 行软建议 / 300 行硬上限」 |
| Layer 3 子目录行数建议                | 无官方规定                       | ≤ 30 行                         | 社区共识                               |
| 每个目录取几个文件                      | 1（override 优先）              | 保持 ★                           | 同目录放两个等于后一个白写                      |
| model_reasoning_summary        | auto                        | 省钱时改 none                      | 关掉省输出 token                        |
| hide_agent_reasoning           | false                       | CI / 省 token 时 true            | —                                  |
| mcp_servers.*.enabled          | true                        | 不用的设 false ★                   | 每个 MCP server 常驻吃上下文               |
| history.persistence            | none                        | 想做周回顾时 save-all                | 与 rollout 是两套机制                    |
| /status                        | —                           | 每次怀疑配置时先跑                      | 看生效配置与剩余上下文最快的方式                   |

必须改的三项：每个目录只留一个 AGENTS 文件、禁掉不用的 MCP server、把超长根文件拆开。

### 常见坑

1. 【最反直觉】32 KiB 是**静默**前缀截断，而且被砍掉的是最深、最具体、你最近写的那层。因为你按「根 → 叶」拼接，叶子排在最后。症状看着像模型退步——它遵守含糊的根级规则、无视你刚加的详细服务级规则。先查字节预算，别急着怪模型。
2. 空的 AGENTS.override.md 也会遮蔽同级的 AGENTS.md。规则是取第一个「存在」的文件，不是第一个「非空」的文件。结果整个目录贡献为零，且不报错。（取非空那条只适用于全局 ~/.codex 层。）
3. 忘了自己建过 AGENTS.override.md。临时规则用完不删，几周后你百思不得其解为什么服务级规则不生效。`find . -name "AGENTS.override.md"` 应当纳入常规排查。
4. 精简全局文件指望给项目层腾空间——腾不出来，全局文件不占 project_doc_max_bytes。它只省你自己的上下文窗口。
5. 写模型已经知道的东西。把「export default function 是 React 组件」「用 pytest 跑 Python 测试」写进去，是纯付费零收益。判据很简单：删掉这条，模型会不会做错？不会就删。
6. 一条 2000 行的根 AGENTS.md 描述全公司所有规范。正确做法是根文件 100 行 + 每个服务 50 行，单任务实际加载约 150 行。
7. 舍不得删示例。示例应该只留在 skills 里按需加载，AGENTS.md 只留规则。
8. 写「遵循最佳实践」「注意代码质量」这类没有约束力的软话——收费，但不改变任何行为。
9. 长会话里指令被 compact 掉。规则写了但模型中途忘了，看起来像 AGENTS.md 失效。关键约束要在当前 prompt 里重复一遍，或者开新线程。
10. 未信任项目不再提供项目级 AGENTS.md（v0.150.0 的修复）。如果你在别人的仓库或未标记信任的目录里干活，项目规则会整体缺席。用 [projects."<路径>"] trust_level = "trusted" 或 `--cd` 到信任目录。
11. Cloud 任务读的是**已提交**的 AGENTS.md，不是你本地的改动。关键规则没提交 = 云上完全没有。
12. MCP server 的 tool schema 常驻上下文，和长 AGENTS.md 叠加会一起吃穿窗口。不用的要显式 enabled = false。
13. 把会腐化的信息写进去（具体函数名、行号、某个临时文件）。代码一变，规则就变成误导。
14. /init 生成的东西直接当成品用。官方明确说过它只是起点，得改成你真实的构建 / 测试 / review / 发布流程。

### 降级与回退路径

1. 超预算：先拆——根文件砍到 50 行内，把服务级规则移到子目录 AGENTS.md（每层 ≤30 行）。拆完仍不够再考虑 project_doc_max_bytes = 65536，但这是最后手段，因为它只推迟问题且让截断更难察觉。
2. 内容确实多且都必须留：把长文档移出 AGENTS.md，改成 skills（.agents/skills/<name>/SKILL.md）按需加载——skills 只在被匹配或显式调用时进上下文，这是最省的扩容方式。
3. 硬约束（安全、合规、禁止项）：移进 .rules 或 execpolicy，用规则引擎而不是提示词来保证，不受 32 KiB 与 compact 影响。
4. Cloud / CI 环境与本地不一致：把关键规则提交进仓库的 AGENTS.md，并在 CI 里断言该文件存在且小于某字节数。
5. 未信任项目导致规则缺席：在 config.toml 里用 [projects."<绝对路径>"] trust_level = "trusted" 显式授信，或通过 --cd 切到信任目录。
6. 规则写了仍被无视：先跑诊断 prompt 确认文件真的加载了；再检查是否被 compact 掉；最后把这一条直接写进当前 prompt。
7. 想回滚：AGENTS.md 是纯文本文件，直接 git 管理即可；临时规则用 AGENTS.override.md，删掉文件就恢复常态，不需要改回原文件。

### 版本与生效时间

AGENTS.md 与 project_doc_max_bytes（32 KiB）、project_doc_fallback_filenames、AGENTS.override.md 覆盖机制在 2026-03 之前就已存在且至今稳定；v0.148.0（2026-08-18）加入 /export；v0.150.0 修复「未信任项目不再提供项目级 AGENTS.md 指令」与「权限变更后 deny-read 规则仍生效」（#39837、#40004）。三层结构与行数建议属于社区实践，非官方硬性规定。

### 可自动化程度

中。AGENTS.md 本身是静态文件，不需要自动化；可自动化的是它的**体检**：用 find / wc 脚本在 CI 里断言项目层累计字节数 <32768、不存在空的 AGENTS.override.md、根文件行数 <50；用 `codex --sandbox read-only` 跑诊断 prompt 定期确认加载结果与预期一致。生成环节可用 /init 起稿，但必须人工审。

### 优先级

P0。与契约模板、门禁并列第一梯队：契约里的「派单契约 / 禁止」四条就是靠 AGENTS.md 变成默认行为的，否则每条单都要重复写一遍。

### 对一人公司的适用性

高，尤其契合「成本敏感」这一条。没有团队帮你分摊维护成本，AGENTS.md 就必须极简——它同时是「每次请求都重复付的税」和「唯一能替你值班的同事」。把「派单契约」与「禁止」写进 AGENTS.md，等于把你的 review 习惯固化成默认行为，晚上下的单不用你逐条重述规则。对异步杠杆而言，这是投入产出比最高的静态资产：写一次，每次会话都生效。代价是它必须短——长到你懒得维护，它就会腐化，而腐化的 AGENTS.md 比没有更糟（会给出错误的默认行为）。

### 信息来源

1. OpenAI 官方 Best practices（AGENTS.md 覆盖范围、/init、全局 / 仓库 / 子目录三层、超长时的处理建议）：<https://developers.openai.com/codex/learn/best-practices>
2. AGENTS.md and Skills Mastery（发现顺序、project_doc_max_bytes 32 KiB、静默前缀截断机制与 openai/codex#7138、三层行数建议、override 模式、诊断 prompt）：<https://developertoolkit.ai/en/codex/tips-tricks/agents-md-optimization>
3. Effective Prompting and AGENTS.md Strategies（层级拼接顺序、override 优先级、 Kitchen Sink 等反例、上下文被吃穿的表现）：<https://developertoolkit.ai/en/codex/productivity-patterns/prompt-engineering>
4. Shipyard Codex CLI Cheatsheet（project_doc_max_bytes 默认 32768、加载优先级列表、/init）：<https://qa.shipyard.build/blog/codex-cli-cheat-sheet/>
5. Codex CLI Hooks Reference（自定义指令作用域、project_doc_fallback_filenames、32 KiB 上限、skills 作用域）：<https://symposium.dev/design/agent-details/codex-cli.html>
6. Codex CLI Prompting Guide（/init 生成的是起点不是成品、/status 查生效配置）：<https://sureprompts.com/blog/codex-cli-prompting-guide>
7. Codex 最佳实践完整指南（中文资料，给出「100 行以内、硬上限 300 行、作用域优先级」）：ima.qq.com 整理版，2026-05-15
8. OpenAI Codex changelog（v0.150.0 未信任项目不再提供项目级 AGENTS.md）：<https://help.openai.com/en/articles/11428266-codex-changelog>

### 待核实

- AGENTS.md 各层行数建议（20 / 50 / 30、以及「100 行软建议 / 300 行硬上限」）均为社区与二手资料给出的实践值，OpenAI 官方未给出明确数字 [不确定]
- project_doc_max_bytes 官方默认值在两份资料中均为 32768，但未见官方文档原文确认 [不确定]
- skills 是否真的按需加载（不常驻上下文），官方仅说明存放位置与发现路径，未明确 token 加载策略 [不确定]
- 空的 AGENTS.override.md 是否在所有版本都遮蔽同级 AGENTS.md（该说法仅见于一份二手资料）[不确定]
- 第一非空规则仅适用于全局层、项目层取第一存在文件——这一区分仅一份资料提及，未交叉验证 [不确定]
- 静默截断的具体实现细节来自对 codex-rs/core/src/agents_md.rs 的二手解读，未直接核对源码；不同版本行为可能已变化 [不确定]

## 4. Goal Mode 长任务自治

### 核心做法

Goal Mode 把 Codex 从「每轮等你重新下命令」的应答式工具，变成「给定终点后自己循环推进直到达成/预算耗尽/被阻塞」的持久化执行器。它的本质不是更长的 prompt，而是一条线程级、可审计的完成契约。

【底层机制：Ralph Loop 四层架构】

1. 持久化层：目标作为独立于对话历史的 thread 状态存储，带状态机。所以 /compact 压缩历史、关掉终端、跨天重启都不会丢目标。
2. App-server RPC：thread/goal/{get,set,clear} 三个接口，客户端读写目标状态。
3. 模型工具：get_goal / create_goal / update_goal 三个工具，模型可查询目标、可声明完成，但【不能】自己暂停、清空、篡改状态——这是安全边界，状态转换只能由用户或运行时触发。
4. 运行时延续 + TUI：每一轮空闲时自动注入两段提示词——goals/continuation.md（决定是否继续）与 goals/budget_limit.md（预算软停止）。

【状态机】pursuing（推进中）→ paused（暂停，保留审计上下文）→ achieved（完成审计通过）→ unmet（被外部依赖阻塞）→ budget_limited（预算耗尽，软停止收尾）。

【最被低估的杀手锏：完成审计】continuation.md 强制模型在声明完成前做一次审计：把目标重述为具体交付物 → 构建「提示词→产物」清单，把每条要求映射到证据 → 检查真实证据（文件、命令输出、测试结果、PR 状态）。核心反偷懒规则：测试通过、清单填满、verifier 跑成功只是辅助信号，不是完成证据；模型不得依赖「意图、阶段进度、已耗精力、看似合理的答案」来声明完成。这就是它压住模型 sandbag（早早声称做完然后偷懒）的机制。

【成功条件怎么写】审计能否生效，取决于你的目标能否被映射成清单。强 Goal 必须写清 6 件事：Outcome（结果）、Verification surface（用什么证据验证）、Constraints（什么不能破坏）、Boundaries（允许动哪些文件/工具）、Iteration policy（每轮后如何决定下一步）、Blocked stop condition（无路可走时如何停止并汇报）。写「optimize/improve/清理一下/全部」这类虚词，清单建不起来，审计退化成「测试跑过就算完成」，你就拿到一个声称完成、实际跑偏的结果。

【/side 是它的配套】/side（别名 /btw）是 v0.122.0 引入的临时分叉，把当前对话当只读快照继承，主线 agent 在后台继续跑，你问完按 Esc 无缝回到主线。只允许 /copy、/diff、/mention、/status 四个命令，禁止改文件。适合长任务中途查 API 签名、验证依赖版本、问报错含义，不污染主线上下文，单次成本仅约 500–2000 token。

### 可直接复制的模板命令配置

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【1｜启用（v0.133.0 起默认开启，旧版需手动）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ~/.codex/config.toml

[features]  
goals = true            # v0.128~v0.132 需手动开启；v0.133 起默认  
collaboration_modes = true  # 可选，让 /plan 与 /goal 更好配合

# 改完重启 Codex

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【2｜命令面（TUI 内输入）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
/goal "迁移 Pydantic v1 到 v2，让全部测试通过"   # 创建/替换目标  
goal                                                    # 查看当前目标摘要（状态/内容/耗时/token 用量）  
/goal pause       # 暂停，保留审计上下文  
/goal resume      # 恢复（早期叫 /goal unpause，已改名）  
/goal clear       # 清空，回到单轮模式

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【3｜五段式黄金模板（所有 /goal 都按这个写）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
/goal <一句话目标，避开「全部/所有/彻底/optimize/improve」这类虚词>  
Scope: <只改哪些文件/子系统，其他不要碰>  
Constraints:

- <硬性约束，必须可机械识别，如「不动 project.pbxproj」>
- <如「保持现有公开 API 不变」>  
  Done when:

1. <可验证产物，引用具体文件路径或命令>
2. <如 npm test / pytest -q / tsc --noEmit>  
   Stop if:

- <机械可识别的停止条件，如「需要新增 npm 依赖」>  
  Use a token budget of <N> tokens for this goal.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【4｜完整实例（可直接抄）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
/goal 把 src/data/words.json 词库扩展到 1000 个唯一词条。  
Scope: 只改 src/data/words.json，其他文件不要动。  
Constraints:

- 词条 schema 保持不变（id / word / phonetic / meaning / example）
- 以 word 字段去重，不允许重复词条
- 只用真实常见英语单词，不要生造  
  Done when:

1. words.json 包含恰好 1000 个唯一词条
2. 用 tools/validate.js 跑一遍 schema 校验通过
3. 终端输出最终词条数与文件大小  
   Stop if:

- 需要修改 words.json 以外的任何文件
- 需要新增 npm 依赖
- schema 校验失败超过 3 次  
  Use a token budget of 80000 tokens.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【5｜睡前一单的标准姿势（一人公司异步杠杆）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 先确认在受信任目录、目标可被测试验证

cd ~/work/my-repo  
git checkout -b feat/nightly-refactor   # 隔离分支，独占写权限  
codex  
/goal <用上面的五段式模板写清目标，预算必给>

# 合上电脑去睡。第二天早上：

codex resume --last     # 恢复会话，看收尾报告/PR 状态

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【6｜/side 用法】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
/side What's the signature of tokio::spawn?   # 主线继续跑，侧问不污染上下文

# Esc / Ctrl+C 退出侧线程，回到主线原位置；/side 不能嵌套、不能改文件

### 关键参数

| 参数             | 官方默认值                                                 | 一人公司推荐值                                 | 说明                             |
| -------------- | ----------------------------------------------------- | --------------------------------------- | ------------------------------ |
| features.goals | v0.133.0 起 true；之前 false                              | true（保持默认）                              | 旧版手动开启后需重启                     |
| token budget   | 无默认，需手动设置                                             | ★必须设：小任务 100k–500k，中 500k–2M，大迁移 2M–10M | 不设预算=没有软停止，跑飞只能干看烧 token       |
| budget 性质      | advisory（软停止，注入收尾提示，非硬杀）                              | 理解为「安全网」而非「急刹车」                         | 当前无每 goal 的硬性计费封顶，需靠订阅计划限额兜底   |
| goal 内容长度      | 最长 4000 字符                                            | 超长时把细节放文件，让 goal 指向文件                   | 官方边界                           |
| 状态机            | pursuing / paused / achieved / unmet / budget_limited | —                                       | 模型只能声明 achieved，暂停/清空由用户或运行时触发 |
| /side 命令集      | 仅 /copy /diff /mention /status                        | —                                       | 侧线程只读，不能改文件                    |

必须改的一项：token budget 必给。它是 Goal Mode 里唯一「一等公民」的成本治理机制。

### 常见坑

1. 【最高频】在 Plan 模式下 /goal 不延续。UI 显示「Goal active」，但源码 should_ignore_goal_for_mode 在 Plan 模式直接跳过延续。必须先用 Shift+Tab 退出 Plan 模式，再启动 /goal。
2. 【最烧钱】不设 token budget。Goal 会一直循环到「自我判定完成」或「撞上账号限流」，无软停止。v0.132.0 之前甚至会在 usage limit 处无限空转，之后才修成「在用量上限处停止」。
3. 【最隐蔽】目标写成虚词。「optimize the system」「清理一下」这类无法映射成清单，审计退化成代理信号，你会拿到声称完成、实际跑偏的结果。判据：能否为每条 Done when 指出一个具体文件或命令。
4. /goal clear 会丢弃进度跟踪。想先审查再决定，用 /goal pause，别用 clear。
5. 在多人（或你自己）同时改文件的活跃开发中跑 goal，会产生冲突。Goal 适合隔离分支、独占写权限的场景。
6. 预算耗尽是软停止不是裸停：它会先收尾总结（已完成/剩余/下一步），第二天你打开终端能看到进度报告而不是半成品。但别把它当硬性计费封顶。
7. /compact 若发生在模型调用中途，延续提示词不会重新注入，下一轮 agent 可能丢掉目标和审计要求（Issue #19910）。超长任务尽量让自动 compaction 落在轮次边界。
8. paused 目标在 codex resume 后仍保持 paused（v0.133 起），需要显式 /goal resume 才重启——防止你为别的事恢复会话时意外烧钱。
9. 目标是线程级契约，不是全局记忆。它只跟当前线程的上下文走，换线程就没了。
10. /side 有 token 上限且继承主线上下文，超长项目别无限堆砌侧问。

### 降级与回退路径

1. 目标写糊了/跑偏：/goal clear 清掉，用普通 prompt 收尾已改动部分；别用 /goal 抢救一个边界不清的任务。
2. 预算耗尽（budget_limited）：读收尾报告 → 检查 diff → /goal resume 续跑（配新预算）或 /goal clear 人工接管。
3. 需要更省：先 /plan 讨论方案，确认后退出 Plan 再 /goal 执行，避免 goal 在模糊需求上反复试错烧 token；或配合 OpenSpec 把需求写成规格文档再交给 /goal。
4. 旧版 CLI 无 /goal：升级 codex update / npm i -g @openai/codex@latest；或用 features.goals = true + 重启。
5. 无法监控成本的长时间跑：改用 codex exec 配合 [rollout_budget] 硬性 token 上限，或订阅计划设 spending limit 兜底（goal 无每目标硬封顶）。
6. 长任务失忆：把关键约束在 goal 文本里写死，不依赖对话历史；必要时开新线程重下 /goal。

### 版本与生效时间

v0.122.0（2026-04-20）引入 /side；v0.128.0（2026-04-30）/goal 实验上线；v0.132.0（2026-05-19）修复 goal 在用量上限处停止；v0.133.0（2026-05-21）/goal 转正、默认开启、目标持久化跨重启、paused 语义固化。v0.145.0 继续细化。

### 可自动化程度

中高。TUI 的 /goal 是交互入口，但底层是 App-server 的 thread/goal/{set,get,clear} JSON-RPC，可用 codex exec 或自定义客户端在无人值守 CI 里创建/查询目标。真正的一人公司自动化姿势是：codex exec 里直接下发带预算的 goal 描述，配合 [rollout_budget] 硬性上限与 --json 的 token_count 事件做计量。注意 /goal 本身是 TUI 命令，非交互跑长任务优先用 codex exec 而非挂着一个终端。

### 优先级

P0。它是「睡前下单、早上收 PR」这一异步杠杆的核心引擎，直接决定一人公司能不能把夜间时间变成产能。但前提是配好 budget 与 Done when，否则从杠杆变成烧钱黑洞。

### 对一人公司的适用性

极高，尤其契合「无同事 review、成本敏感、需要异步杠杆」三前提。无同事 review → 完成审计机制替你把「什么叫做完」固化成证据清单，部分替代了人类 reviewer 的验收功能；成本敏感 → token budget 是唯一一等公民的成本开关，且 /side 让临时疑问不污染主线、省掉重发上下文的税；异步杠杆 → 目标跨重启持久化 + 软停止收尾，正是「睡前下单早上看 PR」的形态。唯一代价是它对「写需求」的要求被抬高了：goal 糊，换来的是一整天的糊产出。把 Scope/Constraints/Done when/Stop if/budget 五段写扎实，它就是一人公司最高杠杆的夜间员工。

### 信息来源

1. OpenAI 官方 cookbook《Using Goals in Codex》（goal 定义、6 要素、弱/强 goal 对比、/goal 最长 4000 字符）：<https://developers.openai.com/codex>
2. Codex CLI changelog（v0.128.0 /goal 引入、v0.132.0 停止修复、v0.133.0 转正）：<https://help.openai.com/en/articles/11428266-codex-changelog>
3. Goal Mode 架构/状态机/budget 软停止详解：<https://codex.danielvaughan.com/2026/07/23/codex-cli-goal-mode-long-horizon-autonomous-workflows-ralph-loop-token-budgets>
4. 五段式黄金模板与 Plan 模式坑（should_ignore_goal_for_mode、Issue #19910/#20656）：<https://www.aivi.fyi/llms/codex-goal>
5. /side、/fork、/agent 三原语对比：<https://codex.danielvaughan.com/2026/07/20/three-parallel-work-primitives-codex-cli-agent-fork-side-concurrency>
6. /goal 成功/失败任务形态与 85% 完成率：<https://dev.to/thegdsks/openai-codex-now-finishes-85-of-scoped-tasks-here-is-the-goal-workflow-that-gets-you-there-1dae>

### 待核实

- /goal 设置预算的准确命令语法：一说 /goal --budget 50000（dev.to），一说在目标文本里写「Use a token budget of N tokens」（aivi.fyi），官方文档命令面未明确 budget 参数形式 [不确定]
- budget_limit 是否支持硬性封顶：多方资料均称 token budget 是 advisory（软停止），且「当前无每 goal 的硬性计费封顶」，但 OpenAI 官方未给出明确书面结论 [不确定]
- features.goals 在 v0.133.0 之后是否仍作为可关闭开关保留、关闭后的行为，未在官方文档核实 [不确定]
- 预算建议范围（小 100k–500k / 中 500k–2M / 大 2M–10M tokens）来自二手资料，非官方数值 [不确定]

## 5. config.toml 核心配置

### 核心做法

config.toml（主位置 ~/.codex/config.toml）不是「偏好文件」，而是 Codex 这台代理的运营策略——信任边界。加载优先级：CLI flag / -c key=value 覆盖 > 指定 profile > 项目 .codex/config.toml（需信任）> 全局 ~/.codex/config.toml > 系统 requirements.toml 强制层。五组核心项如下。

【模型路由】用 model 指定默认模型，用 [profiles.NAME] 做「任务分层路由」：交互用贵模型，CI/后台用便宜模型，用 codex --profile ci 切换。自定义 agent 可在 ~/.codex/agents/*.toml 里按角色单独配 model（explorer 用便宜模型、worker 用贵模型）。

【推理强度】model_reasoning_effort（minimal/low/medium/high/xhigh）调内部思维链深度，是输出 token 的主要开关之一。省钱铁律：不要什么都 high——重命名、格式化用 low/medium，架构设计、复杂重构才用 high。xhigh 烧 token，留给最难的 plan 问题。

【审批模式】approval_policy 决定「何时停下来问你」，与沙箱是正交的两件事。untrusted 几乎每步都问；on-request 只在需要越权/越沙箱时问；never 全自动（慎用，别配 danger-full-access）。granular 表可逐类开关：让 sandbox 升级可问、但自动拒绝 skill 脚本审批。

【沙箱模式】sandbox_mode 决定「技术上能碰什么」，由 OS 层强制（macOS Seatbelt / Linux bwrap+seccomp / Windows）。read-only 只读；workspace-write 可写 cwd+tmp、默认断网；danger-full-access 放开一切。默认值不是常量：信任过的目录默认 workspace-write，未信任的默认 read-only。

【agents 并发】[agents] 只控「全局上限」：max_threads 并发线程、max_depth 嵌套深度、job_max_runtime_seconds 单 worker 超时。角色行为不在这一层，而在 agent 文件里。

【关键事实：--full-auto 已被移除】v0.147.0 起，codex exec --full-auto 被正式移除，正确写法是 --sandbox workspace-write。在 codex exec 上它退化为隐藏兼容陷阱，只打印「warning: --full-auto is deprecated; use --sandbox workspace-write instead」。还在教程里见到 --full-auto 的都是过时资料。

### 可直接复制的模板命令配置

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【1｜一人公司推荐 config.toml（可直接抄）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ~/.codex/config.toml

model = "gpt-5.3-codex"            # 日常编码默认  
model_reasoning_effort = "medium"   # 常规任务 medium，省钱  
approval_policy = "on-request"      # 越界才问，日常少打断  
sandbox_mode = "workspace-write"    # 可写工作区，默认断网  
web_search = "cached"               # 用缓存索引，降低注入风险

[agents]  
max_threads = 6        # 官方默认，够用  
max_depth = 1          # 官方默认，别调大

# 需要装依赖/联网时才临时开网络，别常开

[sandbox_workspace_write]  
network_access = false

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【2｜CI/后台省钱 profile（睡前任务用它）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ~/.codex/ci.config.toml

model = "gpt-5.4-mini"  
model_reasoning_effort = "low"  
approval_policy = "never"  
sandbox_mode = "workspace-write"  
service_tier = "flex"

# 调用：codex --profile ci "任务"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【3｜非交互执行（无人值守 CI 的正确姿势）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# codex exec 默认 approval=never，且只读；要写必须显式给沙箱

codex exec --sandbox workspace-write "跑测试并修复失败"

# 旧写法（已坏，别用）：

# codex exec --full-auto "..."

# JSON 输出做计量：

codex exec --json --sandbox workspace-write "总结仓库结构" | jq

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【4｜granular 审批（只对沙箱升级提问，自动拒绝技能脚本）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
approval_policy = { granular = {  
sandbox_approval = true,     # 越沙箱的请求可以问  
rules = true,                # execpolicy prompt 规则生效  
mcp_elicitations = false,    # 静音 MCP 副作用提示  
request_permissions = false, # 自动拒绝权限申请  
skill_approval = false       # 自动拒绝技能脚本审批  
} }

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【5｜自定义 agent 分档（explorer 用便宜、worker 用贵）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ~/.codex/agents/explorer.toml

name = "explorer"  
description = "只读代码库探索，收集证据不提案"  
developer_instructions = "保持探索态，追踪真实执行路径，引用文件与符号，不要提修复建议。"  
model = "gpt-5.4-mini"  
model_reasoning_effort = "low"  
sandbox_mode = "read-only"

### 关键参数

| 参数                                     | 官方默认值                                   | 一人公司推荐值                                      | 说明                                                  |
| -------------------------------------- | --------------------------------------- | -------------------------------------------- | --------------------------------------------------- |
| model                                  | 依发行/登录态（gpt-5.3-codex 为 coding 优化默认）    | gpt-5.3-codex（日常）；gpt-5.5（复杂任务，需 ChatGPT 登录） | API key 访问新模型有延迟                                    |
| model_reasoning_effort                 | 官方未明文（一说 high）                          | ★medium（常规）、low（批量/CI）、high（架构/重构）           | 值：minimal/low/medium/high/xhigh                     |
| approval_policy                        | untrusted                               | ★on-request                                  | 可选：untrusted / on-request / never / granular 表      |
| sandbox_mode                           | read-only（未信任目录）；workspace-write（已信任目录） | ★workspace-write                             | 可选：read-only / workspace-write / danger-full-access |
| --full-auto                            | 已移除（v0.147.0）                           | 改用 --sandbox workspace-write                 | ★必须改，旧脚本会直接失败                                       |
| sandbox_workspace_write.network_access | false                                   | 保持 false，装依赖时临时开                             | 忘了开= npm/pip install 卡住                             |
| approvals_reviewer                     | user                                    | CI 时 auto_review（配合 --approve-for-me）        | auto_review 走自动审查，不打断                               |
| agents.max_threads                     | 6                                       | 6（保持默认）                                      | 并发线程上限                                              |
| agents.max_depth                       | 1                                       | 1（别调大）                                       | 调大会反复 fan-out 烧 token                               |
| agents.job_max_runtime_seconds         | 1800（spawn_agents_on_csv 回退值）           | 1800                                         | 单 worker 超时                                         |

必须改的三项：① 把残留的 --full-auto 换成 --sandbox workspace-write；② approval_policy 从 untrusted 调到 on-request（否则每步都问，一人公司会被打断到崩溃）；③ 按任务分层路由模型（profile），不要统一 high。

### 常见坑

1. 【版本陷阱】--full-auto 在 v0.147.0 被移除。CI 脚本里残留会导致直接失败；codex exec 上它退化为打印 deprecation warning 的隐藏兼容陷阱。搜一遍 CI 配置替换成 --sandbox workspace-write。
2. 【默认值不是常量】sandbox_mode 默认取决于目录是否被信任：信任过 → workspace-write，没信任 → read-only。同一 repo 的两个 clone 在两条路径上行为可能不同。脚本里永远显式传 --sandbox。
3. 【codex exec 没有 -a】--ask-for-approval 只存在于交互 codex 命令，codex exec 硬编码 approval=never（headless 无人类，提示会挂起）。别在 exec 里指望审批。
4. 【network_access=false 忘开】workspace-write 默认断网，pip/npm install 神秘挂起。需要联网的任务显式 network_access = true 或开 domain 白名单。
5. 【never + danger-full-access 组合】等于裸奔，只有一次性容器/受控 runner 才允许。
6. 【max_depth 调大】官方明示会把宽泛的委派指令变成反复 fan-out，token、延迟、本地资源一起涨。保持 1。
7. 【把 permissions profiles 和 sandbox_mode 混用】两者是二选一的模型，别叠着用。选一个体系，用 /status 看生效结果。
8. 【xhigh 滥用】xhigh 烧输出 token，绝大多数常规任务 medium/low 无感知差异。
9. 【项目 config 未生效】项目 .codex/config.toml 需要该目录被信任才加载；被忽略时先确认 trust_level = "trusted" 或 --cd 到信任目录。
10. 【ChatGPT 登录态 vs API key】gpt-5.5 等新模型 ChatGPT 登录才有，API key 有延迟访问。CI 里用 API key 可能拿不到最新模型。

### 降级与回退路径

1. --full-auto 失效：替换为 --sandbox workspace-write；需要「编辑+跑命令+联网」就用 danger-full-access 或 --yolo（仅一次性环境）。
2. 模型弃用/登录态差异：/model 或 -m 切可用模型；API key 拿不到新模型时退回 gpt-5.4 系；自定义 provider 用 model_provider 指到 DeepSeek/Kimi/GLM 等。
3. 审批太吵：untrusted → on-request，或用 granular 表只留关键类别交互、其余自动拒绝。
4. 无人值守想自动放行：codex exec 配 --sandbox workspace-write + 显式 approval_policy = "never"，或用 v0.147.0 的 --approve-for-me 走自动审查。
5. 配置看起来没生效：跑 /status 看生效值，再跑 /debug-config 看各层优先级与 allowed_approval_policies / allowed_sandbox_modes。
6. 越权被拒导致任务卡住：给最小权限集（--add-dir 加额外可写目录、domain 白名单放行单个域名），而不是一刀切 danger-full-access。

### 版本与生效时间

--full-auto 于 v0.147.0（2026-08-07）移除；--approve-for-me 同版引入。approval_policy granular 自 v0.126；permissions profiles 与 profiles 分档自 2026 年初演进。agents 显式可配自 v0.128.0。模型与 reasoning 值随周更滚动，需以官方 changelog 为准。

### 可自动化程度

高。codex exec 是 CI/定时任务的一等入口，默认只读+never 审批，配 --sandbox workspace-write 即可无人值守改代码，--json 输出 token_count 事件做成本计量。整套「模型路由 + 推理强度 + 审批 + 沙箱 + agents 并发」都能用 config.toml/profile 固化，睡前用 codex exec --profile ci 下单、早上收结果，是完全可自动化的闭环。

### 优先级

P0。它是所有其他能力的地基——Goal Mode 的预算、Hooks 的阻断、权限的白名单，最终都落到这份配置上。一人公司没有团队分摊试错，先把这份配置跑对，其余才谈得上杠杆。

### 对一人公司的适用性

极高，是「成本敏感」的直接解药。无同事 review → on-request + workspace-write 给你「日常少打断、越界才问」的默认；成本敏感 → profile 分层路由（交互贵模型、CI 便宜模型）+ reasoning_effort 下调是最大的省钱杠杆；异步杠杆 → codex exec + 显式沙箱是睡前下单的唯一正确姿势。唯一要警惕的是：一人公司容易图省事滑向 never + danger-full-access 的裸奔配置，而安全边界恰恰是唯一没有同事帮你兜底的地方。守住 workspace-write + on-request + 断网默认这三条底线。

### 信息来源

1. OpenAI 官方 sandbox 与 approvals 文档（--full-auto 弃用、approval_policy/sandbox_mode 取值、--ask-for-approval、--approve-for-me、granular）：<https://developers.openai.com/codex/sandbox>
2. OpenAI 官方 Advanced Configuration（model_reasoning_effort、approvals_reviewer、granular 表）：<https://developers.openai.com/codex/config-advanced>
3. OpenAI 官方 Subagents 文档（agents.max_threads=6 / max_depth=1 / job_max_runtime_seconds=1800、内置 default/worker/explorer）：<https://developers.openai.com/codex/subagents>
4. v0.147.0 变更（--full-auto 移除、--approve-for-me 引入）：<https://codex.danielvaughan.com/2026/08/10/codex-cli-v0147-portable-agent-plugins-multi-catalog-federation-approve-for-me-conversation-sections>
5. 沙箱默认值推导逻辑（derive_permission_profile、exec 硬编码 approval=never）：<https://backgrind.com/blog/codex-cli-sandbox-modes>
6. config 概览与 profile/模型表：<https://shipyard.build/blog/codex-cli-cheat-sheet/>

### 待核实

- approval_policy 的合法取值全集：官方为 untrusted/on-request/never/granular，但二手资料出现 on-failure、reject 等历史/笔误值，是否已彻底移除未核实 [不确定]
- model 的「官方默认值」随登录态/发行渠道变化，gpt-5.3-codex 是否仍是当前统一默认未在官方文档核实 [不确定]
- model_auto_compact_token_limit（64000）与 model_context_window（272000）等数值仅见于单一二手来源，未在官方配置参考确认 [不确定]
- model_reasoning_effort 官方默认值：一说 high（lobehub/CLI 默认），一说 medium（部分中文资料），官方文档未明文，需实测确认 [不确定]
- service_tier = flex 的可用范围与计费影响来自二手资料，官方文档未确认 [不确定]

## 6. 权限新体系

### 核心做法

Codex 的管控从「粗粒度的 sandbox_mode + approval_policy 二维模型」演进到「细粒度的 permission profiles + execpolicy 规则」双轨。它们的定位不同：

【permission profiles】—— 管「能碰哪些文件和哪些网络」，OS 层强制（macOS Seatbelt / Linux bwrap+seccomp）。一个命名 profile 把 filesystem 规则（哪些路径可读/可写/拒绝）+ network 规则（哪些域名/套接字可达）打包成一体，用 default_permissions 或 --profile 激活。三个内置 profile：:read-only（全禁改）、:workspace（工作区内可写）、:danger-full-access（全放开）。自定义 profile 用 extends = ":workspace" 继承内置基座，再逐条覆盖。

【.rules / execpolicy】—— 管「哪些命令能自动跑、哪些要问、哪些禁止」，用 Starlark 写 prefix_rule，按命令前缀做决策，decision 三档 allow / prompt / forbidden，严格度 forbidden > prompt > allow（任一规则匹配 forbidden 即阻断）。这比 approval_policy 更细：approval 是全局「何时问」，execpolicy 是「逐命令白名单/黑名单」。

【关系】profiles 与旧 sandbox_mode 是二选一模型（官方明示：用一套，别叠着用）；execpolicy 与 approval_policy 正交——命令先过 execpolicy，匹配到 prompt 的再按 approval_policy 决定是否弹给用户（或 auto_review）。requirements.toml 是最上层强制：只能 prompt/forbidden，不能 allow，用户配置只能收紧不能放宽。

【特殊 token】filesystem 规则里 :workspace_roots（工作区根）、:minimal（常用工具最小可读集）、:root、:tmpdir、:slash_tmp 是占位符，让规则跟随环境而非写死绝对路径。

【域白名单语法】domains 表里 "example.com" 精确主机、"\*.example.com" 仅子域、"\*\*.example.com" 含 apex、deny 覆盖 allow；本地/私有网络默认阻断（防 DNS rebinding），要访问须显式 allowlist 精确主机或设 allow_local_binding = true。

### 可直接复制的模板命令配置

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【1｜最小可写、默认断网（一人公司日常推荐）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
default_permissions = "project-edit"  
[permissions.project-edit.filesystem]  
":minimal" = "read"  
[permissions.project-edit.filesystem.":workspace_roots"]  
"." = "write"  
[permissions.project-edit.network]  
enabled = false

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【2｜域白名单：只放行需要的域名（装依赖/调 API）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
default_permissions = "workspace-net"  
[features]  
network_proxy = true  
[permissions.workspace-net.filesystem]  
":minimal" = "read"  
[permissions.workspace-net.filesystem.":workspace_roots"]  
"." = "write"  
[permissions.workspace-net.network]  
enabled = true  
mode = "limited"          # limited=白名单之外全拒；full=黑名单之外全放  
[permissions.workspace-net.network.domains]  
"api.openai.com" = "allow"  
"registry.npmjs.org" = "allow"  
"api.github.com" = "allow"  
"ads.example.com" = "deny"   # deny 覆盖 allow

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【3｜继承内置基座 + 保护敏感文件】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
default_permissions = "workspace-only"  
[permissions.workspace-only]  
extends = ":workspace"            # 继承内置工作区基座（.git/.codex 自动只读）  
[permissions.workspace-only.filesystem]  
":root" = "deny"                  # 默认拒绝读整个盘  
":minimal" = "read"               # 放行常用工具最小集  
"**/*.env" = "deny"               # 拒绝所有环境文件（glob）  
"**/*.pem" = "deny"  
":tmpdir" = "deny"  
":slash_tmp" = "deny"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【4｜execpolicy .rules（逐命令管控，可直接抄）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ~/.codex/rules/default.rules

# 只读 git 命令：自动放行

prefix_rule( pattern = ["git", ["status", "diff", "log", "show"]], decision = "allow", justification = "只读 git 操作" )

# git 写入：需确认

prefix_rule( pattern = ["git", ["add", "commit", "merge", "rebase"]], decision = "prompt", justification = "git 写入需审查" )

# 危险操作：禁止

prefix_rule( pattern = ["git", ["push", "force-push"]], decision = "forbidden", justification = "禁止自动推送" )  
prefix_rule( pattern = ["rm", "-rf"], decision = "forbidden", justification = "禁止递归强删" )  
prefix_rule( pattern = [["curl", "wget"]], decision = "forbidden", justification = "网络访问走沙箱策略" )

# 常规开发命令：放行

prefix_rule( pattern = [["npm", "pnpm", "yarn"], ["install", "test", "build"]], decision = "allow", justification = "标准包管理操作" )

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【5｜验证规则是否正确匹配】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
codex execpolicy check --pretty --rules ~/.codex/rules/default.rules -- git push

# 输出 JSON：matchedRules + decision（forbidden/prompt/allow）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【6｜列出/查看 profile】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
codex permissions list                    # 列出所有可用 profile  
codex permissions show secure-base        # 看合并后的定义  
codex permissions show secure-base --trace # 标注每条规则来自哪个配置文件哪一行

### 关键参数

| 参数                  | 官方默认值                                         | 一人公司推荐值                        | 说明                              |
| ------------------- | --------------------------------------------- | ------------------------------ | ------------------------------- |
| 内置 profiles         | :read-only / :workspace / :danger-full-access | :workspace（日常）                 | 用 extends 继承                    |
| filesystem 访问级别     | 无（按 profile）                                  | workspace 可写、.env/.pem 全局 deny | 优先级 deny > write > read，更具体路径优先 |
| network.mode        | 未启用时断网                                        | limited（白名单模式）                 | limited=白名单外全拒；full=黑名单外全放      |
| network 本地/私有       | 默认阻断                                          | 保持阻断                           | 防 DNS rebinding；需访问显式 allowlist |
| execpolicy decision | 无（未配置即回落 approval_policy）                     | 常用命令 allow，危险 forbidden        | forbidden > prompt > allow      |
| requirements.toml   | 无（企业层）                                        | 一人公司可跳过                        | 只能 prompt/forbidden，不能 allow    |
| 与 sandbox_mode 关系   | 二选一                                           | 选 profiles 体系，别混用              | 官方明示用一套                         |

必须改的一项：把敏感文件（.env/.pem/.ssh/\*\*）写成全局 deny 规则。这是无同事 review 时唯一替你兜住「agent 误读密钥文件」的硬闸。

### 常见坑

1. 【最大坑】把 permission profiles 和旧 sandbox_mode 混用。官方明示「用一套或另一套，别叠着用」。两套都写会让人误以为「双层更安全」，实际可能冲突或部分被忽略。
2. 【deny 位置错】把 "\*\*/\*.env" = "deny" 写在 profile 顶层，会变成「全局 deny 所有 .env」——通常是对的，但要意识到它不受 :workspace_roots 作用域限制；想只作用域工作区，须包在 [permissions.NAME.filesystem.":workspace_roots"] 子表里。
3. 【忘记 mode = limited】开了 enabled = true 却不写 domains 白名单，网络行为取决于默认（full 或空），容易变成「本想白名单、实际全放」。
4. 【本地服务访问被静默阻断】默认阻断 localhost/私有 IP，调试本地 API 时连接神秘失败，得显式 allowlist "localhost" 或设 allow_local_binding。
5. 【execpolicy 匹配不上】["npm", "test"] 不匹配 npm run test（参数位置不同）。用 codex execpolicy check 验证，用 match/not_match 做载入期断言。
6. 【规则文件语法错整份不加载】Starlark 语法错误或 match/not_match 断言失败，导致整个 .rules 文件在启动时被拒绝，所有命令回落 approval_policy。看启动输出。
7. 【smart approvals 生成的规则太宽】默认开启时会观察你的审批习惯自动建议 prefix_rule，接受太宽的规则等于留后门。定期 codex execpolicy check 审查 ~/.codex/rules/default.rules。
8. 【deny 覆盖 allow 但被误解】domains 里 deny 永远赢，但更具体路径的 filesystem 规则才会赢更宽泛的——方向别记反。
9. 【项目 .rules 只在信任目录加载】.codex/rules/team.rules 需要项目 .codex 层被信任，否则整份不生效。

### 降级与回退路径

1. 任务被权限卡死：先 /status 看生效 profile 与 writable roots；用 --add-dir 加额外可写目录、domain 白名单放行单个域名，给最小权限集，别一刀切 :danger-full-access。
2. 想从旧 sandbox 体系迁移：官方建议选 profiles 体系，用内置 :workspace 起步，逐条加 filesystem/network 覆盖。
3. execpolicy 规则误伤：codex execpolicy check --pretty 定位是那条规则命中；改 justification 或加 not_match 收窄；紧急时删该条或 /permissions 临时放宽。
4. 规则被 requirements.toml 卡住（企业场景）：确认优先级 cloud > MDM > system requirements.toml > project rules > user rules，用户层只能更紧。
5. 网络行为异常：network_proxy = false 关代理观察；或 mode 切 full 临时排查，再回 limited 白名单。
6. 回滚：profiles 和 .rules 都是纯文本，git 管理即可；删掉自定义 profile 的 default_permissions 就回到内置默认。

### 版本与生效时间

permission profiles 自 2026 年初随 split permissions 引入；v0.133.0（2026-05-21）加入 profile 继承（config-layer 合并）、codex permissions list/show --trace 与 requirements.toml 集成；execpolicy 前缀规则自 v0.126 起成熟，smart approvals 同区间引入。

### 可自动化程度

高。execpolicy 用 codex execpolicy check 可在 CI 里做命令级断言；permission profiles 通过 codex permissions show --trace 可追溯每条规则来源，适合无人值守环境做配置漂移检测。配合 codex exec + 显式 profile，整套权限边界可固化、可版本化、可在 CI 里验证。

### 优先级

P1。它是安全兜底而非产能杠杆——没有同事 review，它就是唯一防止 agent 误读密钥、误删文件、乱联网的硬闸。优先级略低于 P0 的「把活干对」，但必须紧随其后落地，尤其敏感文件 deny 规则。

### 对一人公司的适用性

高，且是「无同事 review」的直接补偿。没有第二个人在 PR 里拦住你，permission profiles 的文件系统 deny + execpolicy 的 forbidden 就是那个「不在场的 reviewer」：它不靠 prompt 祈求 agent 守规矩，而是 OS 层和规则引擎硬拦。成本敏感 → 白名单模式（limited）默认拒一切未授权域名，避免 agent 乱联网烧钱或注入；异步杠杆 → 睡前用带 profile 的 codex exec 下单，权限边界在无人值守时依然成立。建议一人公司从「:workspace + .env/.pem 全局 deny + 危险命令 forbidden」这套最小组合起步，再按需加域名白名单。

### 信息来源

1. OpenAI 官方 Permissions 文档（profile、filesystem/network/domains 语法、:workspace_roots 等特殊 token、local/private 默认阻断）：<https://developers.openai.com/codex/permissions>
2. OpenAI 官方 sandbox/approvals 文档（profiles 与旧 sandbox 二选一、审批模式）：<https://developers.openai.com/codex/sandbox>
3. OpenAI 官方 Advanced Configuration（granular approval_policy 与 permissions 关系）：<https://developers.openai.com/codex/config-advanced>
4. Execution Policy Rules（prefix_rule 语法、forbidden>prompt>allow、host_executable、match/not_match、smart approvals、requirements.toml 优先级）：<https://codex.danielvaughan.com/2026/04/16/codex-cli-execution-policy-rules-starlark-command-governance>
5. Permission Profile Inheritance v0.133（extends 继承、list/show --trace）：<https://codex.danielvaughan.com/2026/05/22/codex-cli-permission-profile-inheritance-composable-security-policies-v0133>
6. Split Permissions（network.mode limited/full、SOCKS5、shell_environment_policy）：<https://codex.danielvaughan.com/2026/04/20/codex-cli-split-permissions-fine-grained-filesystem-network-policies>

### 待核实

- deny glob（如 \*\*/\*.env）在超大仓库的 glob_scan_max_depth 默认上限值，仅见于单一二手来源 [不确定]
- execpolicy 前缀规则的引入版本（v0.126 前后）与 smart approvals 默认开关的精确版本边界未逐一核对 [不确定]
- network.mode 缺省时（enabled=true 但未写 mode/domains）的确切默认行为，官方未明文 [不确定]
- permission profiles 与旧 sandbox_mode/approval_policy 的精确兼容与冲突行为（官方只提示「二选一」但未列全冲突矩阵），与 fields.yaml 既有不确定项一致 [不确定]

## 7. Hooks 强制验证

### 核心做法

原理：Hooks 是 Codex 的「控制平面」，不是「数据平面」——它在 agent 循环的精确点位注入确定性脚本，以 OS 级进程执行、保证送达，不依赖模型在上下文压力下是否还记得 AGENTS.md 里的自然语言指令。一句话：把「跑测试再交回」从软约定（模型可能忽略）升级成硬执行（exit 2 阻断，模型无法跳过）。

四类钩子的分工：

1. SessionStart——会话启动/恢复/清空/压缩时触发（matcher 过滤 startup|resume|clear|compact）。stdout 会被注入为 developer context，是做「动态上下文注入」的主机制（如注入当天项目状态、注意事项）。
2. PreToolUse——工具执行前拦截，是唯一「真正阻断」的点。exit 2 阻止该次工具调用（stderr 作为阻止原因）。用于拦截危险命令（rm -rf、force push）、扫描 API key 泄露。
3. PostToolUse——工具执行后触发。exit 2 会把 stderr 作为反馈「替换工具结果」、迫使模型从 hook 消息处重新考虑（注意：不能撤销已发生的副作用）。用于跑格式化、lint、对刚改的文件做校验。
4. Stop——模型认为一轮完成、准备交回时触发。exit 2 强制模型「继续工作」而不是停下，stderr 会成为自动生成的继续提示词。这是「不跑完测试不许交回」的核心落地点。

操作步骤：① 写 hook 脚本（bash/python 皆可，约定 exit code：0=放行、2=阻断）；② 写入 ~/.codex/hooks.json（或项目 .codex/hooks.json）；③ 进 TUI 用 /hooks 审核并「信任」该 hook（信任记录绑定脚本 hash）；④ 跑一个真实任务验证阻断行为。

exit code 完整语义（关键）：0=成功继续；2=阻断/停止（stderr 写原因）；其他（如 1）=只记录错误、不阻断。也就是说，用 exit 1 想阻断是无效的，必须 exit 2。PreToolUse 用 exit 2 直接拦下命令；PostToolUse 用 exit 2 注入反馈；Stop/SubagentStop 用 exit 2 强制继续；UserPromptSubmit 用 exit 2 阻止提示词。也可以不用 exit code、改用 stdout 输出 JSON（如 {"permissionDecision":"deny",...} 或 {"decision":"block",...}）达到同样效果。

### 可直接复制的模板命令配置

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【1｜一人公司最小可用 hooks.json（四类钩子全套）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 保存为 ~/.codex/hooks.json（全局）或 /.codex/hooks.json（项目级）

{  
"hooks": {  
"SessionStart": [  
{  
"matcher": "startup|resume",  
"hooks": [  
{  
"type": "command",  
"command": "cat ~/.codex/context/daily-brief.txt",  
"statusMessage": "注入项目上下文"  
}  
]  
}  
],  
"PreToolUse": [  
{  
"matcher": "Bash",  
"hooks": [  
{  
"type": "command",  
"command": "python3 ~/.codex/hooks/guard-dangerous.py",  
"statusMessage": "检查危险命令",  
"timeout": 10  
}  
]  
}  
],  
"PostToolUse": [  
{  
"matcher": "Edit|Write",  
"hooks": [  
{  
"type": "command",  
"command": "python3 ~/.codex/hooks/post-edit-check.py",  
"statusMessage": "校验刚改的文件",  
"timeout": 60  
}  
]  
}  
],  
"Stop": [  
{  
"hooks": [  
{  
"type": "command",  
"command": "bash ~/.codex/hooks/run-tests-or-block.sh",  
"statusMessage": "跑测试，失败则不许交回",  
"timeout": 300  
}  
]  
}  
]  
}  
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【2｜Stop 钩子：跑测试，失败 exit 2 强制继续（核心脚本）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
#!/bin/bash

# ~/.codex/hooks/run-tests-or-block.sh

# 语义：exit 0 = 测试通过，允许交回；exit 2 = 测试失败，强制模型继续改

OUTPUT=$(npm test 2>&1)        # 按项目换成 make test / cargo test / pytest 等
CODE=$?  
if [ $CODE -ne 0 ]; then
  echo "测试未通过，继续修复，不要交回。最近 30 行输出：" >&2
  echo "$OUTPUT" | tail -30 >&2  
exit 2  
fi  
exit 0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【3｜PreToolUse 钩子：拦截危险命令】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
#!/usr/bin/env python3

# ~/.codex/hooks/guard-dangerous.py

import json, sys  
BLOCK = ["rm -rf /", "git push --force", "git reset --hard", ":(){ :|:& };:"]  
try:  
evt = json.load(sys.stdin)  
cmd = evt.get("tool_input", {}).get("command", "")  
except Exception:  
sys.exit(0)  
for b in BLOCK:  
if b in cmd:  
print(f"检测到危险命令：{b}，已阻断。", file=sys.stderr)  
sys.exit(2)  
sys.exit(0)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【4｜config.toml 内联写法（等价于上面 hooks.json）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ~/.codex/config.toml

[[hooks.Stop]]  
[[hooks.Stop.hooks]]  
type = "command"  
command = "bash ~/.codex/hooks/run-tests-or-block.sh"  
statusMessage = "跑测试，失败则不许交回"  
timeout = 300

[[hooks.PreToolUse]]  
matcher = "Bash"  
[[hooks.PreToolUse.hooks]]  
type = "command"  
command = "python3 ~/.codex/hooks/guard-dangerous.py"  
timeout = 10

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【5｜v0.148.0 新能力：异步钩子（async）与调用 MCP 工具】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 异步钩子：后台跑，不阻塞 agent 循环。注意：async 钩子不能阻断/放行/改写，

# 只能当观察者（审计日志、埋点、通知）。门禁类钩子必须保持同步（不写 async）。

{  
"hooks": {  
"PostToolUse": [  
{  
"matcher": "Bash",  
"hooks": [  
{  
"type": "command",  
"command": "python3 ~/.codex/hooks/audit-logger.py",  
"async": true  
}  
]  
}  
]  
}  
}

# 调用 MCP 工具：type 必须为 mcp_tool，server/tool 必填，input 用 ${字段} 展开事件数据

{  
"hooks": {  
"PostToolUse": [  
{  
"matcher": "Write|Edit",  
"hooks": [  
{  
"type": "mcp_tool",  
"server": "scanner",  
"tool": "scan_patch",  
"input": { "patch": "${tool_input.command}" },  
"timeout": 30,  
"statusMessage": "扫描改动"  
}  
]  
}  
]  
}  
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【6｜审核与信任钩子】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 进 TUI 后执行，审核新增/变更的 hook 并信任（信任绑定当前 hash）：

/hooks

# 一次性自动化（已在外部审核过 hook 来源）免信任运行：

codex --dangerously-bypass-hook-trust "跑测试并修复"

### 关键参数

| 参数           | 官方默认值                                                                                         | 一人公司推荐值                                  | 说明                                  |
| ------------ | --------------------------------------------------------------------------------------------- | ---------------------------------------- | ----------------------------------- |
| exit code 语义 | 0=放行 / 2=阻断 / 其他=仅记日志                                                                         | 门禁一律 exit 2                              | ★必须用 2，写 exit 1 不会阻断                |
| timeout      | 600 秒（SessionEnd 为 1 秒）                                                                       | Stop 钩子 300、PreToolUse 10、其他 60          | 单位秒，超时会怎样需实测                        |
| async        | false                                                                                         | 审计/日志/通知类 true，门禁类保持 false               | ★v0.148.0 起支持；async 钩子不能阻断，最多 8 并发  |
| matcher      | 正则，* 或省略=全匹配                                                                                  | 按需：Bash / Edit|Write / mcp\_\_xxx        | Stop 和 UserPromptSubmit 不支持 matcher |
| type         | command                                                                                       | command（门禁）；mcp_tool（接外部服务）              | ★v0.148.0 起支持 mcp_tool              |
| 配置位置         | ~~/.codex/hooks.json、~~/.codex/config.toml、<repo>/.codex/hooks.json、<repo>/.codex/config.toml | 项目级放 <repo>/.codex/hooks.json（可 git 版本化） | 项目级需该目录被信任才加载                       |
| 信任机制         | 非托管 command hook 需 /hooks 审核信任（绑定 hash）                                                       | 首次 /hooks 信任一次，之后变更会重新标记待审               | 变更加入新 hook 后会被跳过直到重新信任              |
| 启用开关         | 默认启用                                                                                          | 保持启用                                     | [features] hooks = false 可整体关闭      |

必须改的两项：① 门禁类钩子（Stop 跑测试、PreToolUse 拦危险命令）绝不要加 async:true，否则失去阻断能力；② 阻断必须用 exit 2（或输出 permissionDecision/decision:block JSON），不要误用 exit 1。

### 常见坑

1. 【exit 1 不阻断】只有 exit 2 是阻断信号，exit 1 和其他非零码只被记日志、放行。很多人写脚本习惯 return 1 表示失败，结果门禁形同虚设。
2. 【只有 PreToolUse 能真正拦下动作】PostToolUse 的 exit 2 只是「注入反馈、替换工具结果」，不能撤销已发生的副作用（文件已经改了、命令已经跑了）。要阻止动作发生，必须用 PreToolUse。
3. 【Stop 钩子不跑测试就放行】Stop 事件不支持 matcher（配置了会被忽略），所以它默认对「所有轮次」生效。一定要在 Stop 脚本里自己判断「本轮是否改了代码」，否则连纯聊天轮次都会跑一遍测试、白白烧时间。
4. 【把门禁写成 async】v0.148.0 的 async 钩子是 fire-and-forget，明确不能 block/approve/deny/rewrite。把「跑测试」钩子加 async:true 会让它变成纯观察者，阻断彻底失效。
5. 【未信任的项目 hooks 不加载】项目 .codex/hooks.json 只有在项目 .codex/ 目录被信任时才加载；换机器/换 clone 后需要重新信任，否则钩子静默失效，你以为有门禁其实没有。
6. 【hook 脚本路径用相对路径】Codex 可能从子目录启动，.codex/hooks/... 这类相对路径会失效。仓库级钩子优先用 $(git rev-parse --show-toplevel)/.codex/hooks/... 解析绝对路径。
7. 【脚本变更后 hash 失效】信任记录绑定脚本内容 hash，改脚本后会被重新标记为「待审核」，在被信任前直接跳过。改完 hook 记得回 /hooks 重新信任。
8. 【版本差异】v0.148.0 之前 async/mcp_tool 会被解析但跳过（async:true 直接忽略）；部分旧资料还用 {"decision":"reject"} 或 {"handler":...} 结构，与官方三层结构（事件→matcher 组→hooks 数组）不一致，照抄会踩坑。

### 降级与回退路径

1. 钩子误报/死循环阻断：进 TUI 用 /hooks 禁用单个非托管 hook；或整体 [features] hooks = false 临时关闭；定位问题后重新信任。
2. 一次性自动化想免信任运行：加 --dangerously-bypass-hook-trust（前提是 hook 来源已在 Codex 外部审核过）。
3. PostToolUse 阻断不够、需要「事前」拦截：把校验前移到 PreToolUse（对 Bash 命令做静态检查），或在 PreToolUse 用 permissionDecision:deny 拦下。
4. 想撤销副作用：Hooks 无法回滚已发生的写操作，配合 git 快照/checkpoint（Stop 钩子里 git tag）实现「验证通过才打 checkpoint」的回退能力。
5. 需要跨机器一致的门禁：把 hooks 放到项目 .codex/hooks.json 里随 git 版本化，配合 requirements.toml 托管（企业场景 allow_managed_hooks_only）。

### 版本与生效时间

Hooks 于 2026-05-14 正式 GA（v0.133 前后），GA 后扩展为 10 个事件 + hash 信任模型 + /hooks 浏览器。v0.148.0（2026-08-18）新增「异步命令执行 + 调用 MCP 工具」两项能力。

### 可自动化程度

高。Hooks 在 codex exec 非交互模式下同样生效（headless 无人类也能拦截/继续），配合 --json 输出可做 CI 门禁；用 --dangerously-bypass-hook-trust 覆盖一次性无人值守场景。是少数「交互与无人值守一致」的控制面。

### 优先级

P0。一人公司没有同事 code review，hooks 是你唯一的「硬」质量/安全边界——AGENTS.md 里的自然语言会被模型在上下文压力下忽略，exit 2 不会。先把「Stop 跑测试 + PreToolUse 拦危险命令」这套最小门禁跑通，再谈其他杠杆。

### 对一人公司的适用性

极高，直击「无同事 review」这个最痛前提。Stop 钩子强制「测试通过才交回」= 让机器当那个永远在线、绝不疲劳的 reviewer；PreToolUse 拦危险命令 = 没有同事帮你兜底时的最后安全网；async 钩子做审计日志 = 睡前下单、早上回看的可追溯依据。成本上，门禁类钩子是确定性 shell 脚本，几乎不消耗 token，反而是省钱（避免模型反复返工）。唯一要留神：hook 写错会静默失效或误阻断，一人公司没有第二双眼睛，务必先在小任务上验证阻断行为再正式启用。

### 信息来源

1. Codex 官方 Hooks 文档（中文镜像，含完整三层结构、exit code 语义、async/mcp_tool 写法、timeout 默认值）：<https://www.codex-docs.com/configuration/hooks/>
2. Codex CLI Hooks GA 完整事件模型与信任机制（v0.133，2026-05-25）：<https://codex.danielvaughan.com/2026/05/25/codex-cli-hooks-after-ga-event-model-trust-verification-production-patterns>
3. v0.148.0 发布说明（async hooks + MCP 工具调用）：<https://codex.danielvaughan.com/2026/08/19/codex-cli-v0148-release-markdown-export-async-hooks-mcp-cost-visibility-bedrock-runtime-session-fork>
4. v0.148.0 第三方解读（async hooks 语义、最多 8 并发）：<https://www.getclaudeskills.com/blog/codex-cli-0-148-0-session-branching-export>

### 待核实

- async 字段的确切写法层级：官方镜像为三层结构（事件→matcher 组→hooks 数组，async 放在单个 handler 对象内），而 danielvaughan 文章用 {"matcher":{"tool_name":"..."},"handler":{...}} 结构，两者不一致，需以官方文档实测确认 [不确定]
- codex exec 非交互模式下 hooks 的精确行为（是否需要 --dangerously-bypass-hook-trust 才能运行）细节未逐一实测 [不确定]
- timeout 超时后的具体行为（是视为失败阻断、还是放行）未在文档明确 [不确定]
- 旧版 JSON 返回 {"decision":"reject"} 与官方文档 {"decision":"block"} 的兼容关系：部分二手资料仍用 reject，是否已被 block 取代未核实 [不确定]

## 8. 验证循环设计

### 核心做法

验证循环的底层逻辑：一个任务能不能「一次做对、无人盯防」，取决于有没有一个「便宜、确定、机器可判」的 check 把「done」和「not done」分开。没有这个 check，任何自治循环（/goal、codex exec 后台跑）都会要么永远跑、要么过早停。

五部分设计：

1. 测试命令怎么写——永远用仓库里已有的真实命令（make test / npm test / cargo test / pytest），不要让模型自己发明验证方式。把「验证命令」写进派单四要素（子系统/期望行为/验证命令/收尾动作），作为任务的验收标准，而不是事后补充。
2. 自验证迭代——用 /goal（Ralph Loop：Plan→Act→Test→Review→Iterate）让 agent 自己循环，或手动「最小改动→跑检查→读 diff→失败则带着失败信息重跑」。成功条件写成「闭系统」：目标 + 约束 + 可验证的 success 断言（例如「P95 从 480ms 降到 200ms 以下，新增 benchmark 断言通过」）。
3. 失败处理策略——限定重试次数（每文件最多 3 次，第 3 次失败就报告并停），禁止「改已通过测试的代码」除非用户明说；失败时带着失败输出重跑，而不是重写整段 prompt。
4. 回归防护——用 Stop 钩子「测试不过不许交回」（exit 2 强制继续）；用「人类写的断言」而不是「agent 生成的 print」做真正回归保护；验证通过后打 git checkpoint（tag/stash），后续改坏可回滚。
5. 无测试项目的替代方案——用便宜的观察反馈（shell 一行命令、读现有测试输出、python -c 打印值）做「观察」，但明确区分：观察 ≠ 回归保护；回归保护只能靠你自己写的测试套件，或者 CI 里的外部测试编排。

核心原则：让「脚手架（hooks/CI）做验证」，别让「模型自己做验证」——agent 生成的是 print 语句不是断言，只有外部确定性检查才可靠。

### 可直接复制的模板命令配置

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【1｜派单四要素里的「验证命令」字段（直接抄进任务）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 子系统

src/auth

## 期望行为

给登录加 refresh-token 轮换，旧 token 轮换后立即失效。

## 验证命令

npm test -- src/auth  
npm run typecheck

# 新增：一条断言「轮换后的 token 会使旧 token 失效」

## 收尾动作

跑完以上命令并保留输出；产出 diff 回执与验证结果。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【2｜用 /goal 做自治验证循环（Ralph Loop）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ~/.codex/config.toml 打开 goals

[features]  
goals = true  
[goal]  
max_iterations = 40  
auto_mode = true  
require_tests = true

# 然后在 TUI 里下单（Shift+Tab 进 auto 模式不停顿）：

/goal 给 auth 加 refresh-token 轮换。  
约束：不改公共 API、不新增依赖。  
成功：tests/auth 全部通过，且新增断言「轮换后的 token 使旧 token 失效」通过。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【3｜手动验证循环 checklist（可直接粘贴到任务末尾）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 验证循环 checklist

- [ ] 读取最近的 AGENTS.md 与 AGENTS.override.md
- [ ] 一句话确认任务范围
- [ ] 列出涉及的 MCP 连接器及其写边界
- [ ] 做最小可用改动
- [ ] 用仓库自己的测试/检查命令验证（npm test / make test / cargo test / pytest）
- [ ] 读 diff 看意图，而不是只看语法
- [ ] 记录「改了什么 / 验证了什么 / 什么仍需人工 review」
- [ ] 检查失败时，带着失败信息重跑，而不是重写 prompt

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【4｜失败处理：限重试 + 禁止回改已通过的代码（写进 AGENTS.md）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# AGENTS.md 追加

## 修复循环规则

1. 不要改动已通过全部测试的代码，除非用户明确要求。
2. 每次跑测试后，记录「测了哪些文件 + 内容 hash」。
3. 若某次修改让之前通过的测试变红，先回滚到上一个验证通过的 checkpoint 再修。
4. 每个文件最多改 3 次；第 3 次仍失败就报告失败并停止，不要无限循环。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【5｜Stop 钩子：测试不过不许交回（回归防护的硬门禁）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
#!/bin/bash

# ~/.codex/hooks/run-tests-or-block.sh

OUTPUT=$(npm test 2>&1)   # 换成你的真实测试命令
CODE=$?  
if [ $CODE -ne 0 ]; then
  echo "测试未通过，继续修复，不要交回。最近 30 行：" >&2
  echo "$OUTPUT" | tail -30 >&2  
exit 2                 # exit 2 = 强制模型继续，不能停下  
fi  
exit 0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【6｜验证通过打 checkpoint（可回滚）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
#!/bin/bash

# ~/.codex/hooks/checkpoint-if-passing.sh

if npm test >/dev/null 2>&1; then  
git add -A && git stash create "verified-$(date +%s)" 2>/dev/null ||   
git tag -f verified-latest  
echo "checkpoint 已打：verified-latest"  
fi  
exit 0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【7｜无测试项目：CI 外部编排（agent 改码，脚手架验证）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 让 codex exec 改码，但由外部 CI 跑真实测试

codex exec   
--sandbox workspace-write   
"修复 src/parser.rs 的失败测试。不要新建测试文件。  
用 cargo test 验证你的修复。"

# agent 跑完后，脚手架层独立验证：

cargo test --release 2>&1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【8｜按模型选择测试策略（省钱 profile）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ~/.codex/profiles/verify.toml —— 对不爱写测试的模型，强迫只跑已有测试

[instructions]  
additional = """  
专注改代码，用 `make test` 跑已有测试验证，不要新建测试文件。  
"""

# 启动：codex --profile verify "任务"

### 关键参数

| 参数                     | 官方默认值            | 一人公司推荐值                                      | 说明                        |
| ---------------------- | ---------------- | -------------------------------------------- | ------------------------- |
| /goal 的 max_iterations | 未明文（noqta 文称 40） | 40（够用即可，别无限）                                 | 自治循环的硬上限，防止无限跑烧钱          |
| /goal 的 require_tests  | false            | true                                         | 强制每次迭代跑测试                 |
| /goal 的 auto_mode      | false            | true（睡前任务）                                   | Shift+Tab 等价，不停顿确认        |
| 每文件重试上限                | 无默认              | 3 次                                          | 写进 AGENTS.md，第 3 次失败即报告停止 |
| Stop 钩子 timeout        | 600 秒            | 300                                          | 测试慢的项目按需加大                |
| 验证命令                   | 无（模型自拟）          | 仓库真实命令（npm test/make test/cargo test/pytest） | ★必须显式写进派单，别让模型发明          |

必须改的两项：① 在派单里显式写「验证命令」字段，否则模型会自己发明 print 语句式的假验证；② 打开 require_tests（或等效的 Stop 钩子门禁），把「跑测试」从可选项变成硬约束。

### 常见坑

1. 【模型把 print 语句当测试】agent 天然倾向写 print/观察语句而不是断言，这能「看值」但不能「防回归」。观察反馈 ≠ 回归保护，回归保护必须靠人类写的测试套件 + hooks 强制执行。
2. 【目标模糊导致永不终止或过早停】/goal 「把搜索变快」是开放系统，agent 会跑偏或瞎停。必须写成「目标+约束+可验证 success 断言」的闭系统。
3. 【失败就重写 prompt】正确做法是带着失败输出重跑，让模型在失败上下文里修；重写整段 prompt 等于丢掉定位信息、浪费 token。
4. 【改坏已通过的代码】无边界重试会让模型在「修 A 坏 B」的循环里反复，甚至覆盖本来正确的解法。必须写「不改已通过测试的代码 + 限 3 次重试」。
5. 【flaky 测试】1/5 概率失败的测试会误导 agent 去「修」本来没坏的工作代码。先修 flaky，再开自治循环。
6. 【设计决策类任务硬套自治循环】「搭一个通知系统」有太多正确答案，循环会选一个猛冲。设计决策留给人，执行留给 agent。
7. 【验证命令依赖外部环境】验证要打 staging/付费 API 才能做时，循环收紧不了，agent 只能空转。
8. 【版本差异】--approval-mode full-auto 等旧写法已失效（v0.147.0 起 --full-auto 移除），CI 编排里要用 --sandbox workspace-write。

### 降级与回退路径

1. /goal 自治循环不可用或跑飞：退回「手动循环」——最小改动→跑仓库测试→读 diff→失败带失败信息重跑，或退回 codex exec + 外部 CI 测试编排。
2. 无测试项目：先补一条最便宜的冒烟测试（或 shell 一行命令做观察），再逐步把观察升级成断言；实在没有就靠 CI 里的 build/lint 当最低门禁。
3. 验证门禁（Stop 钩子）误阻断：临时 /hooks 禁用该钩子，或 [features] hooks=false，定位后恢复。
4. 模型测试行为差异：用 profile 区分——对不爱写测试的模型强制「只跑已有测试」；对过度生成测试的模型引导「用 shell 观察，别写测试文件」。
5. 需要回滚到已知良好状态：验证通过时用 git tag/stash 打 checkpoint，失败时 git checkout 到该 checkpoint。

### 版本与生效时间

/goal 与 goals 特性自 v0.128 起可用（Ralph Loop 原生化）；Stop/PostToolUse 钩子做验证门禁自 hooks GA（2026-05-14，v0.133 前后）；--full-auto 于 v0.147.0（2026-08-07）移除、CI 编排改用 --sandbox workspace-write。

### 可自动化程度

高。核心闭环可完全无人值守：codex exec --sandbox workspace-write 让 agent 改码，Stop 钩子 + 外部 CI 测试负责验证，git checkpoint 负责回滚，--json 输出做计量。睡前下单、早上收「已验证通过 + 打了 checkpoint」的结果，是一人公司最高杠杆的异步形态。

### 优先级

P0。验证循环是「派单能不能一次做对」和「能不能放心异步跑」的分水岭——没有验证命令的任务是赌博，有验证命令的任务才是产能。一人公司没有 reviewer 兜底，验证循环就是你的 reviewer。

### 对一人公司的适用性

极高。无同事 review → Stop 钩子「测试不过不许交回」让机器替代那个永远在线的 reviewer；成本敏感 → 验证循环减少返工（返工是最贵的），且确定性脚本几乎不烧 token；异步杠杆 → 「验证命令 + 钩子门禁 + checkpoint」是睡前下单、早上收 PR 的唯一可靠闭环。注意两点：一是无测试项目别硬造测试文化，先用观察反馈 + CI build/lint 兜底；二是 flaky 测试和模糊目标是自治循环的两大杀手，一人公司没人为你 debug 循环，先修掉再放权。

### 信息来源

1. Codex /goal 的 Ralph Loop 模式与成功条件写法：<https://www.noqta.tn/en/blog/codex-goal-command-ralph-loop-autonomous-coding-2026>
2. 修复循环衰减与 typed revision contract（限重试、checkpoint、state-binding hook）：<https://codex.danielvaughan.com/2026/07/30/looping-not-reliability-state-bound-evidence-typed-revision-contracts-codex-cli-repair-loop-checkpoint-defence>
3. Agent 生成测试的观察反馈 vs 回归保护（Stop 钩子、profile 分模型）：<https://codex.danielvaughan.com/2026/06/23/rethinking-agent-generated-tests-observational-feedback-codex-cli-scaffold-testing-strategy>
4. 验证循环 checklist 与 codex review 工作流：<https://www.codexworkshop.com/research/codex-cli-workflows-20260528-0532> 与 <https://www.codexworkshop.com/research/codex-cli-workflows-20260624-0512>

### 待核实

- /goal 的 max_iterations / require_tests / auto_mode 官方默认值：来自二手资料（noqta 文章），官方文档未逐一核实，是否仍为当前配置项名与默认值需确认 [不确定]
- checkpoint 脚本中 git stash create / git tag 的具体写法为推荐方案，非官方能力，需按自身仓库调整 [不确定]
- 「GPT-5.2 几乎不写测试、Kimi K2-T 97.5% 任务写测试」等模型测试行为数据来自二手文章，未在官方来源核实 [不确定]
- 无测试项目「CI 外部编排 + codex exec」是否还需配合 approval 配置（旧 --approval-mode full-auto 已失效）细节未实测 [不确定]

## 9. 上下文与会话治理

### 核心做法

这一环治理两件事：① 长任务里「上下文怎么不爆、不丢关键决策」；② 多任务并行时「线程怎么不混、事后怎么找得回来」。

【auto_compact 压缩】当会话累积 token 逼近上下文窗口时，Codex 会把历史替换成一份「交接摘要」（保留进展、关键决策、约束、待办、续命所需路径/变量），腾出空间继续跑。它是长任务能跑数小时的关键，但本质是 lossy 的——细节会被丢弃或泛化，反复压缩会累积「摘要漂移」，让模型忘记早期决策、已排除的边界情况、三个压缩前读到的精确值。治理要点：

- 用 model_context_window 显式声明窗口大小（不配就用模型默认，gpt-5.3-codex 约 256k、gpt-5.4 约 1M）；
- 用 model_auto_compact_token_limit 控制「第一次压缩何时触发」，建议设在窗口 75–80%（早压缩比晚压缩更省 prompt cache、漂移更小）；
- 官方有 90% 硬钳制：effective_limit = min(你配的值, 窗口×0.90)，配再大也没用；
- 用 tool_output_token_limit 给单次工具输出封顶（默认不限，一个 cat 大文件能灌进几万 volatile token 打爆 cache 连续性），推荐 8000–12000。

【/new <name> 命名线程】给线程起名，从「一堆不可区分的 thread ID」变成「有标签的标签页」。命名会持久化、跨 CLI 重启保留、同步到分页历史列表。配合 /pin 置顶（最多 10 个）、/resume 恢复、/archive 归档、/delete 删除，形成一套工作集管理。

【side conversation】/side（别名 /btw）开一条临时侧聊，查个快问题、验证个假设，不污染主线程上下文。v0.146.0 起侧聊可持久化、可来回切换而不关闭任何一条（像浏览器标签页）。

【/export】v0.148.0 起把整个 TUI 对话导出成 Markdown，到剪贴板或文件——用于日志、写 ticket、事后复核，把「会话」变成可版本化、可交接、可审计的对象。

【长任务失忆与隐性成本】失忆来自压缩漂移；隐性成本来自「大窗口 ≠ 免费」：token 按处理量计费，窗口越大每次请求烧钱越多，且注意力会稀释（塞满旧历史时模型更难聚焦真正相关内容）。所以窗口不是越大越好，OpenAI 特意把默认调小。

### 可直接复制的模板命令配置

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【1｜一人公司压缩配置（config.toml）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ~/.codex/config.toml

model = "gpt-5.3-codex"  
model_context_window = 256000              # 显式声明窗口（不配用模型默认）  
model_auto_compact_token_limit = 160000    # 约窗口 62%，早压缩省 cache  
model_compact_token_limit = 200000         # 可选：压缩目标水位  
model_reasoning_effort = "medium"

# 长任务专用 profile（更大窗口 + 早压缩）

# ~/.codex/long-task.config.toml

model_context_window = 256000  
model_auto_compact_token_limit = 150000    # 75–80% 区间早压缩

# 单次工具输出封顶（防止一个 cat 大文件打爆 cache 连续性）

tool_output_token_limit = 8000

# 启动：codex --profile long-task "任务"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【2｜会话治理命令速查（TUI 内）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
/new "incident-db-pool"     # 命名新线程（不退出 CLI）  
/clear "feature/auth-refactor"  # 清空并开命名线程  
/rename "新名字"            # 重命名当前会话  
/pin                        # 置顶当前线程（/unpin 取消）  
/resume                     # 从会话列表恢复  
/side  或 /btw              # 开临时侧聊，不污染主线程  
/fork "explore-alt-schema"  # 分叉当前线程试另一种方案  
/fork --temporary "quick"   # 临时分叉（不进列表）  
/export /tmp/review.md      # 导出完整对话为 Markdown  
/compact                    # 手动压缩，立即释放上下文  
/status                     # 看模型/权限/可写根/token/成本/会话详情  
/usage                      # 看 token 活动、速率限制、可用额度

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【3｜会话治理配置（[session]）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ~/.codex/config.toml

[session]  
auto_name = true        # 按首条 prompt 自动命名（默认 false）  
max_pinned = 10         # 置顶线程上限（默认 10）  
persist_sides = true    # 侧聊跨重启持久化（默认 true）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【4｜CLI 级会话管理（终端里）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
codex resume                # 恢复最近一次会话  
codex resume <id>           # 按 ID 恢复  
codex fork                  # 分叉当前会话（保留历史）  
codex exec fork             # 从当前状态分叉（v0.148.0）  
codex archive <id|name>     # 归档会话  
codex unarchive <id|name>   # 恢复归档  
codex delete <id|name>      # 永久删除  
codex queue "跟进指令"      # 给正在跑的无头会话发消息（v0.149.0）  
codex agents                # 交互式任务看板（v0.149.0）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【5｜长任务防失忆：把关键决策落到文件而非依赖记忆】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 睡前下单模板：要求 agent 把决策写进文件，压缩也不丢

「重构 auth 模块。把每个关键决策、已排除的方案、  
精确到值的约定写入 DECISIONS.md，随代码一起提交。  
收尾跑 npm test 并 /export 一份 transcript 到 results/。」

### 关键参数

| 参数                             | 官方默认值                                   | 一人公司推荐值                   | 说明                     |
| ------------------------------ | --------------------------------------- | ------------------------- | ---------------------- |
| model_context_window           | 模型默认（gpt-5.3-codex 约 256k，gpt-5.4 约 1M） | 日常不配；长任务显式 256000         | 显式声明窗口大小               |
| model_auto_compact_token_limit | 官方未明文（多来源：32000 / 200000 / 模型窗口×90%）    | ★150000–160000（窗口 60–75%） | 第一次压缩触发阈值，90% 硬钳制      |
| tool_output_token_limit        | unset（不限）                               | ★8000–12000               | 单次工具输出封顶，防止大文件打爆 cache |
| [session].auto_name            | false                                   | true                      | 按首 prompt 自动命名线程       |
| [session].max_pinned           | 10                                      | 10                        | 置顶线程上限                 |
| [session].persist_sides        | true                                    | true                      | 侧聊跨重启持久化               |
| /new 命名                        | 无（v0.146.0 前为匿名 thread ID）              | ★始终命名                     | 命名持久化、可检索              |
| /export                        | 无（v0.148.0 新增）                          | 长任务收尾必做                   | 导出 Markdown 到剪贴板/文件    |

必须改的两项：① 显式设 model_auto_compact_token_limit（别用默认——默认要么太小频繁压缩、要么逼近窗口才压导致溢出）；② tool_output_token_limit 从「不限」降到 8000–12000，这是最便宜的抗失忆 + 省 cache 开关。

### 常见坑

1. 【默认阈值不公开且各来源打架】CSDN 教程写 32000、TokenPilot 文章写 200000、还有「模型窗口×90%」三套说法，官方没明文。别信单一二手值，按「窗口 60–75%」自己显式设。
2. 【配超过 90% 窗口被静默钳制】effective_limit = min(你配的, 窗口×0.90)，配 250000 在 256k 窗口上实际 230400 触发。写更大没意义。
3. 【压缩是 lossy 的，反复压缩累积失忆】多次压缩后模型会忘记早期决策、已排除的边界、精确值。长任务必须把关键决策落到 DECISIONS.md 之类的文件里，不能靠对话记忆。
4. 【大窗口不是免费午餐】token 按量计费，窗口越大每次请求越贵，且塞满旧历史会稀释注意力。OpenAI 默认调小是刻意的，别盲目拉 1M。
5. 【tool_output_token_limit 默认不限】一个 cat 大文件能灌进几万 volatile token，破坏 prompt cache 前缀连续性，后续每轮 cache miss 全价重算。必须设上限。
6. 【/side 旧行为】v0.146.0 前 /side 是「切回主线程即永久关闭」的临时对话，v0.146.0 起才可持久化切换。旧教程里的用法已过时。
7. 【匿名线程难找回】不改名的话一堆不可区分的 thread ID，靠记忆/翻屏找回。养成「开线程就命名」的习惯。
8. 【/clear 会丢名字】/clear 不带名字会清空当前线程并失去命名，v0.146.0 起 /clear 也接受可选名，避免手滑。

### 降级与回退路径

1. 压缩导致失忆：把关键决策外置到文件（DECISIONS.md）并 git 提交；必要时 /export 完整 transcript 存档再 /new 重开，用「总结 + 待办」手写交接。
2. 上下文频繁爆掉：降 model_auto_compact_token_limit 提前压缩；或用 profile 分任务（长任务用大窗口 profile，日常用小窗口）。
3. 线程找不到/误删：codex unarchive 恢复归档；codex resume 列表翻找；/pin 保住重要线程。
4. /export 不可用（旧版本）：用 /copy 复制最新输出，或升级到 v0.148.0+。
5. 侧聊污染主线程（旧版行为）：升级 v0.146.0+ 启用 persist_sides，或改用 /fork --temporary 做一次性探索。
6. 长任务失控成本：用 /status、/usage 盯 token/成本（v0.148.0 起成本显示在 statusline），配合 model_reasoning_effort 下调兜底。

### 版本与生效时间

/new 自 v0.2 起（命名参数自 v0.146.0，2026-07-29）；/pin /unpin、侧聊持久化切换、[session] 配置自 v0.146.0；分页会话历史自 v0.145.0；/export 与 codex exec fork 自 v0.148.0（2026-08-18）；codex agents 看板与 /cd、codex queue 自 v0.149.0（2026-08-20）。auto_compact 的 90% 钳制自 v0.100.0。

### 可自动化程度

高。压缩阈值、tool_output_token_limit、session 配置全部可用 config.toml 固化，配合 codex exec --json 的 token_count 事件做无人值守计量；/export、codex archive/resume 可脚本化，让「睡前下单、早上收已导出 transcript + 已归档会话」成为标准闭环。

### 优先级

P1。上下文治理决定「异步长任务能不能放心过夜」——漏配 tool_output_token_limit 或压缩阈值，长任务会在凌晨默默烧钱 + 失忆。但它不像 Hooks/验证循环那样直接决定对错，所以排在 P0 之后、仍是高杠杆必做项。

### 对一人公司的适用性

高。成本敏感 → tool_output_token_limit + 早压缩是直接省钱（cache 命中率、返工减少）；异步杠杆 → 命名线程 + /pin + /export 让你睡前下单、早上能快速定位「哪条线程干了什么、花了多少」；无同事 review → /export 的 transcript + DECISIONS.md 是你自己事后复核的唯一依据。唯一注意：一人公司容易贪「大窗口」，而大窗口恰恰是「烧钱 + 注意力稀释」的来源，克制窗口、勤外置决策，才是正解。

### 信息来源

1. Codex CLI v0.146 会话管理（命名会话、线程置顶、侧聊切换）：<https://codex.danielvaughan.com/2026/07/29/codex-cli-v0146-session-management-named-sessions-thread-pinning-side-conversations-forking>
2. 上下文压缩调优（90% 钳制、每模型默认、tool_output_token_limit）：<https://codex.danielvaughan.com/2026/04/16/codex-cli-context-compaction-tuning-long-sessions>
3. TokenPilot 与 prompt cache（tool_output_token_limit 作为摄入门、早压缩策略）：<https://codex.danielvaughan.com/2026/07/03/tokenpilot-cache-efficient-context-management-codex-cli-prompt-cache-compaction-eviction-cost>
4. 1M 上下文窗口与 OpenAI 默认调小的原因：<https://www.explainx.ai/blog/enable-1m-token-context-window-codex-cli-gpt-5-6-sol-august-2026>
5. v0.148/0.149 会话导出与任务看板：<https://vibecodedthis.com/blog/codex-cli-0148-0149-session-fork-agents-dashboard-august-2026>
6. Codex 命令速查（/new /export /side /pin 等）：<https://www.scriptbyai.com/codex-commands-cheat-sheet/>

### 待核实

- 90% 钳制公式自 v0.100.0 引入后是否仍为当前行为（后续版本是否调整）未核实 [不确定]
- [session].auto_name / max_pinned / persist_sides 的默认值与取值范围仅见于二手文章，官方配置参考未确认 [不确定]
- model_auto_compact_token_limit 官方默认值：官方未明文，二手来源给出 32000 / 200000 / 模型窗口×90% 三套矛盾值，无法确证 [不确定]
- model_compact_token_limit 是否为当前有效配置项（与 model_auto_compact_token_limit 的关系）未在官方文档确认 [不确定]
- model_context_window 各模型默认值（gpt-5.3-codex 256k、gpt-5.4 1M）来自二手资料，官方未逐一核实 [不确定]

## 10. 成本与额度可视化

### 核心做法

Codex 自 2026-04-02 起从「按消息计数」改为「token 额度（credit）制」，成本敏感型一人公司必须同时回答三个问题：credit 怎么换算成钱、在哪看实时消耗、怎么在无人值守的 CI 里自动计量。

【换算】1 credit ≈ $0.04（经交叉验证：官方费率卡 GPT-5.3-Codex = 43.75 credits/1M 输入，43.75×0.04=$1.75，与 API 侧 $1.75/M 输入完全吻合）。费率按每百万 token 三档计费：输入 / 缓存输入 / 输出。当前 GPT-5.6 家族：Sol（前沿）约 100/500 credits/1M（输入/输出）、Luna（廉价快速）约 5/30；缓存输入约是普通输入的 1/10，是最大的省钱杠杆。上一代 GPT-5.5 参考费率 125/12.50/750（缓存 12.50 ≈ 输入 1/10）。

【三个查看入口分工】  
① /status 看「当前会话」：活动模型、审批策略、可写根、剩余上下文；v0.148+ 额外显示本线程累计估算成本（如 Thread cost: ~$0.47）。  
② /usage 看「账户级」：日/周/累计 token 活动菜单，也是兑换「限速重置」的地方。  
③ /statusline 看「常驻」：TUI 底部状态栏，把限速、token 计数、上下文占用、成本估算永久钉住，持久化到 config.toml 的 tui.status_line。

【CI 计量】用 codex exec --json 抓事件流，token_count 事件携带累计 input/cached/output/reasoning 四项 token 数，把相邻两次差值累加即可得到单次运行消耗；turn.completed 事件也带完整 usage 对象。这是无人值守计量的唯一可靠入口。

【Plus 5 小时窗口回归的影响】2026-08-26 起 Plus 恢复滚动 5 小时窗口（与周配额并行），意味着 ChatGPT 登录态下不能无脑跑长任务：睡前下单前必须先 /status 确认 5 小时 + 周两个窗口都有余量，否则任务中途被限。Pro $100/$200 未来数月暂豁免此窗口。

### 可直接复制的模板命令配置

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【1｜会话内查看消耗（三个命令各司其职）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# TUI 内输入：

/status        # 当前会话：模型/审批/可写根/剩余上下文 + v0.148 起估算成本  
/usage         # 账户级：日/周/累计 token 活动，兑换限速重置  
/statusline    # 切换底部常驻状态栏

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【2｜CI 计量：抓 token_count 事件算消耗】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 抓累计 token 事件（input/cached/output/reasoning 四项）

codex exec --json "重构 auth 模块" 2>/dev/null   
| jq -c 'select(.payload.type == "token_count") | .payload'

# 抓 turn 结束时的 usage 对象（含 reasoning_tokens，v0.125 起）

codex exec --json "重构 auth 模块" 2>/dev/null   
| jq 'select(.type == "turn.completed") | .usage'

# 累加一次运行的总输出 token（差值法示例）

codex exec --json "跑测试并修复失败" 2>/dev/null   
| jq -s '[.[] | select(.payload.type == "token_count") | .payload.output_tokens]  
| last'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【3｜状态栏常驻（config.toml 持久化）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ~/.codex/config.toml

tui.status_line = "context, model, cost"   # 钉住上下文占用/模型/成本估算

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【4｜睡前下单前的额度体检（一行脚本）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 非交互模式也能拿到限速信息，跑长任务前先体检

codex exec --json "报告你当前会话的剩余上下文，不要改任何文件" 2>/dev/null   
| jq -r 'select(.payload.type == "token_count") | .payload' | tail -1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【5｜credit→美元 换算速查（jq 或心算）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 1 credit ≈ $0.04；例：Sol 100 credits/1M 输入 = $4/M 输入

# 输出 token 比输入贵约 5 倍（Sol 500/100），省钱先砍输出+启用缓存输入

### 关键参数

| 参数                     | 官方默认值                    | 一人公司推荐值                       | 说明                                               |
| ---------------------- | ------------------------ | ----------------------------- | ------------------------------------------------ |
| 计费单位                   | credit（1 credit ≈ $0.04） | 同左，换算进 CI 报表                  | 2026-04-02 起按 token 计 credit                     |
| 计费窗口                   | 滚动 5 小时窗口 + 周配额（并行）      | 睡前下单前两者都查                     | Plus 自 2026-08-26 恢复 5 小时窗口                      |
| 模型（成本主变量）              | GPT-5.6 Sol 前沿默认         | ★按任务分层：探索/批量用 Luna，架构/重构用 Sol | 模型选择比 prompt 长度影响大得多                             |
| model_reasoning_effort | 官方未明文                    | ★常规 medium、CI/批量 low          | 推理 token 计费但不出现在可见输出，1x~3x 放大                    |
| tui.status_line        | 未配置（无状态栏）                | ★"context, model, cost"       | 常驻成本/上下文，成本敏感必开                                  |
| codex exec --json      | 默认人读输出                   | ★--json（CI 计量唯一入口）            | token_count / turn.completed 事件                  |
| MCP 服务器数量              | 不限                       | ★按需开关，用完禁用                    | 每台 MCP 每轮注入 schema，一个 GitHub MCP 可多 ~55k token/轮 |
| 缓存输入                   | 自动                       | ★保持 AGENTS.md 精简以复用缓存         | 缓存输入约 1/10 价                                     |

必须改的两项：① tui.status_line 显式开启成本/上下文常驻（默认关着，成本敏感用户等于盲开）；② 按任务把模型和 reasoning_effort 分层，而不是全程 Sol+high。

### 常见坑

1. 【共享额度池】Codex、ChatGPT Work、ChatGPT for Excel、Workspace Agents 共用一个 allowance/credit 池。你没用 Codex 额度也会掉，因为别处（如表格 agent）在烧同一个池。
2. 【两个口径不同】5 小时窗口按「消息」计（GPT-5.5 每消息均摊 5-45 credits），周配额按 credit 计。一个窗口显示 40% 剩余，周配额可能已经爆了——单次大循环（~250k 输入）可烧约 50 credits，6 次就耗光 Plus 整周。别只看 5 小时进度条。
3. 【图像生成 3-5 倍消耗】Codex 内启动的图像生成计入同一额度，且消耗是普通轮次的 3-5 倍；用完额度后还继续从 credit 扣。ChatGPT 侧的图片配额与 Codex 无关，别把 ChatGPT 的「50 张/天」横幅当成 Codex 额度。
4. 【MCP 税】每台 MCP 每轮注入完整 tool schema，线性叠加。GitHub+Slack+Jira+DB 四台同开可加 ~10 万 token/轮的 schema 开销。用完就 disable。
5. 【推理 token 不可见但计费】reasoning token 不计入你看到的输出，但按输出费率计费。medium 可让有效 token 翻倍，high/xhigh 三倍。


6. 【上下文累积 + 压缩螺旋】context 超 80%（model_auto_compact_token_limit 默认）触发自动压缩，压缩本身又烧 token；长会话会陷入「长上下文→压缩→更长」螺旋。
7. 【JSON 事件封装结构随版本变】token_count 事件的字段路径在不同版本有 .type 与 .payload.type 两种写法，jq 脚本要按你实际版本实测，别照抄旧博客。
8. 【登录态决定费率表】ChatGPT 登录态按 credit 计（受 5 小时窗口），API key 按 API token 计费（无窗口限制）。同一模型两条路径费率与限额完全不同，别混算。
9. 【Plus 5 小时窗口回归】2026-08-26 起 Plus 恢复 5 小时窗口，重度用户睡前下单若窗口余量不足会中途挂起；Pro $100/$200 暂豁免，别用 Pro 的经验去推断 Plus。

### 降级与回退路径

1. 额度耗尽：等 5 小时窗口滚动 / 等周重置；或购买额外 credits；或切小模型（Sol→Terra→Luna）让额度撑更久；或改用 API key 走按 token 计费（无窗口限制，成本可控）。
2. Plus 5 小时窗口卡住：改用 codex exec + API key（CODEX_API_KEY / codex login --api-key）跑本地任务，绕开订阅窗口；周配额同理。
3. 计量脚本字段对不上：先跑一次 codex exec --json 裸输出 jq 看事件封装结构，按实际 .type / .payload.type 调整过滤条件。
4. 成本失控：优先关掉不用的 MCP、精简 AGENTS.md、把批量/探索任务路由到 Luna，并下调 reasoning_effort；这是最快的止损，比升级套餐更快。
5. 无窗口期短暂结束的应对：若曾依赖 7 月取消窗口的「无限制」期，现在必须重新引入 /status 体检 + CI 计量，把成本反馈回路自动化，而不是依赖临时政策。

### 版本与生效时间

credit 制 2026-04-02 生效；v0.125（2026-04-25）codex exec --json 增加 reasoning token 上报；v0.140（2026-06）引入 token usage dashboard；v0.148（2026-08-18）/status、statusline、终端标题栏增加估算 thread credits/cost；Plus 5 小时窗口 2026-08-26 恢复（2026-08-25 由 Tibo Sottiaux 宣布）。

### 可自动化程度

高，是三个条目里最可自动化的。codex exec --json 是 CI/定时任务一等入口，token_count 与 turn.completed 事件可被 jq 无人工解析，直接产出每次运行的成本报表；/status 的额度信息也能在非交互模式抓到。对一人公司，这意味着「睡前下单前自动体检额度 + 运行后自动记账」都能脚本化，无需人工盯盘。

### 优先级

P0。成本敏感是一人公司的硬约束，而额度可视化是所有省钱动作（切模型、关 MCP、调 reasoning）的前提——看不见就无从优化。先跑通 CI 计量，再谈并行与模型分档。

### 对一人公司的适用性

极高。无同事 review → 没有第二双眼睛帮你盯成本，必须靠 /status + /statusline + CI 计量把消耗可视化；成本敏感 → credit 换算、模型分层、缓存输入是直接省钱杠杆；异步杠杆 → 睡前下单前用一行脚本体检 5 小时+周双窗口余量，早上收结果时顺手看 token_count 账单。唯一要注意：Plus 5 小时窗口回归后，订阅态的长任务不再「随便跑」，API key 是按 token 计费的可靠降级路径。

### 信息来源

1. OpenAI 官方 Pricing（credit 费率卡、5 小时窗口、credits 说明）：<https://developers.openai.com/codex/pricing>
2. OpenAI 官方 Changelog（v0.125 reasoning 上报、v0.148 成本可见性）：<https://developers.openai.com/codex/changelog>
3. v0.148.0 成本可见性详解：<https://codex.danielvaughan.com/2026/08/19/codex-cli-v0148-release-markdown-export-async-hooks-mcp-cost-visibility-bedrock-runtime-session-fork>
4. token 消耗诊断与 token_count 事件：<https://codex.danielvaughan.com/2026/06/10/codex-cli-token-consumption-diagnosis-reduction-quota-drain-practitioner-toolkit>
5. 登录态两套计费与模型访问差异：<https://codex.danielvaughan.com/2026/06/13/codex-cli-authentication-paths-chatgpt-login-api-key-billing-rate-limits-model-access>
6. Plus 5 小时窗口恢复（2026-08-26）：<https://www.ithinkdiff.com/openai-codex-five-hour-limit>

### 待核实

- GPT-5.6 Sol 的精确 credit 费率（100/500 vs 上一代 125/750）及缓存输入档 [不确定]
- GPT-5.6 Terra 的 credit 费率（输入/缓存/输出三档）未在捕获到的官方费率卡中出现 [不确定]
- Plus 每 5 小时窗口的具体额度（历史推测 ChatGPT Work ~40 条/5h、Codex ~10 次任务提交，本次重启用新值）官方未公布 [不确定]
- model_auto_compact_token_limit 默认阈值（一说 80% 窗口 / 64000）是否可调范围 [不确定]
- token_count 事件的 JSON 封装结构（.type 与 .payload.type 两种路径）在当前版本的准确写法 [不确定]

## 11. 并行与自定义 agent 分档

### 核心做法

单个 agent 会撞三堵墙：上下文过载、无分工、无协调。Codex 的 Subagent 工作流用「主 agent 拆分+协调+汇总，子 agent 在独立线程干一件边界明确的事」来解决——探索、审查、测试、文档核验等独立子任务并行跑，最后只把提炼结果（证据/结论/风险/文件位置）交回主线程，把噪声中间输出挡在主线程之外。

【何时该拆（读密集优先）】适合并行：代码库探索、PR 多维审查、测试/日志分析、文档检索、依赖核验、风险分类、多方案比较——特征是「子任务独立 + 结果可结构化汇总 + 不争抢同一批文件」。  
【何时不该拆（写密集慎用）】多个 agent 同时改同一文件/公共接口、任务有严格前后依赖、需求未明、范围很小、需共享大量中间态——并行会制造冲突和协调开销，得不偿失。稳妥流程是「并行探索/审查 → 主 agent 定方案 → 只让一个 worker 改 → 再并行验证」。

【怎么拆 + 分档省钱开关】核心省钱逻辑：explorer 用便宜模型、worker/reviewer 用贵模型。Codex 内置三个 agent：default（通用后备）、worker（执行/修复）、explorer（只读探索）。自定义 agent 是独立 TOML 文件（~/.codex/agents/ 个人级、.codex/agents/ 项目级），每个文件可单独 pin model 和 model_reasoning_effort——这就是「explorer 用 gpt-5.6-terra/luna 便宜读、worker 用 gpt-5.6-sol 贵写、reviewer 用 gpt-5.6-sol 高推理把关」的落地开关。

【触发方式】Codex 只在被显式要求时才 spawn 子 agent（或 AGENTS.md/skill 指令要求）。好提示词要说清：拆成几个、每个职责、读写权限、是否并行、是否等全部、返回格式。

### 可直接复制的模板命令配置

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【1｜全局并发上限（config.toml）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ~/.codex/config.toml 或 项目 .codex/config.toml

[agents]  
max_threads = 6        # 并发线程上限，官方默认 6  
max_depth = 1          # 嵌套深度，官方默认 1，别调大

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【2｜自定义 agent 分档（explorer 便宜 / worker 贵）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# .codex/agents/explorer.toml —— 便宜模型只读探索

name = "explorer"  
description = "只读代码库探索，定位相关文件、梳理调用链、收集证据"  
developer_instructions = "保持探索态，追踪真实执行路径，引用文件与符号，不要提修复建议，优先精确搜索而非广扫。"  
model = "gpt-5.6-terra"          # 便宜中档，够用  
model_reasoning_effort = "low"  
sandbox_mode = "read-only"

# .codex/agents/implementer.toml —— 贵模型执行修改

name = "implementer"  
description = "实现功能、修复 bug、更新测试"  
developer_instructions = "只改明确指派给你的文件，不要回退/覆盖他人改动，改动保持机械且小，最终列出改动文件与验证结果。"  
model = "gpt-5.6-sol"            # 前沿模型，写的质量是命  
model_reasoning_effort = "high"

# .codex/agents/reviewer.toml —— 贵模型高推理把关

name = "reviewer"  
description = "审查代码正确性、安全、测试缺口"  
developer_instructions = "像 owner 一样审查：优先正确性、安全、行为回归、缺失测试；不评论风格。"  
model = "gpt-5.6-sol"  
model_reasoning_effort = "high"  
sandbox_mode = "read-only"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【3｜触发并行审查（一句话提示词）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
请审查当前分支相对 main 的改动。启动三个并行只读 Subagent：

1. security_reviewer —— 检查认证、授权、输入验证、敏感信息风险
2. test_reviewer —— 检查测试缺口、边界条件、潜在不稳定测试
3. maintainability_reviewer —— 检查复杂度、重复代码、长期维护风险  
   等待全部完成后，按严重程度汇总问题，每项给文件路径、代码位置、原因、建议。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【4｜串行编排（先探索后动手，避免写冲突）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
先启动 explorer 和 docs_researcher 并行。等两者完成后，由主线程判断根因。  
根因明确后，只启动一个 worker 修改。修改完成后，再并行启动 reviewer 和 test_agent 验证。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【5｜CLI 管理线程】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
/agent   # 查看/切换活动或已完成的 agent 线程；审批弹窗里按 o 打开来源线程

### 关键参数

| 参数                               | 官方默认值                         | 一人公司推荐值                                                  | 说明                          |
| -------------------------------- | ----------------------------- | -------------------------------------------------------- | --------------------------- |
| agents.max_threads               | 6                             | 3-6（读密集审查 3 起步，别一上来 6）                                   | 并发线程上限                      |
| agents.max_depth                 | 1                             | 1（★别调大）                                                  | 调大会反复 fan-out 烧 token/延迟/资源 |
| agents.job_max_runtime_seconds   | 1800（spawn_agents_on_csv 回退值） | 1800                                                     | 单 worker 超时                 |
| agents.interrupt_message         | true                          | true                                                     | 中断时给模型留可见提示                 |
| 自定义 agent model                  | 继承父会话                         | ★explorer→gpt-5.6-terra/luna，worker/reviewer→gpt-5.6-sol | 分档省钱的核心开关                   |
| 自定义 agent model_reasoning_effort | 继承父会话                         | ★explorer low，worker/reviewer high                       | 与 model 配对                  |
| sandbox_mode（per agent）          | 继承父会话                         | explorer/reviewer read-only，worker workspace-write       | 只读 agent 绝不写                |

必须改的一项：给 explorer 单独 pin 便宜模型 + read-only。否则探索这种最吃 token 的活儿默认走贵模型，钱全烧在「读代码」上。

### 常见坑

1. 【写密集并行 → 冲突】多个 agent 同时改代码会互相覆盖，OpenAI 明示「要谨慎」。并行只用于读/审查/分析，写操作收敛到单个 worker。
2. 【并行不省钱】官方明确「subagent 工作流消耗更多 token」——并行省的是墙上时间，不是总 token。不要以为拆越多越便宜。
3. 【max_depth 调大】官方明示会把宽泛委派变成反复 fan-out，token、延迟、资源一起涨。保持 1。
4. 【权限继承】子 agent 继承父会话的沙箱/审批/--yolo 实时覆盖，即使 agent 文件设了不同默认。启动并行前先 /permissions 确认，别让所有 agent 都拿到高权限。
5. 【非交互流程审批失败】无人值守里，子 agent 需要新审批的操作会直接失败并回传父工作流，不能依赖中途人工审批。并行任务在 CI 里要预判权限。
6. 【自定义 agent 覆盖内置】自定义 explorer 会覆盖内置 explorer，别用同名造成意外行为。
7. 【文件名 vs name】Codex 以 name 字段为准（不是文件名），文件名与 name 保持一致只是约定，别让两者不一致造成困惑。
8. 【模型写旧 ID】把 agent 文件里的 model 写成已下线 ID（gpt-5.4 等）会失效，参见 model_deprecation 排查清单。
9. 【并发过高】6 线程全开会 token 飙升 + 大量审批弹窗 + 争抢 CPU/内存/端口 + 日志难读。读密集审查 3 起步。

### 降级与回退路径

1. 并行导致写冲突：回退到「并行只读探索 → 单 worker 串行写 → 并行验证」的编排，写操作永远收敛到一个 agent。
2. 成本因并行飙升：把 explorer/审查类 agent 从贵模型降到 gpt-5.6-terra/luna，或直接减少并发数（max_threads=3）。
3. 深度递归需求：绝大多数场景 max_depth=1 够用；确需递归时逐级显式委派，不要靠调大 max_depth 让模型自由 fan-out。
4. 无人值守审批失败：给子 agent 预设只读/workspace-write 沙箱 + approval_policy=never，或对单个 agent 显式 sandbox_mode，避免中途要审批。
5. 自定义 agent 未生效：检查 .codex/ 是否被信任、agent 文件是否在正确目录、name 字段是否与 spawn 引用一致；用 /agent 确认线程是否真的起来。

### 版本与生效时间

Subagent 工作流当前版本默认开启；agents.max_threads/max_depth 显式可配自 v0.128.0 左右；自定义 agent（.codex/agents/*.toml）随 2026 年 subagents 能力成熟演进。Codex 周更，字段名（如 max_concurrent_threads_per_session 是否成为新别名）需以官方 changelog 为准。

### 可自动化程度

中-高。Subagent 靠提示词触发，AGENTS.md/skill 指令也能触发委派，因此可与 codex exec 结合跑无人值守的多维审查（如睡前下单并行 PR 审查）。但写密集并行的冲突风险高、且并行更烧 token，自动化收益主要在「读密集审查/分析」场景；写操作建议保持单 worker 串行。

### 优先级

P1。并行审查是「无同事 review」的最直接替代品——用 security/test/maintainability 三个只读 agent 模拟一个 review 团队，是高杠杆；但成本敏感决定了必须先跑通 cost_control（P0）的计量，否则并行烧 token 没账可算。

### 对一人公司的适用性

高，精准命中三个前提。无同事 review → 并行多维只读审查是「没有 review 团队却有 review 效果」的最优解；成本敏感 → explorer 便宜/worker 贵的分档 + 读密集优先 + max_depth=1 是克制省钱的关键；异步杠杆 → 睡前用 codex exec 触发并行只读审查、早上收汇总报告，完全契合。唯一要守的纪律：写操作永远单 worker 串行，并行只给「读」用。

### 信息来源

1. OpenAI 官方 Subagents（内置 default/worker/explorer、max_threads=6/max_depth=1/job_max_runtime_seconds=1800、自定义 agent 字段 schema）：<https://developers.openai.com/codex/subagents>
2. ChatGPT Learn Subagents（模型选择建议 gpt-5.6/terra、读密集优先、写密集慎用）：<https://learn.chatgpt.com/docs/agent-configuration/subagents>
3. 官方 best-practice 转译（PR 三 agent 审查模式、model 分档示例）：<https://github.com/shanraisshan/codex-cli-best-practice/blob/main/best-practice/codex-subagents.md>
4. 多模型路由分档（explorer gpt-5.4-mini / implementer gpt-5.4 / reviewer gpt-5.5 层级）：<https://codex.danielvaughan.com/2026/06/07/codex-cli-multi-model-daily-workflows-gpt55-spark-mini-open-weight-cost-quality-routing>
5. 本地 Ollama 当便宜 subagent（explorer/worker 分档省主模型 context）：<https://rjv.im/blog/solution/codex-local-ollama-subagents>

### 待核实

- agents.max_concurrent_threads_per_session / default_subagent_model / default_subagent_reasoning_effort / [agents].enabled 是否为 max_threads 等字段的新别名（仅见于单篇中文二手资料）[不确定]
- spawn_agents_on_csv（CSV 批量）任务的可用性与适用场景未在官方文档核实 [不确定]
- subagent 能力默认开启的准确 CLI 起始版本（官方只写「当前版本默认开启」）[不确定]
- 自定义 agent 文件可覆盖的 config.toml 键全集是否随版本继续演进 [不确定]

## 12. 模型弃用与迁移时点

### 核心做法

OpenAI 的模型弃用分两档：「Deprecated」（宣布即开始倒计时，模型仍可用）与「Shut down」（请求不再解析、直接报错）。Codex 侧以周为单位迭代，两周前的建议就可能失效，一人公司必须把「模型 ID 排查」变成可重复执行的脚本，而不是靠记性。

【2026 年两波关键下线】  
① 2026-07-23（已执行）：一次性下线 Codex 系列——gpt-5-codex、gpt-5.1-codex、gpt-5.1-codex-max、gpt-5.1-codex-mini、gpt-5.2-codex，替代为 gpt-5.6-sol（其中 gpt-5.1-codex-mini 映射到 gpt-5.6-terra）。同波还下线 gpt-5-chat-latest、gpt-5.1-chat-latest、computer-use-preview、o3-deep-research、o4-mini-deep-research。  
② 2026-08-31（当前最紧）：gpt-5.4 与 gpt-5.4-mini 从 Codex 的 ChatGPT 登录态下线，迁往 gpt-5.6-terra / gpt-5.6-luna。注意：这只影响 ChatGPT 登录态，API key 不受影响。同时 gpt-5.2、gpt-5.3-codex 也已对 ChatGPT 登录态弃用。

【ChatGPT 登录态 vs API key 的关键差异】  
两条认证路径走完全不同的后端与计费：ChatGPT 登录态走本地代理→chatgpt.com/backend-api/codex/responses，按订阅 credit 计费（5 小时窗口+周配额），但享受「新模型首发、Cloud/Fast mode、Spark」等订阅能力；API key 直连 api.openai.com/v1/responses，按 token 计费（无窗口限制），但拿新模型有延迟、无 Cloud/Fast mode、可接第三方 provider。关键推论：登录态的模型弃用（如 gpt-5.4）不影响 API key 用户，反之 API key 侧的弃用（如 gpt-5.2 系列 2026-06-30 API sunset）不直接等同登录态。

【排查清单】凡是在 config.toml、自定义 agent TOML、定时任务、codex exec --model 脚本里出现过的 model id，都要 grep 一遍；命中已下线 ID 就改，别等请求失败才发现。

### 可直接复制的模板命令配置

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【1｜全库排查 model id（grep 已下线 ID）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 2026-07-23 已下线 + 2026-08-31 将下线的 Codex 系列

rg -n "gpt-5-codex|gpt-5.1-codex|gpt-5.1-codex-max|gpt-5.1-codex-mini|gpt-5.2-codex|gpt-5.4(-mini)?|gpt-5.2|gpt-5.3-codex"   
~/.codex/ .codex/ ./  2>/dev/null

# 精确到配置文件与 agent 文件

rg -n "model\s\*=" ~/.codex/config.toml ~/.codex/\*.config.toml ~/.codex/agents/ .codex/agents/ 2>/dev/null

# 也查脚本里的 --model / -c model=

rg -n -- "--model|-c[ =]model" . 2>/dev/null

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【2｜迁移映射（直接抄）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 已下线/将下线 → 推荐替代

gpt-5-codex        → gpt-5.6-sol  
gpt-5.1-codex      → gpt-5.6-sol  
gpt-5.1-codex-max  → gpt-5.6-sol  
gpt-5.1-codex-mini → gpt-5.6-terra  
gpt-5.2-codex      → gpt-5.6-sol  
gpt-5.4            → gpt-5.6-terra   # 仅 ChatGPT 登录态

# 官方弃用页仍写 gpt-5.5 / gpt-5.4-mini 作替代的属旧快照，以 gpt-5.6 家族为准

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【3｜config.toml 与 agent 文件里的正确写法】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ~/.codex/config.toml

model = "gpt-5.6-terra"        # 日常默认，中档省钱

# .codex/agents/implementer.toml

model = "gpt-5.6-sol"          # 复杂实现用前沿模型

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【4｜一键检测当前会话用哪个模型 + 是否可用】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
codex exec --json "回复你当前使用的模型 id，不要改文件" 2>/dev/null   
| jq -r 'select(.type == "turn.completed") | .model // empty' | tail -1

# 交互式里更简单：直接 /status 看活动模型

### 关键参数

| 参数                     | 官方默认值      | 一人公司推荐值                                                  | 说明              |
| ---------------------- | ---------- | -------------------------------------------------------- | --------------- |
| model（config.toml）     | 随登录态/发行渠道  | ★gpt-5.6-terra（日常）、gpt-5.6-sol（复杂/审查）                    | 别写已下线 ID        |
| 自定义 agent model        | 继承父会话      | ★explorer→gpt-5.6-terra/luna，worker/reviewer→gpt-5.6-sol | 分档省钱的落点         |
| 登录态（认证路径）              | ChatGPT 登录 | 日常 ChatGPT 登录；CI/批量用 API key                             | 决定弃用是否影响你、计费模式  |
| model_reasoning_effort | 官方未明文      | 常规 medium、CI low                                         | 弃用迁移时顺带核对，别带旧参数 |

必须改的一项：grep 出所有 gpt-5.4 / gpt-5.4-mini 与 2026-07-23 已下线的 codex 系列 ID，在 2026-08-31 前全部替换；这属于「不改会断」的硬项。

### 常见坑

1. 【弃用范围≠全局】gpt-5.4 的 08-31 下线只针对 Codex 的 ChatGPT 登录态，API key 用户不受影响；但 gpt-5.2 系列 API 侧早已 2026-06-30 sunset。别把「登录态弃用」当「API 弃用」，也别反过来。
2. 【官方弃用页旧快照】捕获到的 platform.openai.com/docs/deprecations 把 2026-07-23 的替代模型写成 gpt-5.5 / gpt-5.4-mini，那是 GPT-5.6 家族（2026-07-09 GA）之前的旧快照；当前替代应以 gpt-5.6-sol/terra/luna 为准。
3. 【文档在 ≠ 可调用】OpenAI 模型索引对多个已下线 ID 仍保留活文档页且无弃用横幅，别把「文档里搜得到」当成「还能调用」。
4. 【残留 ID 静默失败】gpt-5.4 写在 config.toml / 自定义 agent / 定时任务 / codex exec --model 里，08-31 后请求会报错。grep 是唯一可靠排查手段。
5. 【映射是起点不是结论】o4-mini→gpt-5.6-terra 是同级替代，但 gpt-4-0613→gpt-5.6-sol 跨三代，行为会变。迁移后要重新 eval，别只改字符串。
6. 【别名与快照分开】-chat-latest 别名按自己的节奏退役，与底层模型快照无关。生产钉 dated snapshot，开发才用 alias。
7. 【reasoning_effort 值域变化】gpt-5.3-codex 只接受 low/medium/high/xhigh，旧模型接受更窄值集；迁移时核对传参，否则静默变行为。
8. 【登录态锁定模型目录】ChatGPT 登录态只能用 OpenAI 目录（无法接第三方 provider）；要用 DeepSeek/Ollama 等必须切 API key/custom provider。

### 降级与回退路径

1. 发现已下线 ID：按映射表替换；gpt-5.4→gpt-5.6-terra、gpt-5.4-mini→gpt-5.6-luna、codex 旧系列→gpt-5.6-sol。
2. 迁移后行为不符预期：退一步做小范围 eval（同 prompt 对比新旧结果），必要时调 model_reasoning_effort 或回到上一稳定档。
3. 登录态拿不到新模型：切 API key 走 gpt-5.3-codex（$1.75/M 输入/$14/M 输出）等仍在 API 目录的模型兜底，或用 model_provider 接第三方（DeepSeek/GLM/Kimi）。
4. 想彻底绕开弃用节奏：用 API key + 自定义 provider 锁定第三方模型，把模型生命周期控制权拿回自己手里。
5. 分不清影响范围：先确认会话走哪条认证路径（codex login status / 看 auth 方式），再对照「登录态弃用」还是「API 弃用」清单。

### 版本与生效时间

2026-04-22 宣布两波弃用；2026-07-23 下线 codex 旧系列（gpt-5-codex 等 5 个 ID）；2026-08-31 下线 gpt-5.4 / gpt-5.4-mini（仅 ChatGPT 登录态）；gpt-5.2 系列 API sunset 2026-06-30；GPT-5.6 家族 2026-07-09 GA。

### 可自动化程度

高。模型 ID 排查是纯文本 grep，天然可脚本化，可挂进 CI 前置检查（rg 命中已下线 ID 即 fail）；迁移后可用 codex exec --json 抓实际使用的 model 字段做一致性校验。是三条目里最适合做成「无人值守守护」的。

### 优先级

P0（短期），P1（长期）。08-31 的 gpt-5.4 下线是「不改会断」的硬截止，必须立即 grep+替换；替换完成后降级为 P1 的例行维护（每周跑一次排查脚本）。

### 对一人公司的适用性

高。无同事 review → 没有第二个人提醒你模型下线了，只能靠 grep 脚本主动守护；成本敏感 → 迁移到 gpt-5.6-terra/luna 本身就是省钱（Luna $0.20/$1.20 较 Sol 便宜 20 倍），且登录态 vs API key 的切换是成本调节阀；异步杠杆 → 把排查脚本挂进 CI，睡前下单的定时任务里先跑模型体检，早上不会收到「model not found」的废单。唯一注意：一人公司没有冗余人力，务必在 08-31 前完成替换，避免「下单的任务因为模型下线而静默失败」。

### 信息来源

1. OpenAI 官方弃用页（shutdown 日期与替代模型）：<https://platform.openai.com/docs/deprecations>
2. OpenAI 官方 Codex 模型文档：<https://developers.openai.com/codex/models>
3. 登录态 vs API key 架构差异（后端/计费/模型访问/Cloud/Fast mode）：<https://codex.danielvaughan.com/2026/06/13/codex-cli-authentication-paths-chatgpt-login-api-key-billing-rate-limits-model-access>
4. 2026-07-23 与 08-31 两波 Codex 下线清单与迁移：<https://aitooltier.com/is-it-down/codex>
5. 弃用迁移清单与映射表：<https://www.developersdigest.tech/blog/migrating-off-retired-gpt-models-2026>
6. gpt-5.3-codex 弃用时间线核对：<https://chatforest.com/builders-log/gpt-5-3-codex-default-copilot-july-23-deprecations-builder-guide/>

### 待核实

- API key 侧 gpt-5.2 系列的 sunset 日期（一说 2026-06-30）与登录态下线的对应关系 [不确定]
- gpt-5.2 / gpt-5.3-codex 对 ChatGPT 登录态「已弃用」的准确 shutdown 日期 [不确定]
- gpt-5.4-mini 的推荐替代是 gpt-5.6-luna 还是 gpt-5.6-terra（多数源写 terra，aitooltier 写 luna）[不确定]
- 官方弃用页「替代模型」字段是否已从 gpt-5.5/gpt-5.4-mini 更新为 gpt-5.6-sol/terra/luna（捕获到的为旧快照）[不确定]

## 13. 国内环境适配

### 核心做法

核心矛盾只有一个：Codex 自 2026-02-01 起彻底移除 Chat Completions 支持，wire_api 只认 "responses"（Responses API），而国产模型 API 的主流仍是 Chat Completions。国内实测 chatgpt.com 与 api.openai.com 均超时不可达，api.deepseek.com 可达（约 137ms），所以「适配国内环境」=「让 Codex 的 Responses 请求落到一个能讲 Responses 协议的国产端点或网关」。

【三条路线，按优先级】  
① 路线 A：直连已原生支持 Responses API 的国产大厂。截至 2026-08，国产模型中只有 DeepSeek（deepseek-v4-flash，专为 Codex 实现了 Responses 协议）和 Qwen/通义（阿里云百炼 DashScope 的 /compatible-mode/v1/responses，支持 previous_response_id）原生支持 Responses。Kimi（Moonshot）与 GLM（智谱）目前只提供 Chat Completions，直连必 404。  
② 路线 B：自建翻译网关。当目标模型只讲 Chat Completions 时，在中间放一个「翻译官」，对外暴露 /v1/responses、对内转成各家的 Chat Completions。首选 LiteLLM（需 ≥1.66.3.dev5 才有完整 Responses 兼容），国产开源替代有 New API（v1.0.0-rc.24 起原生支持 /v1/responses 路由，但 Chat→Responses 转换仍标注「开发中」）、CLIProxyAPI、codex-cn-bridge 等单文件桥接器。  
③ 路线 C：本地跑开源模型（Ollama / LM Studio / llama.cpp），断网可用，但要求模型支持工具调用，且小模型易翻车。

【探活是第一步】不管哪条路线，先用 curl 探对方 /v1/responses 是否存在，再决定直连还是上网关——这一步省钱又省时间。

【provider 只能写在用户级配置】项目级 .codex/config.toml 不能覆盖 provider / auth / 通知 / telemetry / profile 选择（安全边界：clone 一个仓库不能把你的 prompt 和 key 静默重定向到别人的端点）。所以 [model_providers.*] 必须写在 ~/.codex/config.toml。

【接国产模型后失去的云端能力】ChatGPT 订阅态独占的云端并行任务（Triggers）、GitHub PR 自动 review、Slack 集成、生图与联网搜索等客户端能力，走第三方 provider 后都不可用——这些是订阅/云端能力，不是模型能力。

### 可直接复制的模板命令配置

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【0｜先探活：确认端点到底讲不讲 Responses】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
curl -s -X POST <https://api.deepseek.com/v1/responses>   
-H "Authorization: Bearer $DEEPSEEK_API_KEY"   
-H "Content-Type: application/json"   
-d '{"model":"deepseek-v4-flash","input":"hi","max_output_tokens":5}'

# 返回 200 + JSON = 直连可行；404/400 = 只实现了 chat 系，跳路线 B

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【1｜DeepSeek 直连（推荐，国产首选）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 官方一键脚本（自动备份旧配置、写 models.json、校验语法）

bash <(curl -fsSL <https://cdn.deepseek.com/api-docs/codex-deepseek-setup-en.sh>)

# 手动版 ~/.codex/config.toml

model = "deepseek-v4-flash"  
model_provider = "deepseek"  
preferred_auth_method = "apikey"  
forced_login_method = "api"  
model_reasoning_effort = "high"  
model_catalog_json = "~/.codex/models.json"

[model_providers.deepseek]  
name = "deepseek"  
base_url = "<https://api.deepseek.com/>"  
wire_api = "responses"  
experimental_bearer_token = "sk-你的DeepSeekAPIKey"

# 更规范的密钥写法（用环境变量，不落盘明文）

[model_providers.deepseek]  
name = "DeepSeek"  
base_url = "<https://api.deepseek.com/v1>"  
env_key = "DEEPSEEK_API_KEY"  
wire_api = "responses"  
requires_openai_auth = false  
request_max_retries = 3  
stream_max_retries = 3  
stream_idle_timeout_ms = 120000

# 调用

export DEEPSEEK_API_KEY="sk-你的key"  
codex exec "给这个 Python 脚本加上类型注解"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【2｜Qwen/通义 直连（DashScope 兼容模式）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
export DASHSCOPE_API_KEY="你的百炼Key"

# ~/.codex/config.toml

model = "qwen-plus"  
model_provider = "qwen"

[model_providers.qwen]  
name = "Qwen"  
base_url = "<https://dashscope.aliyuncs.com/compatible-mode/v1>"  
env_key = "DASHSCOPE_API_KEY"  
wire_api = "responses"  
requires_openai_auth = false

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【3｜LiteLLM 网关（Kimi / GLM / 任何只讲 chat 的模型）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 装：pip install "litellm[proxy]"

# ~/.codex-proxy/litellm_config.yaml

model_list:

- model_name: deepseek-chat  
  litellm_params:  
  model: deepseek/deepseek-chat  
  api_key: os.environ/DEEPSEEK_API_KEY
- model_name: kimi-k3  
  litellm_params:  
  model: moonshot/kimi-k3  
  api_key: os.environ/MOONSHOT_API_KEY
- model_name: glm-5.2  
  litellm_params:  
  model: zai/glm-5.2  
  api_key: os.environ/ZAI_API_KEY
- model_name: qwen-plus  
  litellm_params:  
  model: qwen/qwen-plus  
  api_key: os.environ/DASHSCOPE_API_KEY  
  general_settings:  
  master_key: sk-local-codex

# 启动：litellm --config litellm_config.yaml --port 4000

# Codex 侧 ~/.codex/config.toml

model = "deepseek-chat"  
model_provider = "litellm"

[model_providers.litellm]  
name = "LiteLLM"  
base_url = "<http://127.0.0.1:4000/v1>"  
env_key = "LITELLM_API_KEY"  
wire_api = "responses"  
requires_openai_auth = false

export LITELLM_API_KEY="sk-local-codex"  
codex

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【4｜New API 网关（国产，原生 /v1/responses 路由）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
docker run --name new-api -d --restart always   
-p 3000:3000 -e TZ=Asia/Shanghai -v ./data:/data   
calciumion/new-api:latest

# 初始账号 root/123456，改密码→建渠道→建令牌 sk-xxx

# Codex 侧

model_provider = "custom"  
model = "deepseek-chat"  
model_reasoning_effort = "high"  
disable_response_storage = true

[model_providers.custom]  
name = "custom"  
base_url = "<http://你的IP:3000/v1>"  
wire_api = "responses"  
requires_openai_auth = false

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【5｜纯环境变量法（聚合网关 / 中转，最省事）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
export OPENAI_BASE_URL="<http://127.0.0.1:4000/v1>"   # 新版 Codex 认这个  
export OPENAI_API_BASE="$OPENAI_BASE_URL"           # 旧版(≤0.16)认这个，两个都设  
export OPENAI_API_KEY="sk-你的网关key"  
codex

### 关键参数

| 参数                                                                | 官方默认值              | 一人公司推荐值                                                                                                                              | 说明                                            |
| ----------------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------- |
| wire_api                                                          | "responses"（省略即默认） | ★必须 "responses"                                                                                                                      | 2026-02 起唯一合法值，写 "chat" 直接硬报错                 |
| model_provider                                                    | openai（内置）         | deepseek / qwen / litellm                                                                                                            | ★必须改；且只能写在用户级 ~/.codex/config.toml            |
| base_url                                                          | api.openai.com/v1  | DeepSeek: <https://api.deepseek.com（或> /v1）；Qwen: <https://dashscope.aliyuncs.com/compatible-mode/v1；网关>: <http://127.0.0.1:4000/v1> | ★必须改；写到 OpenAI 兼容根路径，网关场景末尾带 /v1              |
| model                                                             | gpt-5.x            | deepseek-v4-flash（日常）/ qwen-plus                                                                                                     | 以对方 GET /v1/models 返回为准                       |
| model_reasoning_effort                                            | 未明文                | DeepSeek: low/high/max（默认 high）                                                                                                      | ★按模型支持值域填；Kimi/GLM/Qwen 部分模型 reasoning 是开关非档位 |
| env_key                                                           | 无                  | DEEPSEEK_API_KEY / DASHSCOPE_API_KEY / LITELLM_API_KEY                                                                               | 推荐用环境变量，替代 experimental_bearer_token 明文       |
| experimental_bearer_token                                         | 无                  | 不推荐（明文落盘）                                                                                                                            | 内联 key，DeepSeek 官方脚本用这个                       |
| requires_openai_auth                                              | false              | false                                                                                                                                | 走第三方必须 false，否则去要 ChatGPT 登录态                 |
| request_max_retries / stream_max_retries / stream_idle_timeout_ms | 4 / 5 / 300000     | 3 / 3 / 120000（国内网络可调大 idle）                                                                                                         | 国产端点抖动时调大 stream_idle_timeout_ms              |
| model_catalog_json                                                | 无                  | ~/.codex/models.json（DeepSeek 官方脚本生成）                                                                                                | 声明上下文窗口/推理档位，缺了模型能力不完整                        |

必须改的四项：① wire_api="responses"（不写默认也对，但别写 chat）；② model_provider 指向你的 provider 并写在用户级配置；③ base_url 换成国产端点/网关（带对 /v1）；④ requires_openai_auth=false。

### 常见坑

1. 【wire_api 写错层级】wire_api 必须写在 [model_providers.x] 里，不是 [profiles.x]。写错位置直接不生效，报 404。
2. 【误以为还能 wire_api="chat"】2026-02 起写 "chat" 会硬报错「wire_api = "chat" is no longer supported」。大量 2025 年的旧教程还在教你写 chat，照抄必翻车（ofox.ai 甚至到 2026-06 还在教错的）。
3. 【Kimi / GLM 直连必 404】这两家目前只提供 Chat Completions，没有 /v1/responses 端点。curl 探 /v1/chat/completions 通、但 Codex 打 /v1/responses 404，就是协议不匹配，不是网络问题。
4. 【base_url 漏写 /v1 或多写尾斜杠】网关/中转的路由前缀通常是 /v1，漏写直接 404；DeepSeek 官方脚本写 <https://api.deepseek.com/（带尾斜杠），规范写法是> <https://api.deepseek.com/v1，两者都能通但别混。>
5. 【reasoning 型号 + 工具调用冲突】deepseek-reasoner 这类纯推理型号与 Codex 的 function 工具调用配合易出问题，跑代码任务优先用非推理型号（deepseek-v4-flash）。
6. 【模型名不在白名单，启动崩】自定义 provider 的 model 名要精确匹配（OpenRouter 要带前缀如 openai/gpt-5.3-codex），先跑 /v1/models 或 --list-models 核对。
7. 【ChatGPT 登录态锁定模型目录】登录态只能用 OpenAI 目录，接不了第三方；要用国产模型必须切 API key 方式（preferred_auth_method="apikey" + forced_login_method="api"）。
8. 【协议翻译有损】Chat→Responses 转换「能跑起来」但翻译不出加密推理条目、服务端内置工具、previous_response_id；New API 的 Chat→Responses 转换还标注「开发中」，上游能给原生 responses 就别绕转换。
9. 【云端能力静默消失】接第三方后生图、联网搜索、云端并行任务、GitHub PR review、Slack 集成都没了，且无报错——是客户端能力不加载，不是配置错。
10. 【切 provider 后必须重启终端】Codex 不是热切换，改完 config.toml / model_catalog_json 要关掉重开才生效。

### 降级与回退路径

1. 直连 DeepSeek 报 404：先 curl 探 /v1/responses；若只支持 chat，改走路线 B 网关（LiteLLM / New API / CLIProxyAPI）。
2. 网关也搞不定：退到本地 Ollama 跑 qwen 系开源模型（需支持工具调用，升级 Ollama 以支持 responses）。
3. 国内网络抖动/超时：调大 stream_idle_timeout_ms（300000→更大）、stream_max_retries，或换 OpenRouter 这类海外聚合中转做兜底。
4. 需要回 OpenAI：临时 codex -m gpt-5.6-sol 或 codex -c model_provider=openai 单次切回，不必改文件。
5. 彻底绕开协议风险：用 API key + 自定义 provider 锁定 DeepSeek（原生 responses），把协议兼容性交给厂商而不是自己维护网关。
6. 配置写坏了回滚：DeepSeek 官方脚本会备份旧配置到 ~/.codex/backup-deepseek/；CC Switch 会在 ~/.cc-switch/backups/ 留最近 10 份。

### 版本与生效时间

2025-12-09 Codex 官方宣布弃用 Chat Completions（讨论 #7782）；2026-02-01 彻底移除（PR #10157，wire_api="chat" 转硬报错）；DeepSeek V4-Flash 2026-07-31 原生支持 Responses API 并全面适配 Codex（V4-Pro 预计 2026-08 初支持）；New API v1.0.0-rc.24（2026-08-07）原生支持 /v1/responses 路由；LiteLLM 需 ≥1.66.3.dev5 才有完整 Responses 兼容。

### 可自动化程度

高。provider 配置与密钥都固化在 ~/.codex/config.toml + 环境变量后，codex exec --json 在 CI/定时任务里可无人值守跑国产模型；网关（LiteLLM/New API）可作为常驻本地服务开机自启。唯一人工项是首次探活与写配置，之后全自动。

### 优先级

P0。对国内一人公司这是「不做就没得用」的硬前置——chatgpt.com 与 api.openai.com 均超时不可达，不完成适配 Codex 直接打不开。必须先于所有其他条目落地。

### 对一人公司的适用性

极高，是国内一人公司的唯一解。无同事 review → 没有第二个人帮你调协议，所以优先选「厂商原生支持 responses」的 DeepSeek 直连，把调试协议的时间省下来写业务；成本敏感 → DeepSeek V4-Flash 输出约 $0.28/M，比 GPT-5.6 系列便宜一到两个数量级，且国内直连低延迟；异步杠杆 → 配置固化后可 codex exec 睡前下单、早上收结果。唯一要权衡的：接国产模型即放弃云端并行任务/GitHub PR review/Slack 集成，对依赖这些异步杠杆的场景要单独留一个 ChatGPT 订阅兜底。

### 信息来源

1. DeepSeek 官方 Responses API 文档（兼容性矩阵）：<https://api-docs.deepseek.com/zh-cn/guides/responses_api>
2. DeepSeek 官方「接入 Codex」一键脚本：<https://cdn.deepseek.com/api-docs/codex-deepseek-setup-en.sh>
3. Codex 官方弃用 Chat Completions 讨论：#7782 <https://github.com/openai/codex/discussions/7782>
4. wire_api 移除溯源与第三方 provider 实测：<https://www.alexdunlop.com/writing/codex-cli-config-toml>
5. Codex config.toml 第三方 provider 参考（项目配置不能覆盖 provider 的安全边界）：<https://www.morphllm.com/codex-provider-configuration>
6. LiteLLM 网关接入 Codex（版本要求 1.66.3.dev5+）：<https://codex.danielvaughan.com/2026/04/21/codex-cli-ai-gateway-multi-provider-routing-cost-control-failover>
7. New API 原生 /v1/responses 与 CC Switch 实测：<https://colobu.com/2026/05/20/cliproxyapi-codex-support-domestic-models>
8. 国产模型协议兼容全景（Responses 支持现状表）：<https://www.hqwc.cn/a/406695.html>

### 待核实

- DeepSeek V4-Pro 的 Responses API 支持具体 GA 日期（官方说 2026-08 初，但确切上线日未核实）[不确定]
- Kimi / GLM 是否有官方 Responses API 支持路线图或已上线（截至 2026-08 检索结果均为「不支持」，但厂商迭代快，可能已跟进）[不确定]
- New API 的 Chat→Responses 转换功能当前成熟度（README 标注「开发中」，issue #6075 记录过失败，是否已稳定未核实）[不确定]
- Qwen DashScope 的 /compatible-mode/v1/responses 与 Codex 实际兼容度（支持 previous_response_id，但工具调用/推理条目完整度未逐一验证）[不确定]
- 接第三方 provider 后具体损失哪些客户端能力的官方清单（生图/联网搜索丢失来自逆向分析，OpenAI 未公开确认）[不确定]

## 14. 任务模板库与 Skills 打包

### 核心做法

把「反复干的活」沉淀成两类资产：一类是可复用的任务 prompt 模板（补测试/重构/迁移/PR review/批量修 bug），一类是可打包分发的 Skill（SKILL.md）与 Agent Plugin。分层的判断标准是——10 个词能稳定搞定的写进 /command 或 prompt 模板即可；需要文件上下文、工具调用、多步逻辑的写成 SKILL.md；要跨仓库复用、给团队装、绑 MCP 的才升级成 Plugin。

【任务模板的统一骨架：四要素】官方 best practices 推荐的 prompt 结构只有四段——Goal（要改变什么）、Context（哪些文件/文档/报错，用 @ 引用）、Constraints（规范/架构/安全/不要碰什么）、Done when（什么测试过了、什么行为变了才算完）。所有模板都套这个骨架。

【Skill 的运行机制：渐进式披露】Codex 启动时不会把 Skill 正文塞进上下文，先只读 name + description，任务匹配上才加载完整 SKILL.md，需要时才读 references/ 或跑 scripts/。所以 description 决定 Skill 何时被触发——要写成「触发条件」而不是「标题」。

【Skill 目录结构】核心只有 SKILL.md 必需，里面写清 Goal、Workflow、Safety 段（不许 push、不许发布、不许改生产、不许暴露 secret）。可选 scripts/、references/、assets/。位置：单仓库用 .agents/skills/<name>/SKILL.md；跨仓库/分发用 Plugin。

【Agent Plugins 1.0（v0.147.0 引入）】用 plugin.json manifest 把多个 Skill + MCP server 配置 + app 打包成一个可安装单元。目录：~/.agents/plugins/<name>/plugin.json + skills/*/SKILL.md + mcp.json（或 .codex-plugin/plugin.json 官方格式）。

【自定义 agent 分档】补测试、审查类任务可下沉到 .codex/agents/*.toml（name/description/developer_instructions/model/sandbox_mode），explorer 用便宜模型、reviewer 用贵模型。

### 可直接复制的模板命令配置

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【1｜五个任务 prompt 模板（套四要素骨架）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ① 补测试

Goal: 为 src/utils/money.ts 补全单元测试。  
Context: @src/utils/money.ts, @vitest.config.ts, 现有测试在 test/money.test.ts  
Constraints: 复用现有测试风格；不要改生产代码；覆盖率提到 85% 以上。  
Done when: pnpm test money 全绿，且 coverage 报告里该文件分支覆盖 ≥85%。

# ② 重构

/plan 把 Dashboard 组件重构为 React Hooks。保留所有现有测试。对抽取出的组件补新测试。  
Done when: pnpm test 通过，每个函数圈复杂度不增加，公开 API 不变。

# ③ 迁移

Goal: 把 Express 的 user router 迁移到 Hono。  
Context: src/routes/user.ts、middleware/auth.ts、test/user.test.ts  
Constraints: 不引入新依赖大版本跳；公开 API 与响应格式不变。  
Done when: pnpm test 全绿 + 手动 curl /users/:id 返回原结构。

# ④ PR review（只读，不 merge）

/review 重点看：鉴权绕过、XSS/SQL 注入、错误处理是否完整、是否影响公开 API、是否缺关键路径测试。只输出高危问题与建议修复位置，不要改代码。

# ⑤ 批量修 bug

codex exec --sandbox workspace-write "逐个修复 test 目录下失败的用例：先跑 pnpm test 拿失败清单，再每个失败用例最小改动修复，改完重跑对应用例确认转绿，最后汇总：根因/改动文件/验证结果"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【2｜SKILL.md 最小模板（放 .agents/skills/test-gen/SKILL.md）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
----------------------------

name: test-gen  
description: 为改动或指定模块生成单元测试。触发条件：用户要补测试、提覆盖率、写单测；不要用于改生产代码。
-----------------------------------------------------------

## Goal

为指定文件生成风格一致、可运行的单元测试。

## Workflow

1. 先读目标文件与现有测试，确认测试框架与命名风格。
2. 列出要覆盖的关键分支与边界用例。
3. 写测试，复用已有 fixture/mock。
4. 运行对应测试命令，失败则修正到转绿。

## Safety

- 不改生产代码。
- 不引入新依赖。
- 不覆盖或删除现有测试。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【3｜自定义 agent（审查用，放 .codex/agents/security-reviewer.toml）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
name = "security-reviewer"  
description = "审查代码变更中的安全漏洞"  
developer_instructions = """  
你是安全向代码审查者，分析变更中的：SQL 注入/XSS/CSRF、代码里的密钥、不安全依赖、缺失的输入校验。  
按严重程度输出结构化清单并标注文件位置，不要改代码。  
"""  
model = "gpt-5.6-sol"  
sandbox_mode = "read-only"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【4｜Plugin 打包（~/.agents/plugins/my-plugin/）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# plugin.json

{  
"name": "my-codex-toolkit",  
"version": "1.0.0",  
"description": "补测试、lint 修复、PR 审查的一体化技能包",  
"components": {  
"skills": ["skills/test-gen", "skills/lint-fix"],  
"mcp_servers": ["mcp.json"]  
},  
"install_policy": "AVAILABLE"  
}

# 目录树

my-plugin/  
├── plugin.json  
├── skills/  
│   ├── test-gen/SKILL.md  
│   └── lint-fix/SKILL.md  
└── mcp.json

# 建本地 marketplace 并用 CLI 添加

# marketplace.json（plugins[] 指向各 plugin 文件夹，source.path 用 ./- 相对路径）

codex plugin marketplace add ./local-marketplace-root  
codex plugin marketplace list

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【5｜config.toml 里的 Skill 开关】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
[skills]  
test-gen = true  
legacy-deploy = false

[skills.code-review]  
enabled = true  
invocation = "implicit"   # explicit=只能 $skill-name 手动触发  
priority = 5

[plugins]  
my-codex-toolkit = true

### 关键参数

| 参数                    | 官方默认值                                        | 一人公司推荐值                            | 说明                                              |
| --------------------- | -------------------------------------------- | ---------------------------------- | ----------------------------------------------- |
| prompt 骨架             | Goal/Context/Constraints/Done when 四要素       | 五个模板全部套四要素                         | 官方 best practices 推荐，缺 Done when 是最大反模式         |
| Skill 位置              | .agents/skills/（仓库级）/ ~/.agents/skills/（个人级） | 先放仓库 .agents/skills/ 验证，再考虑 Plugin | ★单仓库别过早 Plugin 化                                |
| SKILL.md description  | 必填，触发条件                                      | 写「什么时候用/什么时候不用」的判定句                | ★决定渐进式披露是否命中                                    |
| [skills.x].invocation | implicit（隐式自动触发）                             | 高风险 Skill 设 explicit               | explicit 只能 $skill-name 手动触发                    |
| [skills.x].priority   | 无                                            | 冲突时给高分                             | 多个 Skill 同时命中时高者胜                               |
| install_policy        | INSTALLED_BY_DEFAULT                         | AVAILABLE（装后手动启用）                  | 可选 INSTALLED_BY_DEFAULT/AVAILABLE/NOT_AVAILABLE |
| agent model 分档        | 继承父会话                                        | explorer→便宜、reviewer→贵             | 审查/重构用 gpt-5.6-sol，探索/补测试用 terra/luna           |
| agents.max_threads    | 6                                            | 6（保持默认）                            | 批量修 bug 的并行上限                                   |

必须改的一项：SKILL.md 的 description 必须写成触发条件（含「不要用于 X」），否则模型要么不触发、要么误触发；这是 Skill 好用与否的分水岭。

### 常见坑

1. 【过早 Plugin 化】一个 20 行说明、只在一个仓库用的流程，先放 .agents/skills/<name>/SKILL.md 一个文件就够。上 Plugin 是为「跨仓库复用 + 团队安装 + 绑 MCP」，别一上来就打包。
2. 【description 写成标题】写「Repository helper」这种模糊描述，模型不知道何时用；正确写法是「分析陌生仓库、梳理架构…；不要用于实现功能」。
3. 【SKILL.md 正文堆进上下文】Skill 靠渐进式披露省 token，把流程硬写进 AGENTS.md 或每次 prompt 会烧钱；把长流程放进 references/ 让模型需要时才读。
4. 【把 Skill 文本当权限边界】Skill 里写「Never delete production data」只是模型指令，不是安全层。真正的边界在 MCP 授权、Tool 白名单、审批策略、沙箱、后端 RBAC。
5. 【装插件 ≠ 信任它的 Hook】官方明确：插件捆绑的 Hook 属于 non-managed hooks，装了也不会被自动信任，Codex 会跳过直到用户审查。别设计成「装插件→自动跑未知脚本」。
6. 【Secret 写进插件】真实 Token 交给环境变量/OAuth/Secret Manager，别写进 plugin.json、.mcp.json 或 Git。
7. 【批量修 bug 一把梭】老项目别让 AI 直接改，拆成「理解现状→识别风险→迁移计划→分批执行」四层；先只读找根因，确认方向再写入，返工率明显下降。
8. 【Skill 触发了但没效果】模型不一定会跑 scripts/，Skill 的 Workflow 要写成明确的、可验证的步骤，别只给意图。
9. 【version 漂移】Agent Plugins 1.0 是 v0.147.0 才引入，旧版本 CLI 认不出 plugin.json；确认 CLI 版本再打包分发。

### 降级与回退路径

1. Skill 不触发：把 description 改成更明确的触发条件，或临时用 $skill-name 强制加载定位。
2. 跨仓库要复用但不想做 Plugin：直接把 .agents/skills/<name>/ 目录连同 SKILL.md 复制到目标仓库即可，Skill 本质是目录。
3. 装依赖/跑测试的 Skill 不可靠：退化为「report-first」风格（先只读审查、输出计划、请求批准再改），不追求全自动。
4. Plugin 装不上/版本不认：降级为手动复制 skills 目录 + 在 config.toml 手配 MCP，绕开 plugin.json。
5. 模板没沉淀下来：用 AGENTS.md 的 if/then 规则强制触发（如「改动 SDK 代码前先调 $implementation-strategy」），把模板从「可选」变「必跑」。

### 版本与生效时间

Skills（SKILL.md + 渐进式披露）2025 起持续演进；$skill-creator / $skill-installer 内置技能随 CLI 周更；Agent Plugins 1.0 于 v0.147.0（2026-08-07）引入，用 plugin.json 打包 Skill + MCP；官方 .codex-plugin/plugin.json 与 marketplace.json 为当前分发标准；官方 Skills 最佳实践案例（Agents SDK 仓库）发布于 2026-03。

### 可自动化程度

高。模板可直接喂给 codex exec --json 在 CI 里跑（批量修 bug、补测试、PR review 都能无人值守）；Skill 靠 AGENTS.md 的 if/then 规则做到「到点必跑」；Plugin 装一次后续即自动加载。唯一保留人工的是高风险动作（部署/删除/发布）需 Gate。

### 优先级

P1。不是「不做就断」的硬前置（P0 是国内适配和 config），但它是把 Codex 从「玩具」变「产能」的关键杠杆——模板与 Skill 是异步批量任务的前提，一人公司没有团队分摊，靠模板复用才能放大杠杆。

### 对一人公司的适用性

极高。无同事 review → PR review 模板 + security-reviewer 代理就是你的「虚拟同事」，补上没人给你审代码的缺口；成本敏感 → 模板骨架固定了 Done when，减少来回返工烧 token，Skill 渐进式披露避免每次把长流程塞进上下文；异步杠杆 → 批量修 bug/补测试模板可直接 codex exec 睡前下单，早上收结果。唯一注意：一人公司没人力维护复杂 Plugin，优先用「单文件 SKILL.md」起步，确有跨仓库复用再打包。

### 信息来源

1. OpenAI 官方 best practices（四要素 prompt、AGENTS.md、Skills）：<https://developers.openai.com/codex/learn/best-practices>
2. OpenAI 官方 Skills 最佳实践（Agents SDK 仓库，SKILL.md 目录与 if/then 规则）：<https://developers.openai.com/blog/skills-agents-sdk>
3. OpenAI 官方 Plugin 打包（.codex-plugin/plugin.json、marketplace.json、codex plugin marketplace add）：<https://developers.openai.com/codex/plugins/build>
4. Codex 定制栈五层体系（AGENTS.md/Skills/MCP/Subagents/Plugins）：<https://codex.danielvaughan.com/2026/04/12/codex-cli-customisation-stack-unified-system>
5. Prompt 模板与工作流（Bug Fix/Feature/Review/Refactor）：<https://codex.danielvaughan.com/2026/05/21/codex-cli-prompt-engineering-outcome-first-patterns-gpt55-senior-developer-workflows>
6. Skills & Plugins 结构（agents/openai.yaml、config.toml [skills]）：<https://opentools.ai/resources/codex-skills-and-plugins>

### 待核实

- Agent Plugins 1.0 的 plugin.json 具体字段全集与官方 .codex-plugin/plugin.json 的字段差异（社区 plugin.json 与官方格式可能不完全一致，未逐一核对官方 schema）[不确定]
- SKILL.md frontmatter 的完整合法字段（name/description 之外是否还有 version/license 等，未在官方 schema 核实）[不确定]
- agents/openai.yaml 的 policy 字段（require_confirmation/file_scope/max_execution_time）是否为官方稳定字段，还是第三方（opentools）整理 [不确定]
- install_policy 三档（INSTALLED_BY_DEFAULT/AVAILABLE/NOT_AVAILABLE）在本地 marketplace 场景的实际生效差异 [不确定]
- 批量修 bug 的「数小时修复周期」量化效果来自二手资料，无 OpenAI 官方基准数据 [不确定]

## 15. 故障排查

### 核心做法

Codex 报错九成来自「登录、额度、网络、权限」四件事，先按万能排查顺序走一遍：① 重试一次（网络抖动的错重试能解决一半）→ ② 重新登录（token 失效是第二大来源）→ ③ 看额度（额度耗尽也会表现为任务失败）→ ④ 看配置（自定义端点/模型名错的 404）→ ⑤ 升级版本（版本 bug 的兜底）。多数问题在第 ③ 步之前就解决。

【按症状定位，别盲目换模型】不同状态码指向完全不同的问题：401=Key 没读到或无效；404=base_url 拼错或接口不支持 Responses；429=超频或额度用尽；stream disconnected=SSE 被中断/代理超时/上游波动；「能聊天但从不改文件」=模型不支持工具调用。最浪费时间的行为是「明明是协议问题，却不停换更贵的模型」。

【四类核心故障的定位法】  
① 连接失败：先 curl 直接打对方端点验证网络与 key，再查 Codex 配置。401 排查顺序——echo $KEY 看变量是否导出、curl 测 key 是否有效、确认没有同时定义 env_key 和 [auth] 表（两者互斥）。  
② wire_api 协议不匹配（404 或空流）：Codex 只讲 Responses API，base_url 背后的端点若只实现 Chat Completions，就会 404/unknown endpoint/开局空流。判据是「curl /v1/chat/completions 能通、Codex 却失败」。解法：换支持 Responses 的端点，或加翻译网关（LiteLLM/New API）。  
③ 额度耗尽（429）：分两种——请求超频（rate limit exceeded，等一分钟降频）和限额用尽（quota exhausted / token-plan 1-week quota has been exhausted，等 7 天窗口重置或买用量包）。429 响应没有 retryAfterSeconds 说明只是瞬时预算空，退避一秒即可；固定间隔重试反而会延长限流。  
④ tool calling 不支持：模型「能连上、能聊天、但从不编辑文件」，因为它不实现 OpenAI 工具调用规范。换支持工具调用的模型（DeepSeek V4、Qwen3.5 coder 系、MiniMax M3 均支持）。

【Appshots 与锁定态计算机使用】这是 Codex 桌面端（macOS）的 GUI 能力，与 CLI 排查无关但易踩坑：Appshots 用「双 Command 键」抓取任意应用窗口的截图+文字进对话；锁定态计算机使用（Locked Computer Use）让 Codex 在 Mac 锁屏后仍能操作预授权应用。两者都需要在系统设置里授予「屏幕录制 + 辅助功能」权限，锁定态还需安装 Apple 授权插件。

### 可直接复制的模板命令配置

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【1｜探活：区分网络问题还是协议问题】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 网络+key 是否通

curl -s <https://api.deepseek.com/models> -H "Authorization: Bearer $DEEPSEEK_API_KEY"

# 协议是否支持 Responses（返回 200 JSON=支持；404=只支持 chat）

curl -s -X POST <https://api.deepseek.com/v1/responses>   
-H "Authorization: Bearer $DEEPSEEK_API_KEY"   
-H "Content-Type: application/json"   
-d '{"model":"deepseek-v4-flash","input":"hi","max_output_tokens":5}'

# 对照：chat 端点能通但 responses 404 = 协议不匹配

━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【2｜排查 401：key 有没有被读到】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
echo $DEEPSEEK_API_KEY          # 空行=变量没导出，就是问题

# 确认导出写进了 ~/.zshrc 而不是 ~/.bashrc，且变量名与 env_key 完全一致

source ~/.zshrc  
codex logout                     # 清掉残留 ChatGPT 会话，避免误走登录态

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【3｜排查 404：base_url 与模型名】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 正确（带 /v1）；错误：漏 /v1 或重复 /v1

# base_url = "<https://api.deepseek.com/v1>"

curl -s <https://api.deepseek.com/v1/models> -H "Authorization: Bearer $DEEPSEEK_API_KEY" | grep -o '"id":"[^"]*"'   # 核对真实模型名

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【4｜流中断/大模型慢：调超时与重试】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
[model_providers.ollama]  
name = "Ollama"  
base_url = "<http://localhost:11434/v1>"  
stream_idle_timeout_ms = 600000   # 默认 300000(5分钟)，大模型首 token 前超时就调大  
request_max_retries = 2  
stream_max_retries = 5

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【5｜确认 Codex 实际用哪个模型/端点】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
/status                        # 会话内看解析后的 model 与 base_url（权威）  
tail -f ~/.codex/log/*.log     # 看发出的 /v1/responses 调用

# 不可靠：问模型「你是什么模型」——它看不到你的配置，只会说通用家族名

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【6｜额度耗尽（429）退避】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 读 Retry-After 头做指数退避，别固定间隔重试

# 有 retryAfterSeconds=按提示等；没有=瞬时预算空，退避 1 秒即可

# 重置时间多为 UTC，换算北京时间需 +8 小时

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
【7｜Appshots 与锁定态授权（macOS）】  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 系统设置→隐私与安全性：为 Codex 客户端勾选「屏幕录制」+「辅助功能」

# 锁定态：设置→Computer Use→按引导安装 Apple 授权插件；逐个 App 授权，

# 敏感 App 别点「Always allow」；检测到本地键鼠输入会自动暂停并重新锁屏

### 关键参数

| 参数                        | 官方默认值             | 一人公司推荐值                | 说明                                                    |
| ------------------------- | ----------------- | ---------------------- | ----------------------------------------------------- |
| stream_idle_timeout_ms    | 300000（5 分钟）      | 本地大模型 600000；云端 300000 | 首 token 前超时→stream disconnected，调大解决                  |
| request_max_retries       | 4                 | 2-4                    | 瞬时 5xx 重试次数                                           |
| stream_max_retries        | 5                 | 5-10                   | SSE 重连次数，网络差可调大                                       |
| env_key                   | 无                 | 写「变量名」而非 key 本身        | ★写错成 key 会让 Codex 找错变量、掉到登录页                          |
| base_url                  | api.openai.com/v1 | 带 /v1，不带多余尾斜杠          | ★漏/重复 /v1 直接 404                                      |
| experimental_bearer_token | 无                 | 与 env_key 二选一，别同时定义    | 两者（及 [auth] 表）互斥                                      |
| model                     | 内置默认              | 与网关/厂商真实模型名精确一致        | model not found 多因拼写或缺前缀（如 openrouter 需 vendor/model） |
| 429 退避                    | Retry-After/指数退避  | 读 Retry-After，别固定间隔    | 固定间隔重试会延长限流                                           |

必须改的一项：env_key 填的是环境变量「名字」，不是 key 的「值」——这是第三方接入 401 的头号原因。

### 常见坑

1. 【env_key 写成 key 本身】env_key = "DEEPSEEK_API_KEY" 是对的，写成 "sk-xxx" 会让 Codex 去找一个叫 sk-xxx 的变量、找不到就掉到登录页或 401。
2. 【同时定义 env_key 和 experimental_bearer_token / [auth]】官方明确互斥，只能选一个，混用行为未定义。
3. 【TOML 用成 JSON / 智能引号】config.toml 是 TOML 不是 JSON；弯引号（smart quotes）会破坏解析，报「key with no value, expected =」。
4. 【base_url 漏 /v1 或重复 /v1】网关/OpenAI 兼容端点路由前缀是 /v1，漏写 404；DeepSeek 官方脚本写 <https://api.deepseek.com/> 带尾斜杠，规范是 /v1，两者能通但别混。
5. 【把「协议不匹配」当「网络不通」】curl /v1/chat/completions 通、Codex 却 404/空流，是端点只支持 Chat Completions，不是网络问题，换更贵模型没用。
6. 【model not found ≠ 模型坏了】OpenRouter 要带前缀（openai/gpt-5.3-codex）、Ollama 用本地 tag、OpenAI 用裸 ID，同一个 ID 换个 provider 就 404。
7. 【能聊天但从不改文件】模型不支持工具调用，只会用散文回答。选实现 OpenAI 工具规范的模型（DeepSeek V4 / Qwen3.5 coder / MiniMax M3）。
8. 【登录态残留导致走错 provider】改完 config 还走 OpenAI 默认模型（/status 显示 gpt-5.6-sol），先 codex logout 清掉 ChatGPT 会话，再确认 launch alias 生效。
9. 【固定间隔狂重试】429 时固定 1 秒重试每次都落在惩罚窗口里，越重试越糟；读 Retry-After 做指数退避。
10. 【锁定态计算机使用的授权误区】锁定态不是「远程解锁电脑」——只在活跃的受信任 computer-use turn 内、短时授权窗口内有效，检测到本地键鼠输入就自动重锁；且不能自动化终端、Codex 自身、管理员权限弹窗。

### 降级与回退路径

1. 连接失败：重试→重新登录（codex logout 后重登）→查额度→查配置→升级/回退 CLI 版本。
2. 协议不匹配 404：换支持 Responses 的端点（DeepSeek/Qwen），或加 LiteLLM/New API 翻译网关。
3. 额度耗尽：等窗口重置（7 天/5 小时），或买用量包/降频，或临时切到便宜的第三方 provider（DeepSeek $0.28/M 输出）兜底。
4. 模型不支持工具调用：换成支持工具规范的模型；本地小模型翻车就升级 Ollama 或换 qwen3.5-coder 系。
5. 流持续断：调大 stream_idle_timeout_ms、stream_max_retries，关 VPN/代理重试，或开新对话线程避免上下文过长触发压缩失败。
6. 配置写坏：保留一份「最小可运行 config.toml」备份，出问题先用最小配置验证，快速区分是 Codex 自身问题还是第三方配置问题。

### 版本与生效时间

wire_api="chat" 于 2026-02-01 彻底移除（硬报错）；Appshots、Goal Mode、锁定态计算机使用于 2026-05-21/22 随桌面端更新发布（锁定态仅 macOS，且 EU/UK/瑞士首发不可用）；stream 超时/重试参数（request_max_retries/stream_max_retries/stream_idle_timeout_ms）随 model_providers 配置演进，默认值以官方 config 参考为准。

### 可自动化程度

中。探活（curl /v1/responses）、key 校验、/v1/models 模型名核对都能脚本化并挂进 CI 前置检查；但登录态失效、额度窗口、GUI 授权（屏幕录制/辅助功能）仍需人工。codex exec --json 的报错事件可被日志采集，但定位根因仍靠人工对照这份清单。

### 优先级

P1。它不是「不做就断」的地基（P0 是国内适配+config），而是「出事时救命的消防手册」。平时低频，一旦遇到 401/404/断流/额度耗尽，能省下一人公司整晚的瞎折腾时间，价值体现在关键时刻。

### 对一人公司的适用性

高。无同事 review → 没有第二个人帮你盯着报错，这份按症状定位的清单就是你的「救火队友」；成本敏感 → 区分「网络问题 vs 协议问题 vs 模型能力问题」能避免最贵的错误——因为协议不匹配而反复换更贵的模型白烧钱；异步杠杆 → 睡前下单的 codex exec 任务最容易在无人值守时死于 429/断流，把这些排障探活脚本挂进任务前置检查，早上才不会收到一堆废单。

### 信息来源

1. 官方第三方 provider 排障（401/404/model not found/断流/tool calling）：<https://www.morphllm.com/codex-provider-configuration>
2. 报错症状→原因→处理与万能排查顺序：<https://www.ai-indeed.com/encyclopedia/30160.html>
3. 401/404/断流分型排查与 /status 权威确认：<https://uit.stanford.edu/service/ai-api-gateway/userguide/openai-codex-cli-setup>
4. 阿里云百炼 Codex 排障（stream disconnected/429 两种情形的官方口径）：<https://www.alibabacloud.com/help/zh/model-studio/codex-token-plan>
5. Appshots 与锁定态计算机使用（权限、Apple 授权插件、限制）：<https://www.creativeainews.com/blog/openai-codex-computer-use-mac-locked-2026>
6. 2026-05-21 Codex 更新（AppShots/Goal Mode/locked computer use）：<https://www.aipedia.wiki/news/2026-05-21-openai-codex-appshots-goal-mode-locked-computer-use>

### 待核实

- 429 两种情形（rate limit vs quota exhausted）在 ChatGPT 登录态下的具体重试窗口数值（5 小时窗口与 7 天配额的确切关系，二手资料口径不一）[不确定]
- Appshots 对 macOS 系统版本的具体最低要求（第三方资料写 macOS 14.2+，OpenAI 官方文档未逐一核对）[不确定]
- tool calling 支持模型的完整清单（DeepSeek V4/Qwen3.5 coder/MiniMax M3 之外还有哪些，未逐一核对各厂商官方文档）[不确定]
- 「Codex 间歇性 400」是否仍存在于当前版本（该现象源自较旧的 chat/responses 动态切换分析，2026-02 移除 chat 后是否已消除未核实）[不确定]
- 锁定态计算机使用「短时授权窗口」的具体时长与「本地输入检测」的灵敏度，官方未公开精确参数 [不确定]
