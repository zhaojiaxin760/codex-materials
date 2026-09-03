# Codex 安装配置指南（macOS + DeepSeek）

> 实操记录：2026-09-02（2026-09-03 补充第 6 章 Stop 测试门禁）
> 机器：MacBook Apple M4 / macOS 26.6.2 / 24GB
> 结果：Codex CLI v0.152.1 成功接入 DeepSeek，已通过真实请求验证；Stop 测试门禁已触发并生效

本文记录一次从零到跑通的完整过程，包含踩过的坑。目标：**不搭桥、不翻墙、不出境**，用 DeepSeek 驱动 Codex。

---

## 0. 先搞清楚三件事

**① 为什么不用 ChatGPT 登录？**
国内 `chatgpt.com` 与 `api.openai.com` 实测均超时不可达（2026-08-30、09-02 两次测试结论一致）。Codex 云端功能强制 ChatGPT 登录，所以这条路走不通。

**② 为什么不用搭桥？**
很多教程教你在本地起 LiteLLM / New API / CLIProxyAPI 做「Chat Completions ↔ Responses」协议转换。**这是过时做法。**

DeepSeek 官方文档明确说明：

> 为了满足大家对 Codex 的需求，我们的 API 新增了对 Responses API 格式的支持，其 base_url 为 `https://api.deepseek.com/`

官方文档：https://api-docs.deepseek.com/zh-cn/guides/responses_api

所以直接 `wire_api = "responses"` 即可，不需要任何中间层。

**③ 桥接层会带来什么问题？**
- 模型身份错乱：网关改了模型名，Codex 本地 models.json 记的是另一套 → 出现「它不知道自己是谁」
- 多一个维护项，Agent 边界行为不稳定
- 工具调用经过转译，容易丢能力

---

## 1. 环境体检

```bash
sw_vers                    # macOS ≥ 12
sysctl -n machdep.cpu.brand_string   # 芯片
node -v                    # 建议 22 LTS
git --version              # ≥ 2.23
brew --version
```

本次实测：macOS 26.6.2 / Apple M4 / Node v22.22.2 / Git 2.50.1 / Homebrew 5.1.7 —— 全部达标。

**网络通道检查**：

```bash
curl -s -o /dev/null -m 12 -w "%{http_code}\n" https://registry.npmjs.org/@openai%2Fcodex
curl -s -o /dev/null -m 12 -w "%{http_code}\n" -L https://github.com/openai/codex/releases/latest
curl -s -o /dev/null -m 12 -w "%{http_code}\n" https://api.deepseek.com/v1/chat/completions
```

预期：npm 与 GitHub 返回 200，DeepSeek 返回 401（401 说明端点可达，只是没有密钥）。

---

## 2. 安装 CLI

### 2.1 三种方式，本次只有一种走通

| 方式 | 命令 | 结果 |
|---|---|---|
| npm | `npm i -g @openai/codex` | ⚠️ 可行，但全局 prefix 可能指向应用内嵌的 Node，对用户自己的终端不可见 |
| brew formula | `brew install openai-codex` | ❌ `No available formula` |
| brew cask | `brew install --cask codex` | ❌ cask 定义有 bug：`generate_completions_from_executable does not support shell(s): bash, zsh, fish` |
| **预编译二进制** | 见下 | ✅ **推荐** |

### 2.2 推荐做法：下载预编译二进制

```bash
# 查最新版本号
curl -s https://api.github.com/repos/openai/codex/releases/latest | \
  python3 -c "import json,sys; print(json.load(sys.stdin)['tag_name'])"

# 下载（M 系列芯片用 aarch64-apple-darwin）
cd /tmp && mkdir codex_install && cd codex_install
curl -sL -o codex.tar.gz \
  "https://github.com/openai/codex/releases/download/rust-v0.152.1/codex-aarch64-apple-darwin.tar.gz"
tar -xzf codex.tar.gz
```

### 2.3 安装位置的选择

- `/usr/local/bin`：通常需要 sudo，不动它
- `~/bin`：用户自有目录，**但如果不在 PATH 里需要手动加**

```bash
mkdir -p ~/bin
mv codex-aarch64-apple-darwin ~/bin/codex
chmod +x ~/bin/codex

# 写入 PATH
echo '' >> ~/.zshrc
echo '# Codex CLI' >> ~/.zshrc
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

codex --version   # 应输出 codex-cli 0.152.1
```

> **坑**：不要 `sudo npm install -g`，那是 npm 权限没配对的表现，修权限而不是提权。

---

## 3. 配置 DeepSeek

### 3.1 拿到官方 models.json（关键步骤）

「不知道自己是谁」的根因就是缺这个文件。DeepSeek 官方 setup 脚本里内置了正确的模型卡片，直接取：

```bash
curl -sL -o /tmp/ds_setup.sh \
  "https://cdn.deepseek.com/api-docs/codex-deepseek-setup-en.sh"

# models.json 在脚本第 100~305 行的 heredoc 里
sed -n '100,305p' /tmp/ds_setup.sh > /tmp/models.json
mkdir -p ~/.codex && cp /tmp/models.json ~/.codex/models.json
```

内含三个模型，均为 1M 上下文：

| slug | 显示名 | 定位 |
|---|---|---|
| `deepseek-v4-flash` | DeepSeek-V4-Flash | 轻量快档，**不适合 agentic coding** |
| `deepseek-v4-pro` | DeepSeek-V4-Pro | **推荐**，智能足够 |
| `deepseek-v4-flash-vision-exp` | DeepSeek-V4-Flash-Vision | 带视觉 |

### 3.2 写 config.toml

```toml
model = "deepseek-v4-pro"
model_provider = "deepseek"
preferred_auth_method = "apikey"
forced_login_method = "api"
model_reasoning_effort = "high"
model_catalog_json = "~/.codex/models.json"

[model_providers.deepseek]
name = "deepseek"
base_url = "https://api.deepseek.com/"
wire_api = "responses"
env_key = "DEEPSEEK_API_KEY"
```

**两个刻意的选择：**

1. **用 `env_key` 而不是 `experimental_bearer_token`** —— 官方脚本会把密钥明文写进 config.toml，改用环境变量可以避免密钥落盘
2. **用 `deepseek-v4-pro` 而不是 flash** —— flash 是轻量档，跑 Codex 会明显「智商不够」

设置密钥：

```bash
echo 'export DEEPSEEK_API_KEY="sk-你的Key"' >> ~/.zshrc
source ~/.zshrc
```

### 3.3 安全边界（重要）

**provider 定义必须写在用户级 `~/.codex/config.toml`。**

项目级 `.codex/config.toml` 被禁止覆盖 provider / auth / 通知 / telemetry / profile 选择。这是防「clone 一个仓库就把你的 prompt 和密钥重定向到别人的端点」的设计。

---

## 4. 验证：用假密钥测整条链路

不需要真密钥就能确认配置是否正确：

```bash
cd /tmp
DEEPSEEK_API_KEY="sk-invalid-test-key" codex exec --skip-git-repo-check "回复两个字：收到"
```

**看输出**：

```
OpenAI Codex v0.152.1
model: deepseek-v4-pro          ← 档位正确
provider: deepseek              ← provider 正确
reasoning effort: high
ERROR: unexpected status 401 Unauthorized ... url: https://api.deepseek.com/responses
```

**出现 401 就是成功**，它证明三件事：

1. Codex 正确读取了 config.toml
2. 走的是 Responses API（注意 url 里的 `/responses`）
3. 网络可达 DeepSeek，只是密钥无效

换成真密钥即可正常使用。

---

## 5. 已知能力边界

接第三方模型后会失去的能力（这些是订阅/云端能力，不是模型能力）：

- ❌ 云端并行任务（Triggers）
- ❌ GitHub PR 自动 review
- ❌ Slack 集成

DeepSeek 侧对 Responses API 的支持也有取舍（摘自官方文档）：

| 能力 | 支持情况 |
|---|---|
| function / web_search 工具 | ✅ 支持 |
| `custom` 工具 | ⚠️ 仅 `apply_patch`（为 Codex 兼容） |
| file_search / code_interpreter / computer_use / mcp | ❌ 忽略 |
| `previous_response_id` | ❌ 不支持（无状态 API） |
| `store` / `conversation` | ❌ 不支持 |
| 图片输入 | ❌ 会被替换为占位文本 |

**这意味着：Codex 接 DeepSeek 后是纯代码 agent，不要指望它生成 PPT、操作浏览器或跑多模态任务。**

---

## 6. Stop 测试门禁（Hooks）：四个连环坑

目标：让 Codex **测试没过就不许交回**。配置本身只有几行，但 v0.152.1 上埋了四个坑，逐个踩过一遍。

### 坑 1：字段名已废弃

`[features].codex_hooks` 在 v0.152.1 已废弃，实跑会打印：

```
deprecated: `[features].codex_hooks` is deprecated. Use `[features].hooks` instead.
```

不改的话门禁就是个摆设（旧名仍能解析，但会走废弃路径）。正确写法：

```toml
[features]
hooks = true
```

用 `codex features list | grep hooks` 确认，应显示 `hooks  stable  true`。

### 坑 2：`codex exec` 根本不派发 hooks（最容易误判）

**`codex exec` 无头模式不触发 Stop / SessionStart / PostToolUse / PreToolUse**（Codex 已知问题 openai/codex#26452，多个第三方复现一致）。

后果很坑：**拿 `codex exec` 验证门禁，永远显示「没生效」** —— 这是测试方法错误，不是配置错。只有**交互式 TUI** 才运行 hooks。

### 坑 3：hooks.json 与 config.toml 不要并存

两者同时存在会告警，且行为不可预测：

```
warning: loading hooks from both ~/.codex/hooks.json and ~/.codex/config.toml
```

统一用 config.toml（新版写法），把旧的备份掉：

```bash
mv ~/.codex/hooks.json ~/.codex/hooks.json.bak
```

### 坑 4：Stop hook 的 stdout 必须为空或合法 JSON

往 stdout 打印普通文本（哪怕只是一行中文提示）会直接报错：

```
Stop hook (failed)
error: hook returned invalid stop hook JSON output
```

因为 Codex 会把 Stop hook 的 stdout 当 JSON 解析（用来接收 `decision` / `continue` 指令）。正确姿势：

| 场景 | 做法 |
|---|---|
| 进度 / 结果信息 | 写日志文件，**绝不要**打到 stdout |
| 测试通过 | **stdout 完全静默 + exit 0**（Codex 视为正常结束） |
| 测试失败 | 原因写 **stderr** + `exit 2`（注入反馈，逼它继续修） |

自检 stdout 是否干净：

```bash
OUT=$(bash ~/.codex/hooks/stop_test_gate.sh 2>/dev/null); echo "长度=${#OUT}"   # 必须是 0
```

### 完整配置

`~/.codex/config.toml` 追加：

```toml
[features]
hooks = true

[[hooks.Stop]]
[[hooks.Stop.hooks]]
type = "command"
command = "/Users/apple/.codex/hooks/stop_test_gate.sh"
timeout = 300
statusMessage = "运行测试门禁"
```

`~/.codex/hooks/stop_test_gate.sh`：

```bash
#!/bin/bash
# 有测试必须跑通（exit 2 逼 agent 继续修）；无测试套件则静默放行。
# 注意：stdout 必须保持干净，信息只写日志或 stderr。

LOG=/tmp/codex_stop_hook.log
echo "$(date '+%Y-%m-%d %H:%M:%S') Stop hook fired · cwd=$PWD" >> "$LOG"

if [ -f package.json ] && grep -q '"test"' package.json 2>/dev/null; then
  OUT=$(npm test --silent 2>&1); RC=$?
  if [ $RC -eq 0 ]; then echo "  ✅ npm test 通过" >> "$LOG"; exit 0; fi
  echo "  ❌ npm test 失败" >> "$LOG"
  { echo "测试未通过，请修复后再交回："; echo "$OUT" | tail -30; } >&2
  exit 2
fi

if [ -f pytest.ini ] || [ -f pyproject.toml ] || [ -f setup.py ] || [ -d tests ]; then
  if command -v pytest >/dev/null 2>&1; then
    OUT=$(pytest -q 2>&1); RC=$?
    if [ $RC -eq 0 ]; then echo "  ✅ pytest 通过" >> "$LOG"; exit 0; fi
    echo "  ❌ pytest 失败" >> "$LOG"
    { echo "测试未通过，请修复后再交回："; echo "$OUT" | tail -30; } >&2
    exit 2
  fi
fi

echo "  ℹ️ 无测试套件，放行" >> "$LOG"
exit 0
```

```bash
chmod +x ~/.codex/hooks/stop_test_gate.sh
```

### 首次使用必须手动信任

新版 Codex 有 hook 信任机制，**未信任的 hook 静默不执行**，且这一步无法用非交互方式代劳：

```bash
cd 你的项目目录 && codex   # 进入交互式 TUI
/hooks                     # 在输入框执行
# 选中 Stop → stop_test_gate.sh → Trust
```

改动 hook 定义后可能需要重新信任。

### 验证

在 TUI 里发一条消息并**等它回复完**（Stop 只在「一轮对话结束」那一刻触发），然后：

```bash
cat /tmp/codex_stop_hook.log
# 期望看到：Stop hook fired · cwd=... 以及结论行
# 且 TUI 里不应出现 "Stop hook (failed)"
```

---

## 7. 常见故障

| 症状 | 原因 | 处理 |
|---|---|---|
| 一启动就 404 或空流 | 端点只支持 Chat Completions | 确认 `wire_api = "responses"`，或换网关 |
| 配置不生效 | provider 写在项目级 config | 移到 `~/.codex/config.toml` |
| 模型名乱、身份错乱 | 缺 models.json 或模型名不一致 | 用官方 models.json |
| 明显「智商不够」 | 用了 flash 档 | 换 `deepseek-v4-pro` |
| codex 命令找不到 | PATH 没生效 | `source ~/.zshrc` 或重开终端 |
| 想生成 PPT / 操作浏览器 | Codex 本身没有这些能力 | 换工具，别为难它 |
| Stop hook 报 `invalid stop hook JSON output` | 脚本往 stdout 打了普通文本 | 信息改写日志 / stderr，stdout 保持空 |
| 门禁配了却从不触发 | 用 `codex exec` 验证，或未在 TUI 信任 | 改用交互式 TUI，并在 `/hooks` 里信任 |
| `deprecated: codex_hooks` 警告 | 字段名废弃 | 改为 `[features] hooks = true` |
| hooks 行为诡异 | hooks.json 与 config.toml 并存冲突 | 备份 hooks.json，统一用 config.toml |

---

## 8. 一键复现脚本

```bash
#!/usr/bin/env bash
set -euo pipefail
VER="rust-v0.152.1"

mkdir -p ~/bin ~/.codex

curl -sL -o /tmp/codex.tar.gz \
  "https://github.com/openai/codex/releases/download/${VER}/codex-aarch64-apple-darwin.tar.gz"
tar -xzf /tmp/codex.tar.gz -C /tmp
mv /tmp/codex-aarch64-apple-darwin ~/bin/codex
chmod +x ~/bin/codex

curl -sL -o /tmp/ds_setup.sh \
  "https://cdn.deepseek.com/api-docs/codex-deepseek-setup-en.sh"
sed -n '100,305p' /tmp/ds_setup.sh > ~/.codex/models.json

cat > ~/.codex/config.toml <<'EOF'
model = "deepseek-v4-pro"
model_provider = "deepseek"
preferred_auth_method = "apikey"
forced_login_method = "api"
model_reasoning_effort = "high"
model_catalog_json = "~/.codex/models.json"

[model_providers.deepseek]
name = "deepseek"
base_url = "https://api.deepseek.com/"
wire_api = "responses"
env_key = "DEEPSEEK_API_KEY"
EOF

# ── Stop 测试门禁 ──
mkdir -p ~/.codex/hooks
cat > ~/.codex/hooks/stop_test_gate.sh <<'GATE'
#!/bin/bash
# 有测试必须跑通（exit 2 逼 agent 继续修）；无测试套件则静默放行。
# 注意：stdout 必须保持干净，信息只写日志或 stderr。
LOG=/tmp/codex_stop_hook.log
echo "$(date '+%Y-%m-%d %H:%M:%S') Stop hook fired · cwd=$PWD" >> "$LOG"

if [ -f package.json ] && grep -q '"test"' package.json 2>/dev/null; then
  OUT=$(npm test --silent 2>&1); RC=$?
  if [ $RC -eq 0 ]; then echo "  ✅ npm test 通过" >> "$LOG"; exit 0; fi
  echo "  ❌ npm test 失败" >> "$LOG"
  { echo "测试未通过，请修复后再交回："; echo "$OUT" | tail -30; } >&2
  exit 2
fi

if [ -f pytest.ini ] || [ -f pyproject.toml ] || [ -f setup.py ] || [ -d tests ]; then
  if command -v pytest >/dev/null 2>&1; then
    OUT=$(pytest -q 2>&1); RC=$?
    if [ $RC -eq 0 ]; then echo "  ✅ pytest 通过" >> "$LOG"; exit 0; fi
    echo "  ❌ pytest 失败" >> "$LOG"
    { echo "测试未通过，请修复后再交回："; echo "$OUT" | tail -30; } >&2
    exit 2
  fi
fi

echo "  ℹ️ 无测试套件，放行" >> "$LOG"
exit 0
GATE
chmod +x ~/.codex/hooks/stop_test_gate.sh

# 追加 hooks 配置（此处需展开 $HOME，故不加引号）
cat >> ~/.codex/config.toml <<CFG

[features]
hooks = true

[[hooks.Stop]]
[[hooks.Stop.hooks]]
type = "command"
command = "$HOME/.codex/hooks/stop_test_gate.sh"
timeout = 300
statusMessage = "运行测试门禁"
CFG

grep -q 'HOME/bin' ~/.zshrc || echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
echo "完成。请设置 DEEPSEEK_API_KEY，重开终端后执行 codex，在 TUI 内运行 /hooks 信任测试门禁。"
```
