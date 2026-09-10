from __future__ import annotations

import argparse
import getpass
import json
from collections.abc import Callable
from typing import Any

from .auto import PoytoClient
from .config import Settings
from .models import AuthSession


def dump(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def masked(session: AuthSession) -> dict[str, Any]:
    return {
        "ok": True,
        "access_token": session.access_token[:12] + "...",
        "refresh_token": session.refresh_token[:12] + "..." if session.refresh_token else None,
        "expires_in": session.expires_in,
        "expires_at": session.expires_at,
        "user_id": (session.user or {}).get("id"),
    }


def require_yes(parser: argparse.ArgumentParser, args: argparse.Namespace, action: str) -> None:
    if not args.yes:
        parser.error(f"{action} はアカウント状態を変更します。--yes を付けてください")


def _simple_commands(client: PoytoClient) -> dict[str, Callable[[], Any]]:
    return {
        "health": client.health,
        "profile": client.profile,
        "balances": client.balances,
        "portfolio": client.portfolio,
        "missions": client.missions,
        "streak": client.login_streak,
        "login-bonus": client.login_bonus,
        "notifications": client.notifications,
        "walking": client.walking_challenge_status,
    }


def execute(parser: argparse.ArgumentParser, args: argparse.Namespace, client: PoytoClient) -> Any:
    command = args.command
    simple = _simple_commands(client).get(command)
    if simple is not None:
        return simple()

    if command == "refresh":
        return masked(client.refresh())
    if command == "referral":
        return {"code": client.referral_code(), "stats": client.referral_stats()}
    if command == "home":
        return {"sections": client.home_sections(), "tabs": client.home_tabs()}
    if command == "login":
        if args.login_har:
            if args.login_token or args.login_refresh_token:
                parser.error("--har は login_token / --refresh-token と同時に指定できません")
            return masked(client.login_from_har(args.login_har))
        token = args.login_token or getpass.getpass("POYP access token: ")
        return masked(client.login(token, args.login_refresh_token))
    if command == "login-apple":
        settings = Settings.from_env()
        id_token = args.id_token or settings.apple_id_token
        if not id_token:
            parser.error("--id-token または POYTO_APPLE_ID_TOKEN / POYP_APPLE_ID_TOKEN が必要です")
        return masked(
            client.login_with_apple(
                id_token=id_token,
                apple_access_token=args.apple_access_token or settings.apple_access_token,
                nonce=args.nonce or settings.apple_nonce,
            )
        )
    if command == "logout":
        client.logout(local_only=args.local_only)
        return {"ok": True, "saved_session": False}
    if command == "markets":
        return client.markets(
            limit=args.limit,
            phase=args.phase,
            feed=args.feed,
            sort=args.sort,
        )
    if command == "market":
        return {
            "market": client.market(args.id),
            "related": client.related_markets(args.id),
            "aux": client.market_screen_auxiliary(args.id),
            "positions": client.my_market_positions(args.id),
        }
    if command == "buy":
        require_yes(parser, args, "購入")
        return client.buy(
            market_id=args.market_id,
            position_index=args.position_index,
            point_amount=args.point_amount,
            order_surface=args.order_surface,
            display_preset=args.display_preset,
            entry_point=args.entry_point,
        )
    if command == "sell":
        require_yes(parser, args, "売却")
        return client.sell(
            market_id=args.market_id,
            position_index=args.position_index,
            shares=args.shares,
            order_surface=args.order_surface,
            entry_point=args.entry_point,
        )
    if command == "comment":
        require_yes(parser, args, "コメント投稿")
        return client.post_comment(
            args.market_id,
            args.body,
            parent_comment_id=args.parent_comment_id,
        )
    if command == "edit-comment":
        require_yes(parser, args, "コメント編集")
        return client.edit_comment(args.comment_id, args.body)
    if command == "delete-comment":
        require_yes(parser, args, "コメント削除")
        return client.delete_comment(args.comment_id)
    if command == "like-comment":
        require_yes(parser, args, "いいね")
        return client.like_comment(args.comment_id)
    if command == "follow":
        require_yes(parser, args, "フォロー")
        return client.follow_user(args.user_id)
    if command == "unfollow":
        require_yes(parser, args, "フォロー解除")
        return client.unfollow_user(args.user_id)
    if command == "activity":
        return client.market_activity(args.market_id, limit=args.limit, types=args.types)
    if command == "charts":
        return client.market_charts(args.market_ids, tf=args.tf)
    if command == "price":
        return client.asset_price(args.asset)
    if command == "transactions":
        return client.balance_transactions(
            currency=args.currency,
            limit=args.limit,
            cursor=args.cursor,
        )
    if command == "set-referral":
        require_yes(parser, args, "紹介コード変更")
        return client.set_referral_code(args.code)
    if command == "referral-available":
        return client.referral_code_available(args.code)
    if command == "read-all-notifications":
        return client.mark_all_notifications_read()
    if command == "claim-ad-reward":
        require_yes(parser, args, "報酬claim")
        return client.claim_ad_reward(source=args.source)
    if command == "settlement-claim":
        require_yes(parser, args, "予測市場の決済報酬claim")
        if args.position_index is not None and args.position_index < 0:
            parser.error("position_index は 0 以上である必要があります")
        if args.ticket_id is not None and args.coin_ratio is None:
            parser.error("--ticket-id を使う場合は --coin-ratio も指定してください")
        if args.coin_ratio is not None:
            return client.claim_settlement_split(
                args.market_id,
                args.coin_ratio,
                ticket_id=args.ticket_id,
            )
        if args.position_index is None:
            parser.error("通常の settlement claim では position_index が必要です")
        return client.claim_settlement(args.market_id, args.position_index)
    if command == "loss-gacha-status":
        return client.loss_gacha_status(args.market_id)
    if command == "loss-gacha-ticket":
        require_yes(parser, args, "外れ取引救済チケット発行")
        return client.create_loss_gacha_ticket(args.market_id)
    if command == "loss-gacha-claim":
        require_yes(parser, args, "外れ取引救済報酬claim")
        return client.claim_loss_gacha(args.market_id, args.ticket_id, kind=args.kind)
    if command == "user":
        return {
            "profile": client.user_profile(args.user_id),
            "follow_status": client.user_follow_status(args.user_id),
            "team_follows": client.user_team_follows(args.user_id),
            "followers": client.user_followers(args.user_id),
            "following": client.user_following(args.user_id),
            "balance_history": client.user_balance_history(args.user_id),
            "portfolio_history": client.user_portfolio_history(
                args.user_id,
                tab=args.tab,
                sort=args.sort,
            ),
        }
    if command == "raw":
        return client.request(
            args.method,
            args.path,
            json=json.loads(args.json_text) if args.json_text else None,
        )
    raise RuntimeError(f"unknown command: {command}")
