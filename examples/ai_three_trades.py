from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from poyto import PoytoClient


DONE_PHASES = {"closed", "resolved", "settled", "finished", "ended", "complete", "completed"}


@dataclass(slots=True)
class Pick:
    market_id: str
    position_index: int
    confidence: float
    expected_edge: float
    reason: str
    point_amount: float
    title: str = ""


def _first(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value not in (None, ""):
            return value
    return None


def _market_id(market: dict[str, Any]) -> str:
    value = _first(market, "id", "marketId", "market_id")
    if value is None:
        raise ValueError(f"market has no usable id: {market!r}")
    return str(value)


def _title(market: dict[str, Any]) -> str:
    value = _first(market, "title", "question", "name")
    return str(value or _market_id(market))


def _positions(market: dict[str, Any]) -> list[Any]:
    value = _first(market, "positions", "outcomes", "options", "choices")
    return value if isinstance(value, list) else []


def _deadline(market: dict[str, Any]) -> str | None:
    value = _first(
        market,
        "endsAt",
        "endAt",
        "endingAt",
        "closesAt",
        "closeAt",
        "deadline",
        "resolutionAt",
        "resolvedAt",
    )
    return str(value) if value is not None else None


def _print_market(index: int, market: dict[str, Any]) -> None:
    print(f"\n[{index:02d}] {_title(market)}")
    print(f"  id: {_market_id(market)}")
    print(f"  deadline: {_deadline(market) or 'unknown'}")
    positions = _positions(market)
    if positions:
        print("  positions:")
        for i, position in enumerate(positions):
            if isinstance(position, dict):
                label = _first(position, "label", "name", "title", "text") or f"position {i}"
                price = _first(position, "price", "probability", "prob", "odds")
                suffix = f" | market={price}" if price is not None else ""
                print(f"    {i}: {label}{suffix}")
            else:
                print(f"    {i}: {position}")


def _compact_market(market: dict[str, Any]) -> dict[str, Any]:
    """Keep the AI payload useful without sending unnecessary account metadata."""
    keep = {
        "id",
        "marketId",
        "title",
        "question",
        "description",
        "summary",
        "positions",
        "outcomes",
        "options",
        "choices",
        "phase",
        "status",
        "endsAt",
        "endAt",
        "endingAt",
        "closesAt",
        "deadline",
        "resolutionAt",
        "volume",
        "liquidity",
    }
    return {key: value for key, value in market.items() if key in keep}


def _extract_json(text: str) -> Any:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    first_obj = min((i for i in (text.find("{"), text.find("[")) if i >= 0), default=-1)
    if first_obj > 0:
        text = text[first_obj:]
    return json.loads(text)


def _ai_compare(markets: list[dict[str, Any]], *, model: str, base_url: str, api_key: str) -> list[dict[str, Any]]:
    system = (
        "You are a careful prediction-market analyst. Compare the supplied markets only. "
        "Do not claim guaranteed profit. Prefer markets where the supplied information supports a clear edge, "
        "and lower confidence when evidence is weak. Return JSON only."
    )
    user = {
        "task": (
            "Analyze all supplied ending-soon markets, compare the available positions, and rank the best three "
            "candidates. For each candidate return market_id, position_index, confidence from 0 to 1, expected_edge "
            "from -1 to 1, and a concise reason. Select three distinct markets. expected_edge is your estimated "
            "advantage over the market-implied view, not a guaranteed return."
        ),
        "required_json_shape": {
            "picks": [
                {
                    "market_id": "string",
                    "position_index": 0,
                    "confidence": 0.0,
                    "expected_edge": 0.0,
                    "reason": "string",
                }
            ]
        },
        "markets": [_compact_market(market) for market in markets],
    }

    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "temperature": 0.15,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
        ],
    }
    with httpx.Client(timeout=120) as http:
        response = http.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
    text = data["choices"][0]["message"]["content"]
    parsed = _extract_json(text)
    picks = parsed.get("picks", []) if isinstance(parsed, dict) else []
    if not isinstance(picks, list):
        raise ValueError("AI response did not contain a picks list")
    return picks


def _normalize_picks(
    raw_picks: list[dict[str, Any]],
    markets: list[dict[str, Any]],
    *,
    point_amount: float,
    min_confidence: float,
    min_edge: float,
) -> list[Pick]:
    by_id = {_market_id(market): market for market in markets}
    result: list[Pick] = []
    seen: set[str] = set()

    ranked = sorted(
        (item for item in raw_picks if isinstance(item, dict)),
        key=lambda item: (float(item.get("expected_edge", 0)), float(item.get("confidence", 0))),
        reverse=True,
    )
    for item in ranked:
        market_id = str(item.get("market_id", ""))
        if not market_id or market_id in seen or market_id not in by_id:
            continue
        confidence = max(0.0, min(1.0, float(item.get("confidence", 0))))
        expected_edge = max(-1.0, min(1.0, float(item.get("expected_edge", 0))))
        if confidence < min_confidence or expected_edge < min_edge:
            continue
        position_index = int(item.get("position_index", -1))
        positions = _positions(by_id[market_id])
        if position_index < 0 or (positions and position_index >= len(positions)):
            continue
        result.append(
            Pick(
                market_id=market_id,
                position_index=position_index,
                confidence=confidence,
                expected_edge=expected_edge,
                reason=str(item.get("reason", "")),
                point_amount=point_amount,
                title=_title(by_id[market_id]),
            )
        )
        seen.add(market_id)
        if len(result) == 3:
            break

    if len(result) != 3:
        raise RuntimeError(
            "AI did not produce three picks that met the configured thresholds. "
            "Lower --min-confidence/--min-edge or inspect the candidates instead of forcing trades."
        )
    return result


def _is_done(market: dict[str, Any]) -> bool:
    phase = str(_first(market, "phase", "status", "state") or "").lower()
    if phase in DONE_PHASES:
        return True
    if _first(market, "resolvedAt", "settledAt", "winningPositionIndex", "winnerPositionIndex") is not None:
        return True
    return False


def _winner_index(market: dict[str, Any]) -> int | None:
    value = _first(market, "winningPositionIndex", "winnerPositionIndex", "resolvedPositionIndex")
    if value is not None:
        try:
            return int(value)
        except (TypeError, ValueError):
            pass
    for index, position in enumerate(_positions(market)):
        if isinstance(position, dict) and bool(_first(position, "winner", "isWinner", "won")):
            return index
    return None


def _wait_for_results(client: PoytoClient, picks: list[Pick], *, poll_seconds: int) -> None:
    pending = {pick.market_id: pick for pick in picks}
    print(f"\nMonitoring {len(pending)} trades until all results are available...")
    while pending:
        for market_id, pick in list(pending.items()):
            try:
                market = client.market(market_id)
            except Exception as exc:  # keep a long-lived watcher alive across transient failures
                print(f"[watch] {pick.title}: temporary error: {exc}")
                continue
            if not isinstance(market, dict) or not _is_done(market):
                continue
            winner = _winner_index(market)
            result = "WIN" if winner == pick.position_index else "LOSS" if winner is not None else "RESOLVED"
            print(f"Done | {result} | {pick.title} | selected={pick.position_index} | winner={winner}")
            pending.pop(market_id, None)
        if pending:
            time.sleep(poll_seconds)
    print("\nDone: all 3 selected markets have resolved.")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch 10 ending-soon POYP markets, ask an AI to compare them, select 3, and monitor them."
    )
    parser.add_argument("--token", help="POYP access token; defaults to POYTO_TOKEN/session loading")
    parser.add_argument("--points", type=float, default=10.0, help="Points per selected trade (default: 10)")
    parser.add_argument("--poll-seconds", type=int, default=60, help="Resolution polling interval (default: 60)")
    parser.add_argument("--min-confidence", type=float, default=0.60)
    parser.add_argument("--min-edge", type=float, default=0.02)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually place the three trades. Without this flag the example is analysis-only.",
    )
    parser.add_argument("--ai-model", default=os.getenv("POYTO_AI_MODEL"))
    parser.add_argument(
        "--ai-base-url",
        default=os.getenv("POYTO_AI_BASE_URL", "https://api.openai.com/v1"),
        help="OpenAI-compatible API base URL",
    )
    parser.add_argument("--ai-api-key", default=os.getenv("POYTO_AI_API_KEY"))
    return parser


def main() -> int:
    args = _parser().parse_args()
    if not args.ai_model:
        print("Set POYTO_AI_MODEL or pass --ai-model.", file=sys.stderr)
        return 2
    if not args.ai_api_key:
        print("Set POYTO_AI_API_KEY or pass --ai-api-key.", file=sys.stderr)
        return 2
    if args.points <= 0:
        print("--points must be > 0", file=sys.stderr)
        return 2
    if args.poll_seconds < 10:
        print("--poll-seconds must be >= 10", file=sys.stderr)
        return 2

    started = datetime.now(timezone.utc).isoformat()
    print(f"Poyto AI 3-trade example | started={started}")
    print("Goal: rank opportunities by estimated edge; profit is not guaranteed.")

    kwargs: dict[str, Any] = {}
    if args.token:
        kwargs["token"] = args.token

    with PoytoClient(**kwargs) as client:
        print("\nFetching 10 ending-soon markets...")
        listing = client.markets(phase="open", limit=10, feed="home", sort="ending_soon")
        items = listing.get("items", []) if isinstance(listing, dict) else []
        if len(items) < 3:
            raise RuntimeError(f"Expected at least 3 open markets, got {len(items)}")

        markets: list[dict[str, Any]] = []
        for item in items[:10]:
            market_id = _market_id(item)
            detail = client.market(market_id)
            markets.append(detail if isinstance(detail, dict) else item)

        print(f"Found {len(markets)} candidates:")
        for index, market in enumerate(markets, 1):
            _print_market(index, market)

        print("\nAsking AI to compare all candidates...")
        raw_picks = _ai_compare(
            markets,
            model=args.ai_model,
            base_url=args.ai_base_url,
            api_key=args.ai_api_key,
        )
        picks = _normalize_picks(
            raw_picks,
            markets,
            point_amount=args.points,
            min_confidence=args.min_confidence,
            min_edge=args.min_edge,
        )

        print("\nSelected 3:")
        for index, pick in enumerate(picks, 1):
            print(
                f"{index}. {pick.title}\n"
                f"   position={pick.position_index} confidence={pick.confidence:.0%} "
                f"estimated_edge={pick.expected_edge:+.1%} points={pick.point_amount:g}\n"
                f"   reason={pick.reason}"
            )

        if not args.execute:
            print("\nDry run complete. Re-run with --execute to place these three trades and monitor them.")
            return 0

        print("\nPlacing 3 trades...")
        for pick in picks:
            client.buy(
                market_id=pick.market_id,
                position_index=pick.position_index,
                point_amount=pick.point_amount,
                order_surface="home_card",
                entry_point="home_feed",
            )
            print(f"Placed | {pick.title} | position={pick.position_index} | points={pick.point_amount:g}")

        _wait_for_results(client, picks, poll_seconds=args.poll_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
