import logging
from uuid import UUID

from text_reader.claude_client import ClaudeClient
from text_reader.geonames import GeoNamesClient
from text_reader.rest_client import RestClient
from text_reader.types import (
    ExtractedEvent,
    ResolvedEvent,
    ResolvedPerson,
    ResolvedPlace,
    ResolvedTime,
)

log = logging.getLogger(__name__)


class EntityResolver:
    def __init__(
        self,
        rest_client: RestClient,
        claude_client: ClaudeClient,
        geonames_client: GeoNamesClient,
    ):
        self._rest = rest_client
        self._claude = claude_client
        self._geonames = geonames_client
        # Cache resolved entities to avoid redundant lookups
        self._person_cache: dict[str, ResolvedPerson] = {}
        self._place_cache: dict[str, ResolvedPlace] = {}
        self._time_cache: dict[str, ResolvedTime] = {}

    def resolve_event(self, event: ExtractedEvent) -> ResolvedEvent:
        """Resolve all entities in an extracted event against the DB."""
        people = [self._resolve_person(p.name, p.description) for p in event.people]
        place = self._resolve_place(event.place)
        time = self._resolve_time(event.time)

        # Check for duplicate summary
        match = self._rest.find_matching_summary(
            person_ids=[p.id for p in people],
            place_id=place.id,
            datetime=time.date,
            calendar_model=time.calendar_model,
            precision=time.precision,
        )

        is_duplicate = match.get("found", False)
        duplicate_has_wikidata = match.get("has_wikidata_citation", False)
        existing_summary_id = (
            UUID(match["summary_id"]) if match.get("summary_id") else None
        )

        return ResolvedEvent(
            summary=event.summary,
            excerpt=event.excerpt,
            people=people,
            place=place,
            time=time,
            page_num=event.page_num,
            confidence=event.confidence,
            is_duplicate=is_duplicate,
            duplicate_has_wikidata=duplicate_has_wikidata,
            existing_summary_id=existing_summary_id,
        )

    def _resolve_person(self, name: str, description: str | None) -> ResolvedPerson:
        cache_key = name.lower().strip()
        if cache_key in self._person_cache:
            return self._person_cache[cache_key]

        candidates = self._rest.search_people(name=name)
        if candidates:
            match_id = self._claude.pick_best_entity_match(
                entity_name=name,
                entity_type="PERSON",
                candidates=candidates,
            )
            if match_id:
                matched = next(
                    (c for c in candidates if UUID(c["id"]) == match_id),
                    None,
                )
                if matched:
                    result = ResolvedPerson(id=match_id, name=matched["name"])
                    self._person_cache[cache_key] = result
                    return result

        # No match found — create new person
        created = self._rest.create_person(name=name, description=description)
        result = ResolvedPerson(id=UUID(created["id"]), name=name)
        self._person_cache[cache_key] = result
        return result

    def _resolve_place(self, place) -> ResolvedPlace:
        cache_key = place.name.lower().strip()
        if cache_key in self._place_cache:
            return self._place_cache[cache_key]

        # Search by name and coordinates
        candidates = self._rest.search_places(
            name=place.name,
            latitude=place.latitude,
            longitude=place.longitude,
        )
        if candidates:
            match_id = self._claude.pick_best_entity_match(
                entity_name=place.name,
                entity_type="PLACE",
                candidates=candidates,
            )
            if match_id:
                matched = next(
                    (c for c in candidates if UUID(c["id"]) == match_id),
                    None,
                )
                if matched:
                    result = ResolvedPlace(
                        id=match_id,
                        name=matched["name"],
                        latitude=matched.get("latitude", 0.0),
                        longitude=matched.get("longitude", 0.0),
                    )
                    self._place_cache[cache_key] = result
                    return result

        # No match — try GeoNames for structured data
        lat = place.latitude
        lng = place.longitude
        geonames_id = None

        if self._geonames.available:
            geo_result = self._geonames.search(place.name)
            if geo_result:
                lat = geo_result["latitude"]
                lng = geo_result["longitude"]
                geonames_id = geo_result["geonames_id"]

        # Fall back to Claude's approximate coordinates
        if lat is None:
            lat = 0.0
        if lng is None:
            lng = 0.0

        created = self._rest.create_place(
            name=place.name,
            latitude=lat,
            longitude=lng,
            geonames_id=geonames_id,
            description=place.description,
        )
        result = ResolvedPlace(
            id=UUID(created["id"]),
            name=place.name,
            latitude=lat,
            longitude=lng,
        )
        self._place_cache[cache_key] = result
        return result

    def _resolve_time(self, time) -> ResolvedTime:
        cache_key = f"{time.date}|{time.calendar_model}|{time.precision}"
        if cache_key in self._time_cache:
            return self._time_cache[cache_key]

        # Check if time already exists
        existing_id = self._rest.check_time_exists(
            datetime=time.date,
            calendar_model=time.calendar_model,
            precision=time.precision,
        )
        if existing_id:
            result = ResolvedTime(
                id=existing_id,
                name=time.name,
                date=time.date,
                calendar_model=time.calendar_model,
                precision=time.precision,
            )
            self._time_cache[cache_key] = result
            return result

        # Create new time
        created = self._rest.create_time(
            name=time.name,
            date=time.date,
            calendar_model=time.calendar_model,
            precision=time.precision,
        )
        result = ResolvedTime(
            id=UUID(created["id"]),
            name=time.name,
            date=time.date,
            calendar_model=time.calendar_model,
            precision=time.precision,
        )
        self._time_cache[cache_key] = result
        return result
