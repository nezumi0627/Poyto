from __future__ import annotations

import json

import httpx
import pytest

from poyto import PoytoClient
from poyto.cli_dispatch import execute
from poyto.cli_parser import build_parser
from poyto.mcp.server import build_server


class _CLIClientStub:
    def __getattr__(self, _name: str):
        return lambda *args, **kwargs: None


def test_client_claim_settlement_matches_implemented_shape() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"ok": True})

    with PoytoClient(
        access_token="test-access",
        auto_load_session=False,
        save_session=False,
        transport=httpx.MockTransport(handler),
    ) as client:
        assert client.claim_settlement("market-id", 3) == {"ok": True}

    assert len(seen) == 1
    request = seen[0]
    assert request.method == "POST"
    assert request.url.path == "/api/settlements/claim"
    assert json.loads(request.content) == {"marketId": "market-id", "positionIndex": 3}


@pytest.mark.parametrize("coin_ratio", [0, 10, 50, 100])
def test_client_claim_settlement_split_matches_static_schema(coin_ratio: int) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"ok": True})

    with PoytoClient(
        access_token="test-access",
        auto_load_session=False,
        save_session=False,
        transport=httpx.MockTransport(handler),
    ) as client:
        assert client.claim_settlement_split("market-id", coin_ratio) == {"ok": True}

    assert len(seen) == 1
    request = seen[0]
    assert request.method == "POST"
    assert request.url.path == "/api/settlements/claim-split"
    assert json.loads(request.content) == {"marketId": "market-id", "coinRatio": coin_ratio}


def test_client_claim_settlement_split_includes_optional_ticket() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"ok": True})

    with PoytoClient(
        access_token="test-access",
        auto_load_session=False,
        save_session=False,
        transport=httpx.MockTransport(handler),
    ) as client:
        client.claim_settlement_split("market-id", 70, ticket_id="ticket-id")

    assert json.loads(seen[0].content) == {
        "marketId": "market-id",
        "coinRatio": 70,
        "ticketId": "ticket-id",
    }


@pytest.mark.parametrize("coin_ratio", [-10, 1, 55, 110])
def test_client_claim_settlement_split_rejects_invalid_ratio(coin_ratio: int) -> None:
    with PoytoClient(
        access_token="test-access",
        auto_load_session=False,
        save_session=False,
    ) as client:
        with pytest.raises(ValueError, match="steps of 10"):
            client.claim_settlement_split("market-id", coin_ratio)


def test_cli_settlement_claim_requires_yes() -> None:
    parser = build_parser()
    args = parser.parse_args(["settlement-claim", "market-id", "3"])

    class Client(_CLIClientStub):
        def claim_settlement(self, market_id: str, position_index: int):
            pytest.fail("claim_settlement should not be called without --yes")

    with pytest.raises(SystemExit):
        execute(parser, args, Client())  # type: ignore[arg-type]


def test_cli_settlement_claim_dispatches() -> None:
    parser = build_parser()
    args = parser.parse_args(["settlement-claim", "market-id", "3", "--yes"])

    class Client(_CLIClientStub):
        def claim_settlement(self, market_id: str, position_index: int):
            return {"marketId": market_id, "positionIndex": position_index}

    assert execute(parser, args, Client()) == {  # type: ignore[arg-type]
        "marketId": "market-id",
        "positionIndex": 3,
    }


def test_cli_settlement_claim_dispatches_selected_split() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "settlement-claim",
            "market-id",
            "--coin-ratio",
            "60",
            "--ticket-id",
            "ticket-id",
            "--yes",
        ]
    )

    class Client(_CLIClientStub):
        def claim_settlement_split(
            self,
            market_id: str,
            coin_ratio: int,
            *,
            ticket_id: str | None = None,
        ):
            return {
                "marketId": market_id,
                "coinRatio": coin_ratio,
                "ticketId": ticket_id,
            }

    assert execute(parser, args, Client()) == {  # type: ignore[arg-type]
        "marketId": "market-id",
        "coinRatio": 60,
        "ticketId": "ticket-id",
    }


def test_cli_settlement_claim_requires_position_for_normal_claim() -> None:
    parser = build_parser()
    args = parser.parse_args(["settlement-claim", "market-id", "--yes"])

    with pytest.raises(SystemExit):
        execute(parser, args, _CLIClientStub())  # type: ignore[arg-type]


def test_cli_settlement_claim_rejects_ticket_without_split() -> None:
    parser = build_parser()
    args = parser.parse_args(
        ["settlement-claim", "market-id", "3", "--ticket-id", "ticket-id", "--yes"]
    )

    with pytest.raises(SystemExit):
        execute(parser, args, _CLIClientStub())  # type: ignore[arg-type]


def test_cli_settlement_claim_rejects_negative_position_index() -> None:
    parser = build_parser()
    args = parser.parse_args(["settlement-claim", "market-id", "-1", "--yes"])

    class Client(_CLIClientStub):
        def claim_settlement(self, market_id: str, position_index: int):
            pytest.fail("claim_settlement should not be called with a negative index")

    with pytest.raises(SystemExit):
        execute(parser, args, Client())  # type: ignore[arg-type]


@pytest.mark.anyio
async def test_mcp_exposes_settlement_claim_as_confirmed_mutation() -> None:
    server = build_server(read_only=False)
    tools = {tool.name: tool for tool in await server.list_tools()}
    assert "settlement_claim" in tools
    assert tools["settlement_claim"].annotations
    assert tools["settlement_claim"].annotations.readOnlyHint is False
    assert tools["settlement_claim"].annotations.destructiveHint is True


@pytest.mark.anyio
async def test_mcp_read_only_omits_settlement_claim() -> None:
    server = build_server(read_only=True)
    tools = {tool.name for tool in await server.list_tools()}
    assert "settlement_claim" not in tools
