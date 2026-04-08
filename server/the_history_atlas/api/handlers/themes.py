from the_history_atlas.api.types.themes import (
    ThemesResponse,
    ThemeCategoryResponse,
    ThemeResponse,
)
from the_history_atlas.apps.app_manager import AppManager


def get_themes_handler(apps: AppManager) -> ThemesResponse:
    themes = apps.history_app.get_themes()
    return ThemesResponse(
        categories=[
            ThemeCategoryResponse(
                id=cat.id,
                name=cat.name,
                slug=cat.slug,
                children=[
                    ThemeResponse(id=child.id, name=child.name, slug=child.slug)
                    for child in cat.children
                ],
            )
            for cat in themes
        ]
    )
