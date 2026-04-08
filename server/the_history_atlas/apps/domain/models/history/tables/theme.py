from __future__ import annotations

from uuid import UUID

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class ThemeModel(ConfiguredBaseModel):
    id: UUID
    name: str
    slug: str
    parent_id: UUID | None
    display_order: int


class ThemeWithChildrenModel(ThemeModel):
    children: list[ThemeModel]


class SummaryThemeModel(ConfiguredBaseModel):
    id: UUID
    summary_id: UUID
    theme_id: UUID
    is_primary: bool
    confidence: float | None
