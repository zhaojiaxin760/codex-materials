# TokenHub v2 P1 交付与验收记录

**日期：** 2026-09-28 · **提交：** `8dff78b`（已推送 origin/main）· **基线：** `1dd930b`

实施方式：Codex CLI 执行（12 分 38 秒），AI 独立验收（未采信其自报测试结果）。

## 一、交付内容

### 1. 渠道多 Key（key 级禁用）

| 项 | 说明 |
|----|------|
| 新表 | `provider_keys`（`ProviderKey`）：一把渠道可挂多把上游 Key，各自 `is_active` / `auto_disabled` / `fail_count` / `last_failed_at` / `last_used_at` / `label` |
| 向后兼容 | `provider_keys` 无行时仍走 `Provider.upstream_key_encrypted` 单 Key 老路径，行为与旧版逐字一致 |
| 挑选逻辑 | `provider_keys.pick_key()` 在可用 Key 中随机挑；跳过手动停用、自动摘除、冷却中的 Key |
| Key 级记账 | `record_key_result()`：401/403 或传输层故障**即时摘 Key**；其余失败达 `CHANNEL_FAILURE_THRESHOLD` 摘 Key |
| 关键设计 | **仅当该渠道全部 Key 都不可用时才摘渠道**——一个坏 Key 不再误伤同渠道的好 Key |
| 冷却隔离 | 冷却标识 `provider_id:key_id`；provider 级标识沿用裸 `provider_id`，旧行为不变 |
| 额外修复 | 补 Key / 重新启用 Key 时**自动把被摘渠道拉回分发池**（详见第四节） |
| 管理接口 | `GET/POST/DELETE/PATCH /api/admin/providers/{id}/keys`，只回显掩码，写审计 |

### 2. auto 分组 + 跨组重试

| 项 | 说明 |
|----|------|
| 新配置 | `AUTO_GROUP_ORDER`（默认 `"default"`） |
| 行为 | Key 分组为 `auto` 时，按 `AUTO_GROUP_ORDER` 顺序跨组选渠道；前一组选不出才降级到下一组 |
| 兼容性 | 默认值保证 `auto` 等价于旧 `default` 行为；非 auto 分组逻辑一字未改 |
| 新增函数 | `distributor.select_provider_across_groups()`；`select_provider()` 签名与语义未改 |

改动 12 个文件（9 改 3 新增），未新增第三方依赖。

## 二、验收证据（人工复核，非 Codex 自报）

1. **改动范围**：12 个文件全在派活允许清单内；`HEAD` 未被动（无擅自 commit）；无越界/探测残留文件
2. **基线对照**：改动前在独立 worktree（`/tmp/th_baseline`）跑满 **32/32 通过**，作为回归基准
3. **全量回归**：改动后 **34/34 通过**（32 基线 + 2 新增）
4. **独立验证 1**（`/tmp/verify_p1.py`，自写、不复用其测试）：**28 项断言全过**
   - 老路径取到 provider 自带 key / 有 provider_keys 行时不再用自带 key
   - 40 次取样只落在两把新 Key、401 只摘 Key 不摘渠道
   - Key 级冷却隔离、全 Key 失效才摘渠道且能力索引 `enabled=False`
   - 跨组选择顺序与 `exclude_ids` 降级、`AUTO_GROUP_ORDER` 脏输入容错
5. **独立验证 2**（`/tmp/verify_p1_api.py`，ASGI 端到端）：**19 项断言全过**
   - 管理接口增删改查可用、**响应与列表均不泄漏明文 key**、未带 token 返回 401、重复删除 404
6. `python -m compileall -q app` 通过

## 三、实施方（Codex）主动申报的疑虑点

- ~~Key 恢复后渠道不自动恢复~~ → 已由本次修复解决（见第四节）
- `probe_provider` 新增可选 `key` 参数：非对外接口，不影响 API

## 四、本次额外修复（防静默黑洞）

**问题**：渠道因「所有 Key 都不可用」被自动摘除后，若管理员只是补一把新 Key 或重新启用旧 Key，渠道仍停在 `auto_disabled=True`，分发层不会把流量路由过来 —— 表现为「Key 配好了却一直 503」，且没有任何报错。

**修复**：`provider_keys._recover_provider_if_ready()`，在 `add_key` / `set_key_enabled(enabled=True)` 后调用，复用 `monitor.enable_channel` 的恢复语义（清标记 + 清失败计数 + 重建能力索引 + 审计）。
**边界**：管理员**手动停用**（`is_active=False`）的渠道不受影响 —— 手动停用是明确意图，不被 Key 变更悄悄推翻（已写反向断言守护）。

## 五、遗留决策项：旧副本分叉提交的处置

本地旧副本 `/Users/apple/WorkBuddy/2026-08-30-08-55-45/tokenhub` 与远端双向分叉，独有 5 个提交已备份为远端分支 `backup/local-diverged-20260928`。逐条核查结论：

| 提交 | 内容 | 核查结论 | 建议 |
|------|------|---------|------|
| `efed7d8` | 查单改用线程池 + 单订单异常不中断整轮 | **main 确实缺失**：`app/reconciliation.py:69` 直接同步调用 `query_payment()`，其内部是阻塞 HTTP SDK（wechatpayv3），会阻塞整个事件循环 | **建议移植（P0 级）** |
| `bf4f9cd` | 预算并发竞态 + 金额精度 + 单笔上限改 10 万 | 竞态：main 已用原子 `UPDATE ... WHERE balance >= cost` 独立解决，**无需移植**；精度：main 仍全用 `Float` + `round(float(),6)`，无 `money.py`；上限：main 为 100 万，属业务决策 | 精度单独立项；上限由老大定 |
| `5b026d3` | 文档字段名修正 + Dockerfile 走清华源 | 国内构建加速有效；`DEPLOY_CHECKLIST.md` main 缺失 | 建议移植 |
| `d087eb0` | 新增生产部署清单文档 | main 缺失该文件 | 建议直接补文件 |
| `49d2cba` | P0 渠道治理三项 | 已等价落进 main（`1dd930b`） | 无需处理 |

本记录未做任何移植动作（非破坏性），备份分支保留。

## 六、下一步待办（v2 清单剩余）

- P2：响应 >5s 算不健康、上游余额追踪
- 明确不做：表达式分层计费、订阅双资金源
