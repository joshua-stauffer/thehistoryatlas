import logging
import sys
from uuid import UUID

from text_reader.claude_client import ClaudeClient
from text_reader.entity_resolver import EntityResolver
from text_reader.geonames import GeoNamesClient
from text_reader.pdf_reader import Chunk, chunk_pages, extract_pages
from text_reader.publisher import Publisher
from text_reader.rest_client import RestClient
from text_reader.types import ResolvedEvent

log = logging.getLogger(__name__)


def review_event(event: ResolvedEvent, index: int) -> str:
    """Display event for user review. Returns 'a', 's', or 'q'."""
    print(f"\n{'='*60}")
    print(f"Event #{index}")
    print(f"{'='*60}")
    print(f"Summary: {event.summary}")
    print(f"People:  {', '.join(p.name for p in event.people)}")
    print(
        f"Place:   {event.place.name} ({event.place.latitude}, {event.place.longitude})"
    )
    print(f"Time:    {event.time.name} ({event.time.date})")
    if event.page_num:
        print(f"Page:    {event.page_num}")
    print(f"Confidence: {event.confidence:.0%}")
    if event.excerpt:
        print(f"\nExcerpt: {event.excerpt[:300]}")

    if event.is_duplicate:
        if event.duplicate_has_wikidata:
            print(
                "  >> DUPLICATE (has Wikidata citation — will replace text & add citation)"
            )
        else:
            print("  >> DUPLICATE (non-Wikidata — will skip)")

    while True:
        choice = input("\n[A]pprove / [S]kip / [Q]uit: ").strip().lower()
        if choice in ("a", "s", "q"):
            return choice
        print("Invalid choice. Please enter A, S, or Q.")


def run_pipeline(
    file_path: str,
    title: str,
    author: str,
    publisher_name: str,
    pub_date: str | None,
    model: str,
    start_page: int,
    end_page: int | None,
    skip_review: bool,
    rest_client: RestClient,
    claude_client: ClaudeClient,
    geonames_client: GeoNamesClient,
):
    """Main extraction pipeline."""
    # Step 1: Create or get source
    print(f"Creating source: {title} by {author}")
    source = rest_client.create_source(
        title=title,
        author=author,
        publisher=publisher_name,
        pub_date=pub_date,
    )
    source_id = UUID(source["id"])
    print(f"  Source ID: {source_id}")

    # Step 2: Create or get story
    publisher = Publisher(rest_client=rest_client)
    story_id = publisher.ensure_story(source_id=source_id, source_title=title)
    print(f"  Story ID: {story_id}")

    # Step 3: Read PDF
    print(f"\nReading PDF: {file_path}")
    pages = extract_pages(
        file_path=file_path,
        start_page=start_page,
        end_page=end_page,
    )
    if not pages:
        print("No text extracted from PDF.")
        return

    chunks = chunk_pages(pages)
    print(f"  {len(pages)} pages -> {len(chunks)} chunks")

    # Step 4: Initialize resolver
    resolver = EntityResolver(
        rest_client=rest_client,
        claude_client=claude_client,
        geonames_client=geonames_client,
    )

    # Step 5: Process chunks
    total_extracted = 0
    total_published = 0
    total_skipped = 0

    for chunk_idx, chunk in enumerate(chunks):
        print(
            f"\n--- Chunk {chunk_idx + 1}/{len(chunks)} "
            f"(pages {chunk.start_page}-{chunk.end_page}, "
            f"{len(chunk.text)} chars) ---"
        )

        # Extract events from chunk
        events = claude_client.extract_events(
            chunk_text=chunk.text,
            source_title=title,
            source_author=author,
            start_page=chunk.start_page,
            end_page=chunk.end_page,
        )
        total_extracted += len(events)
        print(f"  Extracted {len(events)} events")

        for event_idx, event in enumerate(events):
            # Set page number from chunk (use excerpt position for precision)
            if event.page_num is None:
                if event.excerpt:
                    event.page_num = chunk.page_for_excerpt(event.excerpt)
                else:
                    event.page_num = chunk.start_page

            # Resolve entities
            try:
                resolved = resolver.resolve_event(event)
            except Exception as e:
                log.error(f"Failed to resolve event: {e}")
                total_skipped += 1
                continue

            # Handle duplicates
            if resolved.is_duplicate and not resolved.duplicate_has_wikidata:
                print(f"  Skipping duplicate: {event.summary[:60]}...")
                total_skipped += 1
                continue

            # User review
            if not skip_review:
                choice = review_event(
                    resolved, total_extracted - len(events) + event_idx + 1
                )
                if choice == "q":
                    print("\nQuitting.")
                    _print_summary(total_extracted, total_published, total_skipped)
                    return
                elif choice == "s":
                    total_skipped += 1
                    continue

            # Publish
            try:
                summary_id = publisher.publish_event(
                    event=resolved,
                    source_id=source_id,
                    story_id=story_id,
                )
                if summary_id:
                    total_published += 1
                    print(f"  Published: {event.summary[:60]}...")
                else:
                    total_skipped += 1
            except Exception as e:
                log.error(f"Failed to publish: {e}")
                total_skipped += 1

    _print_summary(total_extracted, total_published, total_skipped)


def run_batch_pipeline(
    file_path: str,
    title: str,
    author: str,
    publisher_name: str,
    pub_date: str | None,
    model: str,
    start_page: int,
    end_page: int | None,
    rest_client: RestClient,
    claude_client: ClaudeClient,
    geonames_client: GeoNamesClient,
):
    """Batch extraction pipeline — submits all chunks at once, waits for results.

    Uses the Anthropic Message Batches API (50% cost discount). Interactive review
    is not available in batch mode; all qualifying events are published automatically.
    """
    print(f"Creating source: {title} by {author}")
    source = rest_client.create_source(
        title=title,
        author=author,
        publisher=publisher_name,
        pub_date=pub_date,
    )
    source_id = UUID(source["id"])
    print(f"  Source ID: {source_id}")

    publisher = Publisher(rest_client=rest_client)
    story_id = publisher.ensure_story(source_id=source_id, source_title=title)
    print(f"  Story ID: {story_id}")

    print(f"\nReading PDF: {file_path}")
    pages = extract_pages(file_path=file_path, start_page=start_page, end_page=end_page)
    if not pages:
        print("No text extracted from PDF.")
        return

    chunks = chunk_pages(pages)
    print(f"  {len(pages)} pages -> {len(chunks)} chunks")

    chunk_tuples = [(c.text, c.start_page, c.end_page) for c in chunks]
    batch_id = claude_client.submit_extraction_batch(chunk_tuples, title, author)
    print(f"\nBatch submitted: {batch_id}")
    print("Polling for results (check logs for progress)...")

    batch_results = claude_client.poll_extraction_batch(batch_id)

    chunk_map = {
        f"chunk-{i:04d}-p{c.start_page}-{c.end_page}": c
        for i, c in enumerate(chunks)
    }

    resolver = EntityResolver(
        rest_client=rest_client,
        claude_client=claude_client,
        geonames_client=geonames_client,
    )

    total_extracted = 0
    total_published = 0
    total_skipped = 0

    for custom_id, events in batch_results:
        chunk = chunk_map.get(custom_id)
        total_extracted += len(events)

        for event in events:
            if event.page_num is None and chunk:
                if event.excerpt:
                    event.page_num = chunk.page_for_excerpt(event.excerpt)
                else:
                    event.page_num = chunk.start_page

            try:
                resolved = resolver.resolve_event(event)
            except Exception as e:
                log.error(f"Failed to resolve event: {e}")
                total_skipped += 1
                continue

            if resolved.is_duplicate and not resolved.duplicate_has_wikidata:
                total_skipped += 1
                continue

            try:
                summary_id = publisher.publish_event(
                    event=resolved,
                    source_id=source_id,
                    story_id=story_id,
                )
                if summary_id:
                    total_published += 1
                    print(f"  Published: {event.summary[:60]}...")
                else:
                    total_skipped += 1
            except Exception as e:
                log.error(f"Failed to publish: {e}")
                total_skipped += 1

    _print_summary(total_extracted, total_published, total_skipped)


def _print_summary(extracted: int, published: int, skipped: int):
    print(f"\n{'='*60}")
    print("Pipeline Complete")
    print(f"  Events extracted: {extracted}")
    print(f"  Events published: {published}")
    print(f"  Events skipped:   {skipped}")
    print(f"{'='*60}")
