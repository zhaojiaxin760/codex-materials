# TokenHub vs new-api 竞品功能对比分析（渠道健康监测 / 令牌与渠道切换 / 计费）

> 阅读范围：仅本地静态阅读两份源码，未运行、未修改、未联网。
> TokenHub：`/Users/apple/WorkBuddy/2026-08-30-08-55-45/tokenhub`
> new-api：`/tmp/new-api-ref`

---

## 1. new-api 渠道健康监测的实现

new-api 的健康监测分两套互相配合的机制：

1. **请求内即时失效**：真实请求命中可判定为“渠道自身错误”时，直接禁用渠道（可选，默认关闭）。
2. **定时探活**：后台按周期对所有/部分渠道发最小测试请求，决定“禁用”或“自动恢复”（可选，默认关闭）。

两套都只处理“渠道自身错”，不处理客户端请求体错（400 等）。

### 1.1 探活机制：多久测一次、测什么接口、超时判定

**调度入口**

- 文件：`controller/system_task_handlers.go`
- `channelTestHandler`（`controller/system_task_handlers.go:32`）是定时任务处理器：
  - `Enabled()` 读 `monitor_setting.auto_test_channel_enabled`，默认 **false**（`setting/operation_setting/monitor_setting.go:30`）。
  - `Interval()` 读 `monitor_setting.auto_test_channel_minutes`，默认 **10 分钟**（`monitor_setting.go:31`、`system_task_handlers.go:38-44`）。
  - `Run()`（`system_task_handlers.go:58`）调 `runChannelTestTask`（`controller/channel-test.go:1089`）。

**测试请求内容**

- 核心函数 `testChannel`（`controller/channel-test.go:72`）：
  - 测试模型优先级：`channel.TestModel` → 渠道配置的首个模型 → 兜底 `gpt-4o-mini`（`channel-test.go:100-111`）。
  - 自动判断端点：`/v1/chat/completions`；含 `embedding`/`m3e`/`bge-`/`embed` 走 `/v1/embeddings`；含 `rerank` 走 `/v1/rerank`；`codex` 走 `/v1/responses`；VolcEngine `seedream` 走 `/v1/images/generations`（`channel-test.go:113-155`）。
  - 请求体由 `buildTestRequest`（`controller/channel-test.go:701`）构造：默认 `max_tokens=16`，thinking 模型 50、Gemini 3000；流式测试仅 Codex 类型（`shouldUseStreamForAutomaticChannelTest`，`channel-test.go:668`）。
  - 结果校验：`detectErrorFromTestResponseBody`（`channel-test.go:607`）抽 error.message；流式还要 `validateStreamTestResponseBody`（`channel-test.go:636`）确认有合法 SSE 事件。

**超时判定（不是普通 HTTP timeout，而是响应耗时阈值）**

- 全局变量 `ChannelDisableThreshold = 5.0` 秒（`common/constants.go:128`）。
- `testChannelForHealthCheck`（`controller/channel-test.go:920`）中：若本次测试**响应时间超过阈值**，构造 `ErrorCodeChannelResponseTimeExceeded` 并标记应禁用（`channel-test.go:935-951`）。
- `performChannelTests` 把阈值转毫秒，0 时置为“不可能触发”的 10000000（`channel-test.go:1066-1068`）。

### 1.2 自动禁用 / 恢复逻辑

**请求内禁用（即时、非计数）**

- `ProcessChannelError`（`service/relay_error.go:64`）：真实请求失败后调用；判断 `ShouldDisableChannel(err)` 且渠道 `AutoBan` 为真，则异步 `DisableChannel`（`relay_error.go:69-76`）。
- `ShouldDisableChannel`（`service/channel.go:57`）的判定顺序：
  1. 全局开关 `AutomaticDisableChannelEnabled`（默认 false，`common/constants.go:129`）；
  2. `types.IsChannelError(err)`（渠道自身错）直接禁用；
  3. `IsSkipRetryError(err)`（不可重试错）不因它禁用；
  4. 命中 `AutomaticDisableStatusCodes`（默认仅 `401`，`setting/operation_setting/status_code_ranges.go:11`）；
  5. 错误文本命中 `AutomaticDisableKeywords`（AC 自动机关键字）。
- `DisableChannel`（`service/channel.go:28`）：先查 `channelError.AutoBan`，再 `model.UpdateChannelStatus(..., ChannelStatusAutoDisabled, reason)`，成功后关闭该渠道的活动 WebSocket，并给 root 发通知。
- **注意：new-api 请求内禁用没有“连续失败 N 次”计数器**，只要命中规则就禁用；这与 TokenHub 的 `fail_count` 阈值模型不同。

**定时测试内的禁用 / 恢复**

- `testChannelForHealthCheck`（`controller/channel-test.go:920`）：
  - 禁用条件：`allowDisable && 当前为启用 && shouldBanChannel && channel.GetAutoBan()` → `processChannelError` → `DisableChannel`（`channel-test.go:952-956`）。
  - 恢复条件：`result.localErr == nil && 当前非启用 && service.ShouldEnableChannel(newAPIError, status)` → `service.EnableChannel`（`channel-test.go:958-960`）。
- `ShouldEnableChannel`（`service/channel.go:79`）：全局 `AutomaticEnableChannelEnabled`（默认 false，`common/constants.go:130`）开启、本次无错误、且状态恰为 `ChannelStatusAutoDisabled` 时才恢复。
- `EnableChannel`（`service/channel.go:48`）把状态改回 `ChannelStatusEnabled` 并通知 root。

**测试范围三种模式**

- `setting/operation_setting/monitor_setting.go:19-21`：
  - `scheduled_all`：所有非手动禁用渠道（默认模式）。
  - `auto_ban_only`：只测 `AutoBan=1` 的渠道。
  - `passive_recovery`：只测 `auto_disabled` 渠道（只恢复、不新增禁用）。
- 范围筛选在 `selectChannelsForAutomaticTest`（`controller/channel-test.go:1111`）。

**并发与多实例去重**

- `monitor_setting.ChannelTestConcurrency`：默认 1、最大 32（`monitor_setting.go:24-25`）。
- `runChannelTestWorkers`（`channel-test.go:969`）按并发度开 worker，worker 间可用 `common.RequestInterval` 错峰。
- 定时任务走 `model/system_task.go` 的 `SystemTask` + DB 租约（`ActiveKey` 唯一索引、`LockedUntil`），保证多实例只有一台在跑（`system_task.go:12-38`）。

### 1.3 状态模型与渠道多 Key

- 状态枚举：`common/constants.go:258-261`：`Unknown=0 / Enabled=1 / ManuallyDisabled=2 / AutoDisabled=3`。
- `UpdateChannelStatus`（`model/channel.go:738`）：单 Key 渠道直接改状态；多 Key 渠道按 `usingKey` 只禁用该 key，并同步 `ChannelInfo.MultiKeyStatusList`，全部 key 都禁用时整渠道转 `AutoDisabled`（`handlerMultiKeyUpdate`，`model/channel.go:673`）。
- 手动操作与自动摘除通过状态值 2/3 区分，不会互相覆盖。

---

## 2. new-api 令牌分组与渠道切换

### 2.1 令牌如何绑定分组

令牌（`Token`）结构与分组相关字段在 `model/token.go:14-33`：

- `Group`：令牌固定分组，空则继承用户分组。
- `CrossGroupRetry`：是否跨分组重试（仅 `Group == "auto"` 有效）。
- `AutoGroups`：JSON 文本，保存该令牌的 auto 分组快照（有序）。

鉴权时在 `middleware/auth.go:361` 的 `TokenAuth` 中：

- `tokenGroup := token.Group`（`auth.go:456`）。
- 校验该分组是否在用户可用分组内：`service.GetUserUsableGroups`（`service/group.go:14`）、`ratio_setting.ContainsGroupRatio`（`auth.go:457-470`）。
- 若 token 有分组，则 `using_group = token.Group`，否则用 `user.Group`（`auth.go:472`）。
- `SetupContextForToken`（`auth.go:506`）把 `token.Group`、`token.CrossGroupRetry`、`token.AutoGroups` 写入请求上下文（`auth.go:524-533`）。

`Group == "auto"` 时，`GetRequestAutoGroups`（`service/group.go:97`）返回该 token 的有序 auto 分组：

- 有显式 token 快照 → `FilterUserTokenAutoGroups`（`group.go:74`）过滤掉无权分组、去重、按 `MaxTokenAutoGroups` 截断。
- 无快照 → 继承全局 `AutoGroups` 列表（`GetUserAutoGroup`，`group.go:56`）。

### 2.2 请求如何按权重 / 优先级路由

**总体分发**：`middleware/distributor.go` 的 `Distribute()`（`distributor.go:34`）→ `service.SelectChannelForRequest`（`service/channel_select.go:283`）：

1. **固定 pin 优先**：有渠道 pin 时直接用该渠道，状态非启用或过滤器不满足直接拒绝（`channel_select.go:286-317`）。
2. **会话亲和**：第一次尝试时优先复用“会话亲和缓存”里的渠道（`channel_select.go:318-356`）。
3. **随机满足条件的渠道**：`CacheGetRandomSatisfiedChannel`（`channel_select.go:114`）。

**优先级 + 权重算法**（内存缓存路径）在 `model/channel_cache.go:117` 的 `GetRandomSatisfiedChannel`：

- 先按 `group -> model` 索引取候选，精确模型名不中再尝试归一化模型名（`channel_cache.go:137-144`）。
- 收集候选渠道的所有唯一 `priority`，**降序排序**（`channel_cache.go:154-165`）。
- `retry` 作为“优先级档位下标”：`retry=0` 选最高优先级，`retry=1` 选次高……超界则用最低档（`channel_cache.go:167-169`）。
- 在目标优先级档内，按 `weight` 加权随机（`channel_cache.go:171-213`）。权重全 0 时每个渠道等效 100；平均权重 <10 时乘 100 平滑，避免“配了权重就饿死没配权重的渠道”。

无内存缓存时的 DB 回退路径等价逻辑在 `model/ability.go:108` 的 `GetChannel`（优先按 `Ability` 表过滤，同优先级内按 `weight+10` 加权随机）。

### 2.3 失败重试时的渠道切换策略

**重试循环**：`controller/relay.go:148-222`：

- `retryParam` 从 0 到 `common.RetryTimes`（默认 **0**，`common/constants.go:137`，即默认不重试，可配置）。
- 每次循环 `getChannel` → `SelectChannelForRequest` 用当前 `retry` 下标选渠道。
- 失败后由 `service.DecideRelayRetry`（`service/relay_error.go:21`）决定是否继续。

**切换策略是“优先级降级 + 档内加权随机”**，不是严格的顺序遍历：

- `ChannelError`（渠道自身错）→ 必重试（`relay_error.go:39-40`）。
- `SkipRetryError`（不可重试错）→ 停止（`relay_error.go:42-44`）。
- 剩余次数为 0 → 停止。
- 2xx → 不重试；无法识别的状态码 → 重试；命中 `AutomaticRetryStatusCodes` → 重试；否则停止（`relay_error.go:48-58`）。
- 状态码矩阵默认值在 `setting/operation_setting/status_code_ranges.go:11-25`：重试 1xx/3xx/401-407/409-499/500-503/505-523/525-599；504、524 永远不重试（`status_code_ranges.go:68-71`）。
- 由于重试下标递增，同一优先级档可能被再次随机选到（不显式排除上一渠道）；真正“换下一家”由优先级档位递减保证。

**auto 分组下的跨分组重试**：`service/channel_select.go:121-194`：

- 从 `ContextKeyAutoGroupIndex` 开始遍历 auto 分组。
- 每个分组内部先把自身所有优先级档用完；该分组找不到渠道再切下一分组。
- `CrossGroupRetry=true` 且当前分组重试次数耗尽（`priorityRetry >= RetryTimes`）时，预先切到下一分组（`channel_select.go:174-181`）。
- 语义：**分组间顺序降级、分组内优先级降级、同优先级加权随机**。

---

## 3. new-api 计费体系

### 3.1 额度单位与倍率体系

- 额度基准：`QuotaPerUnit = 500 * 1000.0`，即 $0.002 / 1K tokens（`common/constants.go:22`）。额度 = 金额 × `QuotaPerUnit`。

**倍率叠加（文本模型，按量计费）**：`relay/helper/price.go:71` 的 `ModelPriceHelper` 与 `service/text_quota.go:230` 的 `calculateTextQuotaSummary`：

- 预扣额度（开流前估计）：
  `preConsume = promptTokens × PreConsumeMultiplier × modelRatio × groupRatio`
  其中 `PreConsumeMultiplier` 默认 1（`setting/operation_setting/quota_setting.go:17-20`、`price.go:88-101`）。
- 实际结算（`text_quota.go:230-382`）把用量拆成：
  - 基础 prompt token × `modelRatio`
  - 缓存命中 token × `cacheRatio`（含 5m/1h 细分缓存写入倍率）
  - 图像 token × `imageRatio`、音频 token × `audioRatio`
  - 输出 token × `completionRatio`
  - 加总后再 × `groupRatio`，最后加工具调用附加费并四舍五入。
- 模型倍率 / 完成倍率 / 缓存倍率 / 图像倍率 / 音频倍率都由 `setting/ratio_setting` 提供（`GetModelRatio`/`GetCompletionRatio`/`GetCacheRatio`/`GetImageRatio`/`GetAudioRatio`，`setting/ratio_setting/model_ratio.go` 与 `cache_ratio.go`）。

**分组倍率（含用户分组 × 使用分组的特殊倍率）**：

- `HandleGroupRatio`（`relay/helper/price.go:43`）先查 `(userGroup, usingGroup)` 的特殊倍率 `GetGroupGroupRatio`，否则用 `usingGroup` 的普通 `GetGroupRatio`（`setting/ratio_setting/group_ratio.go:79`）。

**按次计费（MJ / 任务类）**：`ModelPriceHelperPerCall`（`relay/helper/price.go:216`）：

- 配了 model price：`quota = modelPrice × QuotaPerUnit × groupRatio`。
- 没配 price：预扣按 `modelRatio / 2 × QuotaPerUnit × groupRatio`（用一半倍率做预扣）。

**高级分层表达式计费（tiered_expr）**：`pkg/billingexpr` + `service/tiered_settle.go`：

- 支持按上下文长度分档、缓存/图像/音频子变量、固定单次价（`BillingUnitRequest`）等；由 `modelPriceHelperTiered`（`price.go:342`）生成 `BillingSnapshot`，结算走 `TryTieredSettle`（`tiered_settle.go:205`）。这套比 TokenHub 现有 `input/output/cache × 单价` 复杂得多。

### 3.2 用户预付费扣费流程（余额预扣、失败退款、并发）

**请求生命周期**：`controller/relay.go:141` 先 `relay.PrepareRequestBilling`，`defer` 里 `relay.RefundFailedRequestBilling`（`relay.go:144-146`）。

**预扣**：`relay/request_billing.go:24` 的 `PrepareRequestBilling`：

- 估算 prompt token → `ModelPriceHelper` 算 `QuotaToPreConsume`。
- 免费模型（且关闭免费模型预扣）直接跳过预扣。
- 否则 `service.PreConsumeBilling`（`service/billing.go:20`）→ `NewBillingSession`（`service/billing_session.go:379`）。

**资金源选择与回退**：`NewBillingSession`（`billing_session.go:379-500`）按用户 `BillingPreference` 选择：

- `wallet_only`：只用钱包。
- `subscription_only`：只用订阅。
- `wallet_first`：钱包不足回退订阅。
- 默认（`subscription_first`）：有活跃订阅先订阅，订阅不足且允许 overflow 才回退钱包。

**预扣顺序与原子性**：`BillingSession.preConsume`（`billing_session.go:198`）：

1. 信任额度旁路 `shouldTrust`（`billing_session.go:319`）：钱包余额 > `TrustQuotaUSD`（默认 $10，`quota_setting.go:19`）且 token 充足时，免预扣（`trusted=true`，`effectiveQuota=0`）。
2. 先预扣令牌额度：`PreConsumeTokenQuota` → `TryReserveTokenQuota`（`service/quota.go:389`、`model/quota_reserve.go:203`）。
3. 再预扣资金源：`WalletFunding.PreConsume` → `TryReserveUserQuota`（`service/funding_source.go:34`、`model/quota_reserve.go:165`）；订阅走 `PreConsumeUserSubscription`。
4. 资金源预扣失败时回滚已扣的令牌额度（`billing_session.go:232-245`）。

**并发处理（核心）**：`model/quota_reserve.go`：

- Redis 可用时用 Lua 脚本原子完成“检查 + 扣减”：
  - 用户额度：`userQuotaReserveScript`（`quota_reserve.go:20-30`），先校验 cache 里的 Id/Schema，再 `HINCRBY Quota -amount`。
  - 令牌额度：`tokenQuotaReserveScript`（`quota_reserve.go:42-59`），同步减 `RemainQuota`、加 `UsedQuota`、刷新 `AccessedTime`。
- Redis 不可用/未命中时降级为 DB 条件更新 `WHERE quota >= ?`（`reserveUserQuotaDB`/`reserveTokenQuotaDB`，`quota_reserve.go:144-161`）。
- 缓存扣减成功但落库失败时，回补缓存（`TryReserveUserQuota` 的 compensation，`quota_reserve.go:165-201`）。

**结算（多退少补）**：`BillingSession.Settle`（`billing_session.go:45`）：

- `delta = actualQuota - preConsumedQuota`。
- 先调整资金源（正补扣、负退还），再调整令牌额度；资金已提交而令牌调整失败时只记日志、标记已结算，避免误退资金（`billing_session.go:45-83`）。

**失败退款**：`RelayInfo.Billing.Refund`（`billing_session.go:86`）：

- 幂等（`settled/refunded/fundingSettled` 任一为真则不再退）。
- 异步 `gopool.Go`：先退资金源，再退令牌额度；订阅的预扣退款有 requestId 幂等保护（`funding_source.go:104-135`）。
- `RefundFailedRequestBilling`（`relay/request_billing.go:71`）在重试全部失败后调用。

**TokenHub 对应现状**：见第 5 节。TokenHub 目前是“后付费原子扣减 + 流式预占结算”，没有用户钱包预扣、信任旁路、订阅资金源和 Redis Lua 原子额度预留。

---

## 4. 数据表结构对比

### 4.1 channels（new-api）vs providers（TokenHub）

| 类别 | new-api `channels`（`model/channel.go:23`） | TokenHub `providers`（`app/models.py:55`） | 备注 |
|---|---|---|---|
| 主键 | `Id int` | `id String(36) UUID` | 主键类型不同 |
| 类型/名称 | `Type int`（渠道类型） | 无 Type，用 `name`（openai/anthropic） | **new-api 有** |
| 凭证 | `Key string`（多行/JSON 多 Key）+ `ChannelInfo` | `upstream_key_encrypted Text`（Fernet 密文） | 存储模型不同 |
| 组织 | `OpenAIOrganization *string` | 无 | **new-api 有** |
| 测试模型 | `TestModel *string` | 无 | **new-api 有** |
| 状态 | `Status int`（0/1/2/3 三态） | `is_active bool` + `auto_disabled bool` | 等价但 TokenHub 分两个布尔 |
| 权重/优先级 | `Weight *uint`、`Priority *int64` | `weight int`、`priority int` | 都有 |
| 响应/测试时间 | `ResponseTime int`、`TestTime int64` | `response_time_ms int`、`last_checked_at` | 近似 |
| 上游余额 | `Balance float64`、`BalanceUpdatedTime int64` | 无 | **new-api 有** |
| 平台用量 | `UsedQuota int64` | 无（由 UsageRecord 统计） | **new-api 有** |
| 模型/映射 | `Models string`、`ModelMapping *string` | `models JSON`、`model_mapping JSON` | 都有 |
| 状态码映射 | `StatusCodeMapping *string` | 无 | **new-api 有** |
| 自动禁用 | `AutoBan *int`（渠道级开关） | `fail_count` 阈值 + `auto_disabled` | 机制不同 |
| 其他配置 | `OtherInfo`、`Tag`、`Setting`、`ParamOverride`、`HeaderOverride`、`Remark`、`OtherSettings` | 无 | **new-api 有一批** |
| 多 Key | `ChannelInfo`（JSON：多 key 状态/轮询游标/模式） | 无 | **new-api 有** |
| 健康计数 | 无 fail_count（请求内即时禁用） | `fail_count`、`last_failed_at` | **TokenHub 有** |

### 4.2 tokens（new-api）vs api_keys（TokenHub）

| 类别 | new-api `tokens`（`model/token.go:14`） | TokenHub `api_keys`（`app/models.py:100`） | 备注 |
|---|---|---|---|
| 所属用户 | `UserId int` | `user_id String(36)` | 类型不同 |
| 密钥 | `Key string` 明文存库（另有用量缓存哈希） | `api_key_hash` + `masked_key` | 存储模型不同 |
| 绑定渠道 | 无（走 group 分发） | `provider_id`（可空，空=动态分发） | **TokenHub 有固定绑定概念** |
| 状态 | `Status int` | `is_active bool` | 近似 |
| 有效期 | `ExpiredTime int64`（-1=永久） | 无（用轮换机制） | **new-api 有** |
| 额度 | `RemainQuota`、`UsedQuota`、`UnlimitedQuota` | `balance Numeric`（RMB） | 语义不同 |
| 模型限制 | `ModelLimitsEnabled`、`ModelLimits string` | `allowed_models JSON` | 近似 |
| IP 限制 | `AllowIps *string` | `allowed_subnets JSON` | 近似 |
| 分组 | `Group`、`CrossGroupRetry`、`AutoGroups` | `group_name` | **new-api 有 auto 分组 + 跨组重试** |
| 轮换 | 无 | `auto_rotate_days`、`last_rotated_at` | **TokenHub 有** |
| 时间 | `CreatedTime`、`AccessedTime` | `created_at`、`last_used_at` | 都有 |
| 自带上游 key | 无 | `upstream_key_encrypted`（预留） | **TokenHub 有** |

### 4.3 users（new-api）vs users（TokenHub）

| 类别 | new-api `users`（`model/user.go:79`） | TokenHub `users`（`app/models.py:32`） | 备注 |
|---|---|---|---|
| 登录 | `Username`、`Password`、`Email` | `email`、`hashed_password` | new-api 支持用户名登录 |
| 角色/状态 | `Role int`、`Status int` | `is_admin bool`、`is_active bool` | 近似 |
| 额度 | `Quota int`、`UsedQuota int`、`RequestCount int` | `balance Numeric`、`budget_cap Numeric` | 语义不同 |
| 分组 | `Group string` | `group_name` | 都有 |
| 折扣 | 无用户折扣字段（在 user Setting JSON 里） | `discount_rate float` | **TokenHub 有独立折扣列** |
| 设置 | `Setting string`（JSON：计费偏好/通知等） | 无 | **new-api 有** |
| 分销/邀请 | `AffCode`、`AffCount`、`AffQuota`、`AffHistoryQuota`、`InviterId` | 无（有 InviteCode 表） | **new-api 有** |
| OAuth | GitHubId、DiscordId、OidcId、WeChatId、TelegramId、LinuxDOId | 无 | **new-api 有** |
| 支付 | `StripeCustomer` | 无 | **new-api 有** |
| 安全 | `AuthVersion`、`AccessToken`、2FA/passkey（独立表） | `token_version` | 近似 |

### 4.4 「new-api 有、TokenHub 没有」的相关表

| new-api 表/结构 | 文件 | 用途 |
|---|---|---|
| `abilities` | `model/ability.go:18` | 渠道×模型×分组能力宽表，TokenHub 的 `channel_abilities` 已对齐（字段略少：无 `Tag`、无 per-ability `Weight`，权重在 provider 上） |
| `system_tasks` / `system_task_locks` | `model/system_task.go:12,28` | 定时任务 DB 租约与去重，TokenHub 只有进程内 asyncio 循环 |
| `subscriptions` 等订阅表 | `model/subscription.go` | 订阅额度作为第二种计费资金源 |
| 全局 options KV（倍率/价格/分组倍率都存在这里，非独立表） | `setting/ratio_setting/*`、`model/option.go` | new-api 的倍率与价格是全局 KV 配置，TokenHub 是 provider.pricing + model_pricing 表 |

---

## 5. 「它有我没有」清单（重点）

只列与「渠道健康监测 / 令牌与渠道切换 / 分层计费」相关的能力。

| # | 功能点 | new-api 做法 | TokenHub 现状 | 移植难度 | 建议优先级 |
|---|---|---|---|---|---|
| 1 | 渠道多 Key（轮询/随机 + key 级禁用） | `ChannelInfo` + `GetNextEnabledKey`（`model/channel.go:64`、`model/channel.go:206`）；多 key 状态禁用见 `handlerMultiKeyUpdate`（`model/channel.go:673`） | Provider 单 key 一个密文，无 key 级状态 | 中 | 高 |
| 2 | 请求内即时自动禁用（状态码/关键字/渠道错误，配通知与 WS 关闭） | `ShouldDisableChannel`/`DisableChannel`（`service/channel.go:57`、`service/channel.go:28`）+ `ProcessChannelError`（`service/relay_error.go:64`）+ 状态码矩阵（`setting/operation_setting/status_code_ranges.go:11`） | 只有 `fail_count` 计数阈值 + 轮询恢复，无状态码/关键字即时禁用、无通知 | 低 | 高 |
| 3 | 令牌 auto 分组 + 跨分组重试 | `Token.Group/AutoGroups/CrossGroupRetry`（`model/token.go:14`）+ `GetRequestAutoGroups`（`service/group.go:97`）+ auto 分组遍历（`service/channel_select.go:121`） | 每 Key 仅单 `group_name`，无 auto/跨组 | 中 | 高 |
| 4 | 优先级档内按 weight 加权随机 + retry 按优先级降级 + 可配置重试状态码矩阵 | `GetRandomSatisfiedChannel`（`model/channel_cache.go:117`）+ `DecideRelayRetry`（`service/relay_error.go:21`）+ `status_code_ranges.go` | 已有“最高优先级档内加权随机 + exclude_ids 故障转移”，但无 retry 按优先级逐档降级、无状态码矩阵 | 低 | 高 |
| 5 | 用户钱包预扣 + 失败退款 + Redis Lua 原子额度预留 | `BillingSession`（`service/billing_session.go`）+ `TryReserveUserQuota/TokenQuota`（`model/quota_reserve.go:165,203`）+ `Refund`（`billing_session.go:86`） | 非流式后付费原子扣 key.balance；流式按预估预占 + 多退少补；无用户钱包预扣/信任旁路 | 中 | 高 |
| 6 | 响应时间超时阈值自动禁用 | `ChannelDisableThreshold=5s` + `testChannelForHealthCheck`（`controller/channel-test.go:920`） | 只有探测 timeout，无“响应时间超阈值摘除” | 低 | 中 |
| 7 | 定时探活任务框架（DB 租约去重、并发 worker、三种模式） | `channelTestHandler`（`controller/system_task_handlers.go:32`）+ `SystemTask`（`model/system_task.go`）+ `runChannelTestWorkers`（`controller/channel-test.go:969`） | 进程内 `monitor_loop`，多 worker 靠手工关调度改 cron，无 DB 租约 | 中 | 中 |
| 8 | 订阅资金源 + wallet_first/subscription_first 回退 | `NewBillingSession`（`service/billing_session.go:379`）+ `SubscriptionFunding`（`service/funding_source.go:87`） | 无订阅计费，仅钱包划拨到 key.balance | 高 | 中 |
| 9 | 模型/分组/按次倍率叠加 + 完成/缓存/图像/音频细分倍率 | `ModelPriceHelper`（`relay/helper/price.go:71`）+ `calculateTextQuotaSummary`（`service/text_quota.go:230`）+ `ratio_setting` 各倍率表 | 有 provider 定价 + model_pricing 分层 + 缓存价 + per_request，但无完成倍率/图像/音频/缓存写入细分倍率 | 中 | 低 |
| 10 | tiered_expr 分层表达式计费（按上下文长度分档、固定单次价） | `pkg/billingexpr` + `service/tiered_settle.go:205` | 无表达式计费，只有 `per_1k_tokens` / `per_request` | 高 | 低 |
| 11 | 渠道上游余额追踪 + 余额不足自动禁用 | `Channel.Balance/BalanceUpdatedTime`（`model/channel.go:23`）+ `controller/channel-billing.go:642` | 无上游余额字段与余额不足禁用 | 低 | 中 |

说明：第 3、4 条直接对应你要做的「令牌/渠道分组切换」；第 2、6、7 条对应「渠道健康监测」；第 5、8、9、10 条对应「分层计费」；第 1、11 条是这两块公用的渠道侧能力，一并列出。

---

## 附：本次声明

本次未修改任何源文件、未执行 git 操作。
