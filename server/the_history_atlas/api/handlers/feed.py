from the_history_atlas.api.types.feed import (
    FeedResponse,
    FeedEvent,
    FeedTag,
    FeedTheme,
)
from the_history_atlas.apps.app_manager import AppManager


def get_feed_handler(
    apps: AppManager,
    themes: list[str] | None = None,
    after_cursor: str | None = None,
    limit: int = 20,
    user_id: str | None = None,
) -> FeedResponse:
    result = apps.history_app.get_feed(
        limit=limit,
        theme_slugs=themes,
        after_cursor=after_cursor,
        user_id=user_id,
    )
    events = [
        FeedEvent(
            summaryId=e["summary_id"],
            summaryText=e["summary_text"],
            tags=[
                FeedTag(id=t["id"], type=t["type"], name=t["name"])
                for t in e["tags"]
            ],
            themes=[
                FeedTheme(slug=t["slug"], name=t["name"])
                for t in e["themes"]
            ],
            latitude=e["latitude"],
            longitude=e["longitude"],
            datetime=e["datetime"],
            precision=e["precision"],
            isFavorited=e["is_favorited"],
        )
        for e in result["events"]
    ]
    return FeedResponse(events=events, nextCursor=result["next_cursor"])
