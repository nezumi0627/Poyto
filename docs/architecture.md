# Architecture

Poyto is intentionally split by responsibility so API behavior can be audited without reading one giant client module.

```text
src/poyto/
├── config.py          # environment/config resolution
├── token_loader.py    # literal/plaintext/JSON/dotenv token parsing
├── session_store.py   # persistent session storage
├── device_store.py    # persistent app-style device identity
├── models.py          # AuthSession / DeviceInfo
├── exceptions.py      # public error hierarchy
├── _http.py           # HTTP transport, headers, auth exchange, raw requests
├── _resource.py       # typing contract for resource mixins
├── resources/
│   ├── account.py     # /api/me, referrals, notifications, walking
│   ├── markets.py     # market reads, charts, activity, prices
│   ├── trades.py      # buy/sell request shapes
│   ├── social.py      # comments, users, follows, leaderboards, timeline
│   ├── discovery.py   # home/search/interests/onboarding
│   └── events.py      # analytics-event payloads
├── client.py          # low-level composition only
├── auto.py            # high-level token persistence + refresh policy
├── cli_parser.py      # argparse schema
├── cli_dispatch.py    # command execution
└── cli.py             # tiny CLI entry point
```

## Design rules

1. **Observed API shapes stay in resource modules.** A resource method should be easy to compare against a HAR entry.
2. **Transport concerns stay out of resources.** Authorization, headers, HTTP errors, base URLs, and Supabase exchange live in `_http.py`.
3. **Credential sources do not bleed into each other.** Explicit credentials are never paired with unrelated environment refresh tokens.
4. **Authentication and device identity have separate lifecycles.** Saved sessions, refresh-before-expiry, one-time 401 retry, and logout cleanup live in `auto.py`; the stable device ID lives independently in `device_store.py`.
5. **CLI is an adapter, not business logic.** It parses arguments and delegates to the same public client methods used by Python callers.
6. **Undocumented operations are not invented.** Dedicated methods are added only for request shapes observed in supplied captures; `request()` remains the escape hatch.

## Client layers

`poyto.client.PoytoClient` is the low-level composed client. `poyto.PoytoClient` points to the high-level client in `auto.py`, which subclasses the low-level client and adds credential lifecycle behavior.

This keeps library usage simple:

```python
from poyto import PoytoClient

with PoytoClient() as client:
    print(client.balances())
```

while still keeping the implementation modular and testable.
