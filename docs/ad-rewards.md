# Ad reward request

This note records only what was observed in the supplied POYP HAR captures.

## Observed request

One capture contained the following request shape:

```text
POST https://api.poyp.app/api/me/ad-rewards/claim?source=watch_ad
```

No JSON request body was present. The authenticated POYP bearer token and normal `x-poyp-*` device headers were sent.

The HAR entry ended with response status `0`, so the capture does **not** prove that the request succeeded or reveal the server's success response schema.

Poyto therefore keeps `claim_ad_reward(source="watch_ad")` limited to the observed request shape and does not invent additional proof fields or undocumented endpoints.

## Usage boundary

The endpoint should only be invoked after the corresponding advertisement/reward flow has legitimately completed. Poyto does not attempt to fabricate ad-completion events or bypass eligibility checks.

For offline verification, tests should use `httpx.MockTransport` and assert the exact method, path, query string, and absence of a request body.
