from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="poyto", description="Poyto — unofficial POYP API CLI")
    parser.add_argument("--token", dest="global_token", help="temporary token or token-file source")
    parser.add_argument("--refresh-token", dest="global_refresh_token")
    parser.add_argument("--token-file", dest="global_token_file")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in (
        "health", "profile", "balances", "portfolio", "missions", "streak", "login-bonus",
        "referral", "notifications", "home", "walking", "refresh",
    ):
        sub.add_parser(name)

    login = sub.add_parser("login", help="save a POYP token locally")
    login.add_argument("login_token", nargs="?", help="literal token or token-file source")
    login.add_argument("--refresh-token", dest="login_refresh_token")
    login.add_argument("--har", dest="login_har", help="import a POYP session from .har or .har.zip")

    apple = sub.add_parser("login-apple")
    apple.add_argument("--id-token")
    apple.add_argument("--apple-access-token")
    apple.add_argument("--nonce")

    logout = sub.add_parser("logout")
    logout.add_argument("--local-only", action="store_true")

    markets = sub.add_parser("markets")
    markets.add_argument("--limit", type=int, default=20)
    markets.add_argument("--phase", default="open")
    markets.add_argument("--feed", default="home")
    markets.add_argument("--sort", default="recommended")

    market = sub.add_parser("market")
    market.add_argument("id")

    buy = sub.add_parser("buy")
    buy.add_argument("market_id")
    buy.add_argument("position_index", type=int)
    buy.add_argument("point_amount", type=float)
    buy.add_argument("--order-surface", default="home_card")
    buy.add_argument("--display-preset", default="dominance")
    buy.add_argument("--entry-point", default="home_feed")
    buy.add_argument("--yes", action="store_true")

    sell = sub.add_parser("sell")
    sell.add_argument("market_id")
    sell.add_argument("position_index", type=int)
    sell.add_argument("shares", type=float)
    sell.add_argument("--order-surface", default="modal_position_sell")
    sell.add_argument("--entry-point", default="mypage")
    sell.add_argument("--yes", action="store_true")

    comment = sub.add_parser("comment")
    comment.add_argument("market_id")
    comment.add_argument("body")
    comment.add_argument("--parent-comment-id")
    comment.add_argument("--yes", action="store_true")

    edit = sub.add_parser("edit-comment")
    edit.add_argument("comment_id")
    edit.add_argument("body")
    edit.add_argument("--yes", action="store_true")

    for name in ("delete-comment", "like-comment"):
        command = sub.add_parser(name)
        command.add_argument("comment_id")
        command.add_argument("--yes", action="store_true")

    for name in ("follow", "unfollow"):
        command = sub.add_parser(name)
        command.add_argument("user_id")
        command.add_argument("--yes", action="store_true")

    activity = sub.add_parser("activity")
    activity.add_argument("market_id")
    activity.add_argument("--limit", type=int, default=50)
    activity.add_argument("--types", default="all")

    charts = sub.add_parser("charts")
    charts.add_argument("market_ids", nargs="+")
    charts.add_argument("--tf", default="max")

    price = sub.add_parser("price")
    price.add_argument("asset", nargs="?", default="BTC")

    transactions = sub.add_parser("transactions")
    transactions.add_argument("--currency", default="point")
    transactions.add_argument("--limit", type=int, default=30)
    transactions.add_argument("--cursor")

    referral = sub.add_parser("set-referral")
    referral.add_argument("code")
    referral.add_argument("--yes", action="store_true")

    referral_available = sub.add_parser("referral-available")
    referral_available.add_argument("code")
    sub.add_parser("read-all-notifications")

    ad = sub.add_parser("claim-ad-reward")
    ad.add_argument("--source", default="watch_ad")
    ad.add_argument("--yes", action="store_true")

    settlement_claim = sub.add_parser("settlement-claim")
    settlement_claim.add_argument("market_id")
    settlement_claim.add_argument("position_index", type=int)
    settlement_claim.add_argument("--yes", action="store_true")

    loss_status = sub.add_parser("loss-gacha-status")
    loss_status.add_argument("market_id")

    loss_ticket = sub.add_parser("loss-gacha-ticket")
    loss_ticket.add_argument("market_id")
    loss_ticket.add_argument("--yes", action="store_true")

    loss_claim = sub.add_parser("loss-gacha-claim")
    loss_claim.add_argument("market_id")
    loss_claim.add_argument("ticket_id")
    loss_claim.add_argument("--kind", default="video_gacha")
    loss_claim.add_argument("--yes", action="store_true")

    user = sub.add_parser("user")
    user.add_argument("user_id")
    user.add_argument("--tab", default="active")
    user.add_argument("--sort", default="newest")

    raw = sub.add_parser("raw")
    raw.add_argument("method")
    raw.add_argument("path")
    raw.add_argument("--json", dest="json_text")
    return parser
