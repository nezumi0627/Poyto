from __future__ import annotations

from ._http import HTTPClient
from .resources import (
    AccountMixin,
    DiscoveryMixin,
    EventsMixin,
    MarketsMixin,
    SocialMixin,
    TradesMixin,
)


class PoytoClient(
    HTTPClient,
    AccountMixin,
    MarketsMixin,
    TradesMixin,
    SocialMixin,
    DiscoveryMixin,
    EventsMixin,
):
    """Low-level synchronous POYP client.

    The public ``poyto.PoytoClient`` adds token loading, persistence, and automatic
    refresh on top of this class. Resource methods are split by responsibility to
    keep each module small and easy to audit against captured API traffic.
    """


__all__ = ["PoytoClient"]
