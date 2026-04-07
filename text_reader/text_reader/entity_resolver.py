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

    def pre_resolve(self, events: list[ExtractedEvent]) -> None:
        """Pre-resolve all unique entities using a batched Message Batch.

        Searches the DB for candidates for every unique person and place across
        all events, then submits a single entity-match batch to Claude. Results
        are stored in the entity caches so the subsequent publishing loop makes
        no additional Claude API calls for entity resolution.
        """
        # Step 1: Collect unique entities with event context
        person_info: dict[str, dict] = {}  # cache_key -> info dict
        place_info: dict[str, dict] = {}   # cache_key -> info dict

        for event in events:
            event_context = self._build_event_context(event)

            for person in event.people:
                key = person.name.lower().strip()
                if key not in person_info:
                    person_info[key] = {
                        "name": person.name,
                        "description": person.description,
                        "context": event_context,
                    }

            search_name = event.place.qualified_name or event.place.name
            key = search_name.lower().strip()
            if key not in place_info:
                place_info[key] = {
                    "place": event.place,
                    "search_name": search_name,
                    "context": event_context,
                }

        log.info(
            f"Pre-resolving {len(person_info)} unique people "
            f"and {len(place_info)} unique places"
        )

        # Step 2: Search DB for candidates; collect entity-match requests
        entity_requests: list[dict] = []

        for key, info in person_info.items():
            if key in self._person_cache:
                continue
            candidates = self._rest.search_people(name=info["name"])
            if candidates:
                entity_requests.append({
                    "key": f"entity-{len(entity_requests):05d}",
                    "entity_type": "PERSON",
                    "cache_key": key,
                    "entity_name": info["name"],
                    "context": info["context"],
                    "candidates": candidates,
                    "info": info,
                })
            else:
                created = self._rest.create_person(
                    name=info["name"], description=info["description"]
                )
                self._person_cache[key] = ResolvedPerson(
                    id=UUID(created["id"]), name=info["name"],
                    summary_name=info["name"],
                )

        for key, info in place_info.items():
            if key in self._place_cache:
                continue
            place = info["place"]
            candidates = self._rest.search_places(
                name=info["search_name"],
                latitude=place.latitude,
                longitude=place.longitude,
            )
            if candidates:
                entity_requests.append({
                    "key": f"entity-{len(entity_requests):05d}",
                    "entity_type": "PLACE",
                    "cache_key": key,
                    "entity_name": info["search_name"],
                    "context": info["context"],
                    "candidates": candidates,
                    "info": info,
                })
            else:
                self._place_cache[key] = self._create_place(
                    place, info["search_name"]
                )

        if not entity_requests:
            log.info("No entity matching needed — all entities resolved from cache or created")
            return

        # Step 3: Submit a single batch for all entity-matching decisions
        log.info(f"Submitting entity match batch for {len(entity_requests)} entities")
        batch_id = self._claude.submit_entity_match_batch(entity_requests)
        match_results = self._claude.poll_entity_match_batch(batch_id)

        # Step 4: Populate caches from batch results
        for req in entity_requests:
            key = req["cache_key"]
            match_id = match_results.get(req["key"])

            if req["entity_type"] == "PERSON":
                info = req["info"]
                if match_id:
                    matched = next(
                        (c for c in req["candidates"] if UUID(c["id"]) == match_id), None
                    )
                    if matched:
                        log.info(f"Matched person {info['name']!r} → {matched['name']!r} ({match_id})")
                        self._person_cache[key] = ResolvedPerson(
                            id=match_id, name=matched["name"],
                            summary_name=info["name"],
                        )
                        continue
                # No match → create new person
                log.info(f"Creating new person: {info['name']!r}")
                created = self._rest.create_person(
                    name=info["name"], description=info["description"]
                )
                self._person_cache[key] = ResolvedPerson(
                    id=UUID(created["id"]), name=info["name"],
                    summary_name=info["name"],
                )

            else:  # PLACE
                place = req["info"]["place"]
                if match_id:
                    matched = next(
                        (c for c in req["candidates"] if UUID(c["id"]) == match_id), None
                    )
                    if matched:
                        log.info(f"Matched place {req['entity_name']!r} → {matched['name']!r} ({match_id})")
                        self._place_cache[key] = ResolvedPlace(
                            id=match_id,
                            name=matched["name"],
                            latitude=matched.get("latitude", 0.0),
                            longitude=matched.get("longitude", 0.0),
                            summary_name=place.name,
                        )
                        continue
                # No match → create new place
                log.info(f"Creating new place: {req['entity_name']!r}")
                self._place_cache[key] = self._create_place(
                    place, req["info"]["search_name"]
                )

    def resolve_event(self, event: ExtractedEvent) -> ResolvedEvent:
        """Resolve all entities in an extracted event against the DB."""
        event_context = self._build_event_context(event)
        people = []
        for p in event.people:
            resolved = self._resolve_person(
                name=p.name,
                full_name=p.full_name,
                description=p.description,
                context=event_context,
            )
            # Override summary_name with THIS event's extracted name — the cache
            # may hold a different form from the first event (e.g., "Benjamin Dale"
            # vs "Benjamin James Dale").
            resolved = resolved.model_copy(update={"summary_name": p.name})
            people.append(resolved)
        place = self._resolve_place(event.place, context=event_context)
        # Override summary_name with THIS event's place.name — the cache may
        # store a different summary_name from the first event that created
        # the entry (e.g., "Lambeth" vs "St. Paul's Cathedral" when both
        # share qualified_name "Lambeth, London").
        place = place.model_copy(update={"summary_name": event.place.name})
        time = self._resolve_time(event.time)

        if people:
            match = self._rest.find_matching_summary(
                person_ids=[p.id for p in people],
                place_id=place.id,
                datetime=time.date,
                calendar_model=time.calendar_model,
                precision=time.precision,
            )
        else:
            match = {}

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

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _build_event_context(self, event: ExtractedEvent) -> str | None:
        """Build a context string for entity matching from an event's people + excerpt."""
        parts = [p.description for p in event.people if p.description]
        if event.excerpt:
            parts.append(f"Excerpt: {event.excerpt[:200]}")
        return "; ".join(parts) or None

    def _resolve_person(
        self,
        name: str,
        full_name: str | None = None,
        description: str | None = None,
        context: str | None = None,
    ) -> ResolvedPerson:
        # Use full_name for search/create; fall back to name (summary form)
        canonical = full_name or name
        cache_key = canonical.lower().strip()
        if cache_key in self._person_cache:
            return self._person_cache[cache_key]
        # Also check cache by summary name in case it was cached under that
        summary_key = name.lower().strip()
        if summary_key in self._person_cache:
            return self._person_cache[summary_key]

        candidates = self._rest.search_people(name=canonical)
        if candidates:
            match_id = self._claude.pick_best_entity_match(
                entity_name=canonical,
                entity_type="PERSON",
                candidates=candidates,
                context=context,
            )
            if match_id:
                matched = next(
                    (c for c in candidates if UUID(c["id"]) == match_id), None
                )
                if matched:
                    result = ResolvedPerson(
                        id=match_id, name=matched["name"],
                        summary_name=name,
                    )
                    self._person_cache[cache_key] = result
                    self._person_cache[summary_key] = result
                    return result

        created = self._rest.create_person(name=canonical, description=description)
        result = ResolvedPerson(
            id=UUID(created["id"]), name=canonical, summary_name=name,
        )
        self._person_cache[cache_key] = result
        self._person_cache[summary_key] = result
        return result

    def _resolve_place(self, place, context: str | None = None) -> ResolvedPlace:
        search_name = place.qualified_name or place.name
        cache_key = search_name.lower().strip()
        if cache_key in self._place_cache:
            return self._place_cache[cache_key]

        candidates = self._rest.search_places(
            name=search_name,
            latitude=place.latitude,
            longitude=place.longitude,
        )
        if candidates:
            match_id = self._claude.pick_best_entity_match(
                entity_name=search_name,
                entity_type="PLACE",
                candidates=candidates,
                context=context,
            )
            if match_id:
                matched = next(
                    (c for c in candidates if UUID(c["id"]) == match_id), None
                )
                if matched:
                    result = ResolvedPlace(
                        id=match_id,
                        name=matched["name"],
                        latitude=matched.get("latitude", 0.0),
                        longitude=matched.get("longitude", 0.0),
                        summary_name=place.name,
                    )
                    self._place_cache[cache_key] = result
                    return result

        result = self._create_place(place, search_name)
        self._place_cache[cache_key] = result
        return result

    def _resolve_time(self, time) -> ResolvedTime:
        cache_key = f"{time.date}|{time.calendar_model}|{time.precision}"
        if cache_key in self._time_cache:
            return self._time_cache[cache_key]

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

    def _create_place(self, place, search_name: str) -> ResolvedPlace:
        """Create a new place, trying GeoNames for coordinates first."""
        lat = place.latitude
        lng = place.longitude
        geonames_id = None

        if self._geonames.available:
            geo_result = self._geonames.search(search_name)
            if geo_result:
                lat = geo_result["latitude"]
                lng = geo_result["longitude"]
                geonames_id = geo_result["geonames_id"]

        if lat is None:
            lat = 0.0
        if lng is None:
            lng = 0.0

        created = self._rest.create_place(
            name=search_name,
            latitude=lat,
            longitude=lng,
            geonames_id=geonames_id,
            description=place.description,
        )
        return ResolvedPlace(
            id=UUID(created["id"]),
            name=search_name,
            latitude=lat,
            longitude=lng,
            summary_name=place.name,
        )
