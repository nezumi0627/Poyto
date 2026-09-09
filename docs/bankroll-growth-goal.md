# Point bankroll growth goal

This document defines the intended operating policy for a conservative POYP point-growth workflow. It describes a target and risk limits; it does not promise that the target can always be reached.

## Default goal

The default campaign treats **500 points as the entire managed bankroll**, not as a single-order stake.

- Starting managed bankroll: up to **500 points**
- Target balance: **1,000 points**
- Maximum managed exposure: never exceed the configured bankroll
- Capital preservation: do not intentionally put the whole bankroll into one position
- Stop condition: once the target balance is reached, stop opening new positions and exit/settle the campaign as appropriate

For a new user who receives **400 referral points** under POYP's current eligible referral offer, the same workflow can use those points as the starting bankroll and aim for a **1,000-point total balance**.

## Session handling

The workflow should remain authenticated without requiring repeated manual HAR imports when a valid refresh token is already stored.

1. Use the saved access token while it is valid.
2. If it expires, refresh it automatically with the saved refresh token.
3. Persist any rotated refresh credential immediately after a successful refresh.
4. Retry an authenticated request at most once after a 401-triggered refresh.
5. Never print or commit access tokens, refresh tokens, cookies, HAR credentials, or session files.

## Position-selection policy

A position should be considered only after its market information has been checked and there is an evidence-based reason for the direction being taken.

The intended selection rule is:

- inspect the current market/position price and expected payout before entry
- research the underlying event when external evidence is relevant
- require a clear written rationale before entry
- prefer opportunities whose projected gross payout is at least **2x the points committed**
- skip the trade when the supporting evidence is weak, contradictory, stale, or unavailable
- never describe an expected return as guaranteed

A projected 2x payout is a screening target, not a certainty. Market settlement, price movement, and event outcomes can still produce losses.

## Bankroll protection

The 500-point bankroll is the campaign's total risk budget. It must not be treated as permission to place a 500-point all-in order.

Before each entry, the operator or automation should calculate the remaining bankroll and choose a smaller position size that preserves the ability to continue after a losing trade. Multiple simultaneous positions must be counted together when enforcing the bankroll cap.

At minimum, the workflow must enforce these invariants:

```text
single_order_stake < configured_bankroll
open_exposure + new_stake <= configured_bankroll
available_campaign_capital >= 0
target_reached => no_new_entries
```

If no sufficiently supported opportunity exists, the correct action is to wait rather than force a trade.

## Referral example

POYP's current referral offer is documented in the README as awarding 400 points to both sides when an eligible registration succeeds. A referral-driven campaign can therefore be represented as:

```text
eligible referral registration
        ↓
400 starting points
        ↓
small, evidence-backed positions
        ↓
automatic session refresh as needed
        ↓
1,000-point target balance
        ↓
stop opening new positions
```

Referral rewards and eligibility are controlled by POYP and can change, so the starting balance should always be read from the live account rather than hard-coded.
