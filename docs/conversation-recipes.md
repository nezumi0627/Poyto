# Conversation recipes

Poyto is designed so a user can control POYP from a normal conversation with one short sentence. The agent should infer the safe sequence of reads, monitoring cadence, and reporting language from the user's request instead of requiring command syntax.

## Language behavior

Respond in the language the user normally uses in the current conversation. If the user explicitly asks for another language, use that language. Keep tool names, market IDs, and exact numeric values unchanged. When presenting a proposed trade, restate the market, side/position, amount, and timing clearly before executing any state-changing action.

## One-line examples

### 1. Follow one market until it ends

> この市場を終了まで追って、残り時間に合わせて確認間隔を自動で変えて、重要な変化だけ日本語で教えて。

Agent behavior:

- identify the referenced market from conversation context or inspect the market list
- read the market end/deadline information when available
- choose a monitoring interval from the remaining time instead of using a fixed cadence
- check less often when far from the deadline and more often near the end
- notify only on meaningful changes, deadline proximity, or settlement/closure
- stop automatically after the market is closed/resolved or after the deadline has clearly passed

Suggested cadence policy when the host scheduler supports rescheduling:

| Remaining time | Suggested interval |
| --- | --- |
| more than 7 days | every 12–24 hours |
| 2–7 days | every 6 hours |
| 12–48 hours | every 2 hours |
| 3–12 hours | every 30–60 minutes |
| 30 minutes–3 hours | every 15 minutes |
| under 30 minutes | every 5 minutes, subject to host limits |

This is a default policy, not a hard-coded trading rule. The agent should lengthen the interval for inactive markets and shorten it when a material change or imminent deadline warrants closer observation.

### 2. Follow one position until exit/settlement

> このポジションを終わるまで追って、残り時間と値動きから確認間隔を自動調整して、売る判断が必要になった時だけ教えて。

Agent behavior:

- inspect the user's portfolio and referenced market
- monitor current position/market state
- adapt the interval from remaining time and observed activity
- do not sell automatically unless the user explicitly authorized a concrete exit rule
- when the rule is met, report the exact proposed sell operation and ask for confirmation unless prior explicit authorization already covers that exact action
- stop after the position is gone or the market closes

### 3. Daily market review without automatic trading

> 毎日1回、注目市場と自分のポートフォリオを確認して、取引した方がよさそうなものがあれば日本語で短く教えて。

Agent behavior:

- run once per day using the host scheduler
- inspect balances, portfolio, and relevant open markets
- summarize only notable changes/opportunities
- never turn a recommendation into a buy/sell without concrete confirmation

### 4. One fixed trade every day

> 毎日9時にこの市場のYESへ10ポイントずつ買って、実行結果だけ日本語で教えて。

This is a recurring mutation. Create it only when the user has explicitly specified the exact market, position/side, amount, recurrence, and understands it repeats. Each run should fetch fresh market state first. If the market is closed, unavailable, or the exact trade is no longer valid, skip the trade and report the reason instead of guessing.

### 5. Daily conditional trade

> 毎日1回この市場を見て、YESが指定条件を満たした時だけ10ポイント買って、それ以外は何もしないで。

Agent behavior:

- turn this into a condition-based scheduled check
- inspect fresh market data every run
- execute only if the user has explicitly defined the exact condition and exact trade
- do nothing when the condition is false
- avoid duplicate execution if the condition remains true across multiple runs unless the user explicitly requested repeated buys

### 6. Balance / portfolio digest

> 毎晩、残高とポートフォリオの変化だけ日本語でまとめて。

Agent behavior:

- schedule one read-only run each evening
- compare with the previous run when the host can retain prior output/state
- report only changes; suppress unchanged details when practical

### 7. Deadline-aware notification

> この市場が終わるまで監視して、終了が近づいたら間隔を詰めて、残り1時間・30分・10分でも知らせて。

Agent behavior:

- use deadline-aware adaptive scheduling
- ensure milestone notifications happen at or after the requested thresholds
- continue normal meaningful-change monitoring between milestones
- stop automatically on closure/resolution

## Scheduling principles

The host agent/automation system owns scheduling. Poyto provides fresh account/market reads and guarded mutations at execution time.

For one-market monitoring, prefer adaptive scheduling over a fixed high-frequency loop. The agent should choose the next check from remaining time, observed activity, requested urgency, and scheduler minimum frequency. If the host scheduler cannot dynamically reschedule an existing job, choose the nearest safe fixed interval or create staged schedules for coarse, medium, and near-deadline phases.

Read-only monitoring may be scheduled from a short natural-language request. Recurring buys/sells require explicit authorization of the exact repeated transaction. Conditional mutations additionally require an explicit, testable condition. Never infer an amount, side, market, or repeated-mutation policy from vague language.
