from __future__ import annotations

from typing import Any

from .._resource import ResourceMixin


class DiscoveryMixin(ResourceMixin):
    def home_sections(self) -> Any:
        return self.get("/api/home-sections")

    def home_tabs(self) -> Any:
        return self.get("/api/home-tabs")

    def search_sections(self, **params: Any) -> Any:
        return self.get("/api/search/sections", params=params or None)

    def interest_subcategories(self, category: str = "all") -> Any:
        return self.get(f"/api/interests/{category}/subcategories")

    def campaign_banners(self) -> Any:
        return self.get("/api/campaign-banners")

    def onboarding(self) -> Any:
        return self.get("/api/onboarding")
