# Codex 资料库

OpenAI Codex 的调研资料与落地手册。面向**一人公司**视角整理：无同事 code review、成本敏感、需要异步杠杆。

最后更新：2026-08-31

---

## 先看哪个

| 你的目的 | 看这个 |
|---|---|
| **想马上用起来** | [`codex-workflow/report.md`](codex-workflow/report.md) —— 15 章可照做的操作手册 |
| **想先了解 Codex 是什么** | [`codex资料汇总.md`](codex资料汇总.md) —— 10 章调研笔记 |
| **只想看结论** | 本文件「关键结论速览」 |
| **想改手册** | 改 `codex-workflow/results/*.json`，然后 `python3 codex-workflow/generate_report.py` 重新生成 |

---

## 文件说明

```
codex资料汇总.md              28K   调研笔记，10 章
  1  Codex 是什么
  2  近期重要动态（含官方 changelog 版本追踪与模型弃用时间表）
  3  AGENTS.md 自定义指令机制
  4  Codex vs Claude Code 全面对比（基准 / 价格 / 选型决策规则）
  5  多 Agent 配置与并发上限
  6  使用 Codex 的前置要求（账号 / 环境 / 沙箱）
  7  成本模型与 token 控制
  8  能否接入国内模型
  9  Codex vs 国内同类产品

codex-workflow/               落地手册（deep-research 产出）
  report.md                   224K  15 章完整手册 ← 主交付物
  outline.yaml                      调研大纲（15 章节 + 执行配置）
  fields.yaml                       字段定义（10 个维度）
  generate_report.py                汇总脚本，改完 JSON 跑它重新生成 report.md
  results/*.json                    15 份原始调研数据（每章一份）
```

手册 15 章：契约式派单模板 · 派单验收门禁 · AGENTS.md 写法 · Goal Mode · config.toml 配置 · 权限新体系 · Hooks 强制验证 · 验证循环 · 上下文治理 · 成本可视化 · 并行与 agent 分档 · 模型弃用迁移 · 国内环境适配 · 任务模板库 · 故障排查

---

## 关键结论速览

**选型**
- Codex 与 Claude Code 综合评分打平（Artificial Analysis 67:67），但赢法不同：Codex 赢执行效率（单任务 10.2min / 13.2M token / $7.08），Claude 赢探索与代码质量
- Codex 独门优势只有两个：**异步并行无人值守** + **PR 自动 review**
- 国内产品（CodeBuddy / 通义灵码 / Trae）赢在国内可用性与性价比（个人版多免费），短板是整库理解（6~7 分 vs 9.3）

**成本**
- 2026-04-02 起改 token 额度制，1 credit ≈ $0.04，滚动 5 小时窗口（不是月度封顶）
- 订阅制**没有用户可设的支出上限**；唯一硬封顶是走 API key 在平台设 budget cap
- 一人公司月成本：$20（Plus）够用，重度 $100~200
- 省钱杠杆排序：模型分档（价差 6.7 倍）> 复用会话（缓存输入 1/10 价）> 压输出（单价 6 倍于输入）> AGENTS.md 精炼 > 任务契约化

**国内可用**（本机实测 2026-08-30）
- `chatgpt.com` 与 `api.openai.com` **均超时不可达**，`api.deepseek.com` 可达（137ms）
- 因此 Codex 云端订阅路线用不了，只能走 **Codex CLI + 国产模型 API key**
- **DeepSeek**（`deepseek-v4-flash`）与 **Qwen**（百炼 compatible-mode）已原生支持 Responses API，**可直连**
- Kimi / GLM 只有 Chat Completions，必须走转换网关（LiteLLM / New API）

**易踩的坑**
- `wire_api` 只支持 `"responses"`，仅支持 Chat Completions 的端点会 404 或空流
- provider 定义必须写在**用户级** `~/.codex/config.toml`，项目级不能覆盖（安全边界）
- `--full-auto` 已于 v0.147.0 移除，改用 `--sandbox workspace-write`
- v0.150.0 起未信任项目不再加载项目级 AGENTS.md
- 配置里写死 model id 是定时炸弹（见资料汇总 2.1 的弃用时间表）

---

## 待办

- [ ] 装 Codex CLI 并配 DeepSeek provider
- [ ] 写 30 行以内的 AGENTS.md
- [ ] 配 Stop 钩子强制测试通过才交回
- [ ] 建立「派单前先 git commit」的习惯
