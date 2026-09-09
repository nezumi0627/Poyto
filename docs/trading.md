# Trading API evidence

This document consolidates the POYP trading information that is otherwise spread across the client implementation, CLI, MCP server, endpoint inventory, APK/Hermes inventory, and regression tests.

## Current status

Poyto already has first-class buy and sell support on `main`.

| Operation | Route | Client | CLI | MCP | Evidence |
| --- | --- | --- | --- | --- | --- |
| Buy | `POST /api/trades/buy` | `PoytoClient.buy()` | `poyto buy ... --yes` | `buy(..., confirm=true)` | Observed request shape |
| Sell | `POST /api/trades/sell` | `PoytoClient.sell()` | `poyto sell ... --yes` | `sell(..., confirm=true)` | Observed request shape |

The implementation lives in `src/poyto/resources/trades.py`. CLI parsing/dispatch lives in `src/poyto/cli_parser.py` and `src/poyto/cli_dispatch.py`. Conversational-agent exposure lives in `src/poyto/mcp_server.py`. The request shapes are covered by the network-free `tests/test_client.py` MockTransport test.

## Sell request

Established route:

```text
POST /api/trades/sell
```

Established JSON fields:

```json
{
  "marketId": "MARKET_ID",
  "positionIndex": 0,
  "shares": 0.5,
  "orderSurface": "modal_position_sell",
  "entryPoint": "mypage",
  "sessionId": "SESSION_ID",
  "deviceId": "DEVICE_ID"
}
```

Poyto's public call is:

```python
client.sell(
    market_id="MARKET_ID",
    position_index=0,
    shares=0.5,
)
```

The CLI equivalent is:

```powershell
poyto sell MARKET_ID 0 0.5 --yes
```

`shares` is the number of position shares to sell; it is not a point amount. The default request metadata currently matches the observed app flow: `orderSurface="modal_position_sell"` and `entryPoint="mypage"`. `sessionId` and `deviceId` are supplied by the caller or generated/reused by Poyto as appropriate.

The repository currently establishes the sell request shape. It does not claim a complete successful-response schema, pricing formula, slippage behavior, fees, idempotency guarantees, settlement rules, anti-abuse behavior, or every server error response.

## Buy request

Established route:

```text
POST /api/trades/buy
```

Established fields are:

- `marketId`
- `positionIndex`
- `pointAmount`
- `orderSurface`
- `requestId`
- `displayPreset`
- `entryPoint`
- `sessionId`
- `deviceId`

The buy request uses `pointAmount`; the sell request uses `shares`. Keep that distinction when adding higher-level automation.

## Related trading routes found in the APK

The Android APK/Hermes static inventory also contains these trading-related routes:

| Route | Evidence | Current Poyto wrapper |
| --- | --- | --- |
| `GET /api/me/trades` | APK static-only | none |
| `POST /api/trades/quote` | APK static-only | none |
| `POST /api/trades/buy` | APK + observed | `buy()` |
| `POST /api/trades/sell` | APK + observed | `sell()` |

`GET /api/me/trades` was statically seen with query keys `cursor`, `limit`, and `status`. The exact response schema is not established in the current repository.

`POST /api/trades/quote` is present in the APK endpoint inventory, but its complete request/response shape is not established in the current repository. Do not invent a wrapper body until HAR/runtime evidence or sufficiently strong call-site evidence establishes the fields.

## Verification already present

`tests/test_client.py` exercises both trade methods through `httpx.MockTransport` and asserts that:

- buy sends `POST /api/trades/buy` with the expected `pointAmount`
- sell sends `POST /api/trades/sell` with the expected `shares`

This verifies Poyto's request construction without spending live account points.

## Evidence boundaries

Use the project evidence vocabulary consistently:

- `POST /api/trades/buy`: observed request shape and implemented
- `POST /api/trades/sell`: observed request shape and implemented
- `GET /api/me/trades`: APK static-only until dynamically verified
- `POST /api/trades/quote`: APK static-only until its shape is established

Do not promote static-only routes to observed status just because they exist in the application bundle.
