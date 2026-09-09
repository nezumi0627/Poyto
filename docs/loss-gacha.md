# Loss gacha recovery

Poyto supports the observed recovery flow for an eligible resolved losing market.

## Flow

First check eligibility:

```python
status = client.loss_gacha_status("MARKET_ID")
```

Observed status examples include:

```json
{
  "mode": "gacha_mini",
  "reason": null,
  "gachaExpiresAt": "...",
  "publicRange": {"min": 5, "max": 10}
}
```

Other observed states include `mode="claimed"` with `reason="already_claimed"` and `mode="none"` with `reason="winner_not_eligible"`.

If the market is eligible, create a short-lived ticket:

```python
ticket = client.create_loss_gacha_ticket("MARKET_ID")
```

Observed response shape:

```json
{
  "ticketId": "<uuid>",
  "expiresAt": "..."
}
```

The observed ticket lifetime was about five minutes. Treat `expiresAt` as authoritative rather than assuming a fixed lifetime.

After the service's required rewarded flow has legitimately completed, claim with that ticket:

```python
result = client.claim_loss_gacha(
    "MARKET_ID",
    ticket["ticketId"],
    kind="video_gacha",
)
```

Observed success shape:

```json
{
  "grantedPoints": 10,
  "grantedCoins": 0,
  "roll": "jackpot",
  "balanceAfter": 20
}
```

Those values are one observation, not universal reward constants.

## CLI

```powershell
poyto loss-gacha-status MARKET_ID
poyto loss-gacha-ticket MARKET_ID --yes
poyto loss-gacha-claim MARKET_ID TICKET_ID --kind video_gacha --yes
```

Ticket creation and claim are state-changing commands and therefore require `--yes`.

## MCP / AI harnesses

The optional MCP server exposes:

- `loss_gacha_status`
- `loss_gacha_ticket`
- `loss_gacha_claim`

The two mutation tools require `confirm=true`.

## Important boundary

Poyto exposes only the observed POYP API operations. It does not fabricate rewarded-ad completion callbacks, provider proof, eligibility state, or anti-abuse signals. A claim should only be attempted after the service's legitimate reward flow has completed and while the ticket is valid.
