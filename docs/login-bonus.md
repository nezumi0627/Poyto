# Login bonus

Poyto exposes the current login-bonus / streak state through:

```python
status = client.login_bonus()
```

CLI:

```text
poyto login-bonus
```

The current service response shape contains:

- `currentStreakDay`
- `todayReward`
- `claimedToday`
- `bonusClaimedToday`
- `bonusReward`
- `cycle`

Example sanitized response:

```json
{
  "currentStreakDay": 8,
  "todayReward": 1,
  "claimedToday": true,
  "bonusClaimedToday": false,
  "bonusReward": 1,
  "cycle": [1, 2, 2, 6, 3, 3, 8]
}
```

`claimedToday` reports whether the normal daily login reward has already been granted. In the observed flow, the normal login reward was already marked claimed and there was no separate POST/PUT claim request for that daily reward.

`bonusClaimedToday` and `bonusReward` describe a separate bonus state. A dedicated request that claims that extra bonus has not been established, so Poyto does not invent one.

The reward values and cycle above are one observed response and are not hard-coded as global constants. The server response remains authoritative.
