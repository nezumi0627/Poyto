# Ad reward request

This note records only what was observed in the supplied POYP HAR captures.

## Observed request

The successful capture contains this request shape:

```text
POST https://api.poyp.app/api/me/ad-rewards/claim?source=watch_ad
```

No JSON request body was present. The authenticated POYP bearer token and normal `x-poyp-*` device headers were sent.

Poyto exposes the same operation directly:

```python
result = client.claim_ad_reward()
print(result["rewardPoints"])
```

The CLI also exposes it as an explicit state-changing command:

```text
poyto claim-ad-reward --yes
```

`--yes` is intentionally required because this call changes the account balance/reward state.

## Observed success response

A later capture recorded HTTP 200 with the following response fields:

```json
{
  "earnId": "<uuid>",
  "rewardPoints": 5,
  "pointBalanceAfter": 8,
  "dailyViewCount": 2,
  "dailyViewLimit": 5
}
```

The values above are from one observed successful reward claim. They show that the captured claim awarded 5 points and that the account was at 2 of 5 daily views after the claim. They should not be treated as universal constants; the server remains authoritative.

Poyto exports `AdRewardClaimResponse` as a `TypedDict` matching the observed success schema while preserving the runtime response as the original JSON dictionary.

## Scope

Poyto keeps `claim_ad_reward(source="watch_ad")` limited to the request shape actually observed in the supplied traffic. It does not invent proof fields, alternate sources, ad-completion events, or undocumented endpoints.

The endpoint is intended to be called as part of the service's normal reward flow. Poyto does not fabricate advertisement-completion signals or attempt to bypass server-side eligibility checks.

For offline verification, tests use `httpx.MockTransport` and assert the exact method, path, query string, absence of a request body, and the observed success-response keys.
