from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Callable

from .client import PoytoClient
from .exceptions import PoytoError


def _dump(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _masked(session: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "access_token": session.access_token[:12] + "...",
        "refresh_token": session.refresh_token[:12] + "..." if session.refresh_token else None,
        "expires_in": session.expires_in,
        "expires_at": session.expires_at,
        "user_id": (session.user or {}).get("id"),
    }


def _yes(parser: argparse.ArgumentParser, args: argparse.Namespace, action: str) -> None:
    if not args.yes:
        parser.error(f"{action} はアカウント状態を変更します。--yes を付けてください")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="poyto", description="Poyto — unofficial POYP API CLI")
    p.add_argument("--token", default=os.getenv("POYP_ACCESS_TOKEN"))
    p.add_argument("--refresh-token", default=os.getenv("POYP_REFRESH_TOKEN"))
    sub = p.add_subparsers(dest="command", required=True)

    for name in ("health", "profile", "balances", "portfolio", "missions", "streak", "referral", "notifications", "home", "walking", "refresh"):
        sub.add_parser(name)

    login = sub.add_parser("login-apple")
    login.add_argument("--id-token", default=os.getenv("POYP_APPLE_ID_TOKEN"))
    login.add_argument("--apple-access-token", default=os.getenv("POYP_APPLE_ACCESS_TOKEN"))
    login.add_argument("--nonce", default=os.getenv("POYP_APPLE_NONCE"))

    markets = sub.add_parser("markets")
    markets.add_argument("--limit", type=int, default=20)
    markets.add_argument("--phase", default="open")
    markets.add_argument("--feed", default="home")
    markets.add_argument("--sort", default="recommended")

    market = sub.add_parser("market")
    market.add_argument("id")

    buy = sub.add_parser("buy")
    buy.add_argument("market_id"); buy.add_argument("position_index", type=int); buy.add_argument("point_amount", type=float)
    buy.add_argument("--order-surface", default="home_card"); buy.add_argument("--display-preset", default="dominance"); buy.add_argument("--entry-point", default="home_feed"); buy.add_argument("--yes", action="store_true")

    sell = sub.add_parser("sell")
    sell.add_argument("market_id"); sell.add_argument("position_index", type=int); sell.add_argument("shares", type=float)
    sell.add_argument("--order-surface", default="modal_position_sell"); sell.add_argument("--entry-point", default="mypage"); sell.add_argument("--yes", action="store_true")

    comment = sub.add_parser("comment")
    comment.add_argument("market_id"); comment.add_argument("body"); comment.add_argument("--parent-comment-id"); comment.add_argument("--yes", action="store_true")

    for name in ("edit-comment", "delete-comment", "like-comment"):
        c = sub.add_parser(name); c.add_argument("comment_id")
        if name == "edit-comment": c.add_argument("body")
        c.add_argument("--yes", action="store_true")

    for name in ("follow", "unfollow"):
        f = sub.add_parser(name); f.add_argument("user_id"); f.add_argument("--yes", action="store_true")

    activity = sub.add_parser("activity")
    activity.add_argument("market_id"); activity.add_argument("--limit", type=int, default=50); activity.add_argument("--types", default="all")

    charts = sub.add_parser("charts")
    charts.add_argument("market_ids", nargs="+"); charts.add_argument("--tf", default="max")

    price = sub.add_parser("price"); price.add_argument("asset", nargs="?", default="BTC")
    tx = sub.add_parser("transactions"); tx.add_argument("--currency", default="point"); tx.add_argument("--limit", type=int, default=30); tx.add_argument("--cursor")

    ref = sub.add_parser("set-referral"); ref.add_argument("code"); ref.add_argument("--yes", action="store_true")
    refa = sub.add_parser("referral-available"); refa.add_argument("code")
    sub.add_parser("read-all-notifications")

    ad = sub.add_parser("claim-ad-reward"); ad.add_argument("--source", default="watch_ad"); ad.add_argument("--yes", action="store_true")

    user = sub.add_parser("user"); user.add_argument("user_id"); user.add_argument("--tab", default="active"); user.add_argument("--sort", default="newest")

    raw = sub.add_parser("raw"); raw.add_argument("method"); raw.add_argument("path"); raw.add_argument("--json", dest="json_text")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    with PoytoClient(access_token=args.token, refresh_token=args.refresh_token) as c:
        try:
            cmd = args.command
            simple: dict[str, Callable[[], Any]] = {
                "health": c.health, "profile": c.profile, "balances": c.balances,
                "portfolio": c.portfolio, "missions": c.missions, "streak": c.login_streak,
                "notifications": c.notifications, "walking": c.walking_challenge_status,
            }
            if cmd in simple: _dump(simple[cmd]())
            elif cmd == "refresh": _dump(_masked(c.refresh()))
            elif cmd == "login-apple":
                if not args.id_token: parser.error("--id-token または POYP_APPLE_ID_TOKEN が必要です")
                _dump(_masked(c.login_with_apple(id_token=args.id_token, apple_access_token=args.apple_access_token, nonce=args.nonce)))
            elif cmd == "referral": _dump({"code": c.referral_code(), "stats": c.referral_stats()})
            elif cmd == "home": _dump({"sections": c.home_sections(), "tabs": c.home_tabs()})
            elif cmd == "markets": _dump(c.markets(limit=args.limit, phase=args.phase, feed=args.feed, sort=args.sort))
            elif cmd == "market": _dump({"market": c.market(args.id), "related": c.related_markets(args.id), "aux": c.market_screen_auxiliary(args.id), "positions": c.my_market_positions(args.id)})
            elif cmd == "buy": _yes(parser, args, "購入"); _dump(c.buy(market_id=args.market_id, position_index=args.position_index, point_amount=args.point_amount, order_surface=args.order_surface, display_preset=args.display_preset, entry_point=args.entry_point))
            elif cmd == "sell": _yes(parser, args, "売却"); _dump(c.sell(market_id=args.market_id, position_index=args.position_index, shares=args.shares, order_surface=args.order_surface, entry_point=args.entry_point))
            elif cmd == "comment": _yes(parser, args, "コメント投稿"); _dump(c.post_comment(args.market_id, args.body, parent_comment_id=args.parent_comment_id))
            elif cmd == "edit-comment": _yes(parser, args, "コメント編集"); _dump(c.edit_comment(args.comment_id, args.body))
            elif cmd == "delete-comment": _yes(parser, args, "コメント削除"); _dump(c.delete_comment(args.comment_id))
            elif cmd == "like-comment": _yes(parser, args, "いいね"); _dump(c.like_comment(args.comment_id))
            elif cmd == "follow": _yes(parser, args, "フォロー"); _dump(c.follow_user(args.user_id))
            elif cmd == "unfollow": _yes(parser, args, "フォロー解除"); _dump(c.unfollow_user(args.user_id))
            elif cmd == "activity": _dump(c.market_activity(args.market_id, limit=args.limit, types=args.types))
            elif cmd == "charts": _dump(c.market_charts(args.market_ids, tf=args.tf))
            elif cmd == "price": _dump(c.asset_price(args.asset))
            elif cmd == "transactions": _dump(c.balance_transactions(currency=args.currency, limit=args.limit, cursor=args.cursor))
            elif cmd == "set-referral": _yes(parser, args, "紹介コード変更"); _dump(c.set_referral_code(args.code))
            elif cmd == "referral-available": _dump(c.referral_code_available(args.code))
            elif cmd == "read-all-notifications": _dump(c.mark_all_notifications_read())
            elif cmd == "claim-ad-reward": _yes(parser, args, "報酬claim"); _dump(c.claim_ad_reward(source=args.source))
            elif cmd == "user": _dump({
                "profile": c.user_profile(args.user_id), "follow_status": c.user_follow_status(args.user_id),
                "team_follows": c.user_team_follows(args.user_id), "followers": c.user_followers(args.user_id),
                "following": c.user_following(args.user_id), "balance_history": c.user_balance_history(args.user_id),
                "portfolio_history": c.user_portfolio_history(args.user_id, tab=args.tab, sort=args.sort),
            })
            elif cmd == "raw": _dump(c.request(args.method, args.path, json=json.loads(args.json_text) if args.json_text else None))
        except PoytoError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
