import json
import logging
import sys
from pathlib import Path
from uuid import UUID

from text_reader.base_client import BaseLLMClient
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
        print(
            "  >> DUPLICATE (same entities already exist — will publish as secondary)"
        )

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
    claude_client: BaseLLMClient,
    geonames_client: GeoNamesClient,
    pdf_page_offset: int = 0,
    state_file: str | None = None,
    _resume_totals: tuple[int, int, int] = (0, 0, 0),
):
    """Main extraction pipeline."""
    # Step 1: Create or get source
    print(f"Creating source: {title} by {author}")
    source = rest_client.create_source(
        title=title,
        author=author,
        publisher=publisher_name,
        pub_date=pub_date,
        pdf_page_offset=pdf_page_offset,
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

    # Create state file for resume support
    if state_file is None:
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        slug = "".join(c if c.isalnum() else "_" for c in title.lower()).strip("_")[:40]
        state_file = str(log_dir / f"{slug}_state.json")

    # Step 4: Initialize resolver
    resolver = EntityResolver(
        rest_client=rest_client,
        claude_client=claude_client,
        geonames_client=geonames_client,
    )

    # Step 5: Process chunks
    total_extracted, total_published, total_skipped = _resume_totals

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
            # Expand excerpt to include surrounding sentence context
            if event.excerpt:
                event.excerpt = _expand_excerpt(event.excerpt, chunk.text)

            # Resolve entities
            try:
                resolved = resolver.resolve_event(event)
            except Exception as e:
                log.error(f"Failed to resolve event: {e}")
                total_skipped += 1
                continue

            # User review
            if not skip_review:
                choice = review_event(
                    resolved, total_extracted - len(events) + event_idx + 1
                )
                if choice == "q":
                    print("\nQuitting.")
                    _save_progress(
                        state_file,
                        file_path=file_path,
                        title=title,
                        author=author,
                        publisher_name=publisher_name,
                        pub_date=pub_date,
                        pdf_page_offset=pdf_page_offset,
                        end_page=end_page,
                        next_start_page=chunk.start_page,
                        totals=(total_extracted, total_published, total_skipped),
                    )
                    _print_summary(
                        total_extracted,
                        total_published,
                        total_skipped,
                        claude_client,
                        len(pages),
                    )
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

        # Save progress after each completed chunk
        next_start = chunk.end_page + 1 if chunk_idx < len(chunks) - 1 else None
        _save_progress(
            state_file,
            file_path=file_path,
            title=title,
            author=author,
            publisher_name=publisher_name,
            pub_date=pub_date,
            pdf_page_offset=pdf_page_offset,
            end_page=end_page,
            next_start_page=next_start,
            totals=(total_extracted, total_published, total_skipped),
        )

    _print_summary(
        total_extracted, total_published, total_skipped, claude_client, len(pages)
    )


def _save_progress(
    state_file: str,
    file_path: str,
    title: str,
    author: str,
    publisher_name: str,
    pub_date: str | None,
    pdf_page_offset: int,
    end_page: int | None,
    next_start_page: int | None,
    totals: tuple[int, int, int],
) -> None:
    """Save pipeline progress so the run can be resumed."""
    state = {
        "file_path": file_path,
        "title": title,
        "author": author,
        "publisher_name": publisher_name,
        "pub_date": pub_date,
        "pdf_page_offset": pdf_page_offset,
        "end_page": end_page,
        "next_start_page": next_start_page,
        "total_extracted": totals[0],
        "total_published": totals[1],
        "total_skipped": totals[2],
    }
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)
    log.debug(f"Progress saved: {state_file}")


def run_resume_sync_pipeline(
    state_file: str,
    skip_review: bool,
    model: str,
    rest_client: RestClient,
    claude_client: BaseLLMClient,
    geonames_client: GeoNamesClient,
):
    """Resume a sync pipeline from a saved state file."""
    with open(state_file) as f:
        state = json.load(f)

    next_start = state.get("next_start_page")
    if next_start is None:
        print("This run already completed — nothing to resume.")
        return

    prev = (
        state["total_extracted"],
        state["total_published"],
        state["total_skipped"],
    )
    print(
        f"Resuming from page {next_start} (prior: {prev[0]} extracted, {prev[1]} published, {prev[2]} skipped)"
    )

    run_pipeline(
        file_path=state["file_path"],
        title=state["title"],
        author=state["author"],
        publisher_name=state.get("publisher_name", "Unknown"),
        pub_date=state.get("pub_date"),
        model=model,
        start_page=next_start,
        end_page=state.get("end_page"),
        skip_review=skip_review,
        rest_client=rest_client,
        claude_client=claude_client,
        geonames_client=geonames_client,
        pdf_page_offset=state.get("pdf_page_offset", 0),
        state_file=state_file,
        _resume_totals=prev,
    )


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
    claude_client: BaseLLMClient,
    geonames_client: GeoNamesClient,
    pdf_page_offset: int = 0,
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
        pdf_page_offset=pdf_page_offset,
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

    # Save state file so the run can be resumed if it crashes during polling/publishing
    state = {
        "batch_id": batch_id,
        "source_id": str(source_id),
        "story_id": str(story_id),
        "chunk_pages": {
            f"chunk-{i:04d}-p{c.start_page}-{c.end_page}": c.start_page
            for i, c in enumerate(chunks)
        },
    }
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    state_path = log_dir / f"{batch_id}.json"
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)
    print(f"State saved: {state_path}")
    print(f"To resume if interrupted: python main.py --resume-batch {state_path}")
    print("Polling for results (check logs for progress)...")

    batch_results, all_invalid = claude_client.poll_extraction_batch(
        batch_id, fix_inline=False
    )

    chunk_map = {
        f"chunk-{i:04d}-p{c.start_page}-{c.end_page}": c for i, c in enumerate(chunks)
    }

    # Fix invalid events via a second batch
    if all_invalid:
        print(f"\nSubmitting fix batch for {len(all_invalid)} invalid events...")
        fix_batch_id = claude_client.submit_fix_batch(all_invalid)
        print(f"Fix batch submitted: {fix_batch_id}")
        fixed_groups = claude_client.poll_fix_batch(fix_batch_id, all_invalid)
        fixed_events: list = []
        for (original, _), replacements in zip(all_invalid, fixed_groups):
            if not replacements:
                log.warning(f"Could not fix event, dropping: {original.summary[:80]!r}")
                continue
            for fixed in replacements:
                still_missing = claude_client._validate_event(fixed)
                if still_missing:
                    log.warning(
                        f"Fixed event still missing {still_missing!r}, dropping: "
                        f"{fixed.summary[:80]!r}"
                    )
                else:
                    fixed_events.append(fixed)
        if fixed_events:
            print(f"  Recovered {len(fixed_events)} events from fix batch")
            batch_results.append(("__fixed__", fixed_events))

    resolver = EntityResolver(
        rest_client=rest_client,
        claude_client=claude_client,
        geonames_client=geonames_client,
    )

    # Assign page numbers, expand excerpts, and flatten all events before pre-resolution
    all_events = []
    for custom_id, events in batch_results:
        chunk = chunk_map.get(custom_id)
        for event in events:
            if event.page_num is None and chunk:
                if event.excerpt:
                    event.page_num = chunk.page_for_excerpt(event.excerpt)
                else:
                    event.page_num = chunk.start_page
            if chunk and event.excerpt:
                event.excerpt = _expand_excerpt(event.excerpt, chunk.text)
            all_events.append(event)

    # Pre-resolve all entities in a single batch before publishing
    if all_events:
        print(f"\nPre-resolving entities for {len(all_events)} events...")
        resolver.pre_resolve(all_events)
        print("Entity pre-resolution complete.")

    total_extracted = len(all_events)
    total_published = 0
    total_skipped = 0

    for event in all_events:
        try:
            resolved = resolver.resolve_event(event)
        except Exception as e:
            log.error(f"Failed to resolve event: {e}")
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

    _print_summary(
        total_extracted, total_published, total_skipped, claude_client, len(pages)
    )


def run_resume_pipeline(
    state_file: str,
    rest_client: RestClient,
    claude_client: BaseLLMClient,
    geonames_client: GeoNamesClient,
):
    """Resume a batch pipeline from a saved state file.

    Use when polling or publishing was interrupted after batch submission. The
    batch results are re-fetched (or waited for if still processing), invalid
    events are fixed via a second batch, and all events are published.
    """
    with open(state_file) as f:
        state = json.load(f)

    batch_id = state["batch_id"]
    source_id = UUID(state["source_id"])
    story_id = UUID(state["story_id"])
    chunk_start_pages: dict[str, int] = state.get("chunk_pages", {})

    print(f"Resuming batch: {batch_id}")
    print(f"  Source: {source_id}")
    print(f"  Story:  {story_id}")
    print("Polling for results (check logs for progress)...")

    batch_results, all_invalid = claude_client.poll_extraction_batch(
        batch_id, fix_inline=False
    )

    if all_invalid:
        print(f"\nSubmitting fix batch for {len(all_invalid)} invalid events...")
        fix_batch_id = claude_client.submit_fix_batch(all_invalid)
        print(f"Fix batch submitted: {fix_batch_id}")
        fixed_groups = claude_client.poll_fix_batch(fix_batch_id, all_invalid)
        fixed_events: list = []
        for (original, _), replacements in zip(all_invalid, fixed_groups):
            if not replacements:
                log.warning(f"Could not fix event, dropping: {original.summary[:80]!r}")
                continue
            for fixed in replacements:
                still_missing = claude_client._validate_event(fixed)
                if still_missing:
                    log.warning(
                        f"Fixed event still missing {still_missing!r}, dropping: "
                        f"{fixed.summary[:80]!r}"
                    )
                else:
                    fixed_events.append(fixed)
        if fixed_events:
            print(f"  Recovered {len(fixed_events)} events from fix batch")
            batch_results.append(("__fixed__", fixed_events))

    publisher = Publisher(rest_client=rest_client)
    resolver = EntityResolver(
        rest_client=rest_client,
        claude_client=claude_client,
        geonames_client=geonames_client,
    )

    # Assign page numbers and flatten all events before pre-resolution
    all_events = []
    for custom_id, events in batch_results:
        start_page = chunk_start_pages.get(custom_id)
        for event in events:
            if event.page_num is None and start_page is not None:
                event.page_num = start_page
            all_events.append(event)

    # Pre-resolve all entities in a single batch before publishing
    if all_events:
        print(f"\nPre-resolving entities for {len(all_events)} events...")
        resolver.pre_resolve(all_events)
        print("Entity pre-resolution complete.")

    total_extracted = len(all_events)
    total_published = 0
    total_skipped = 0

    for event in all_events:
        try:
            resolved = resolver.resolve_event(event)
        except Exception as e:
            log.error(f"Failed to resolve event: {e}")
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

    _print_summary(total_extracted, total_published, total_skipped, claude_client)


_ABBREVS = frozenset(
    [
        "mr",
        "mrs",
        "ms",
        "dr",
        "prof",
        "rev",
        "lt",
        "col",
        "gen",
        "capt",
        "sgt",
        "st",
        "ave",
        "blvd",
        "vol",
        "no",
        "op",
        "pp",
        "p",
        "vs",
        "jan",
        "feb",
        "mar",
        "apr",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
        "etc",
        "i.e",
        "e.g",
        "viz",
    ]
)


def _normalize_text(text: str) -> str:
    """Normalize PDF extraction artifacts for reliable substring matching."""
    # Remove soft hyphens and line-break hyphens
    text = text.replace("\u00ad", "")  # soft hyphen
    text = text.replace("-\n", "")
    # Normalize dashes to ASCII hyphen
    for ch in "\u2013\u2014\u2012\u2015":  # en-dash, em-dash, figure dash, horz bar
        text = text.replace(ch, "-")
    # Normalize quotation marks
    for ch in "\u2018\u2019\u201b":  # left/right single quote, reversed
        text = text.replace(ch, "'")
    for ch in "\u201c\u201d\u201e\u201f":  # left/right double quote variants
        text = text.replace(ch, '"')
    return text


def _is_sentence_end(text: str, dot_pos: int) -> bool:
    """Return True if the '.' (or '!' or '?') at dot_pos ends a sentence.

    Filters out abbreviations like "Feb.", "Dr.", "op.", "p.".
    """
    if text[dot_pos] in "!?":
        return True
    # Extract the alphabetic word immediately before the dot
    word_end = dot_pos
    word_start = word_end - 1
    while word_start >= 0 and text[word_start].isalpha():
        word_start -= 1
    word = text[word_start + 1 : word_end].lower()
    # No alpha chars before dot (e.g. a year "1843." or close-paren) — treat as sentence end
    if not word:
        return True
    if word in _ABBREVS or len(word) <= 2:
        return False
    return True


def _find_sentence_end(text: str, start: int) -> int:
    """Return the index one past the sentence-ending punctuation at or after `start`."""
    i = start
    while i < len(text):
        if text[i] in ".!?" and (i + 1 >= len(text) or text[i + 1] in " \t\n\r"):
            if _is_sentence_end(text, i):
                return i + 1
        if i + 1 < len(text) and text[i] == "\n" and text[i + 1] == "\n":
            return i
        i += 1
    return len(text)


def _find_sentence_start(text: str, before: int) -> int:
    """Return the start of the sentence that ends before position `before`.

    Walks backward past one sentence boundary to find the start of the
    *preceding* sentence, giving context.  Stops at a paragraph break.
    """
    i = before - 1
    boundaries_found = 0
    while i >= 0:
        if i + 1 < len(text) and text[i] == "\n" and text[i + 1] == "\n":
            return i + 2
        if text[i] in ".!?" and i + 1 < len(text) and text[i + 1] in " \t\n\r":
            if _is_sentence_end(text, i):
                boundaries_found += 1
                if boundaries_found == 2:
                    return i + 2
        i -= 1
    return 0


def _expand_excerpt(excerpt: str, chunk_text: str) -> str:
    """Expand a short excerpt to include the preceding sentence and the following sentence.

    Works on a normalized copy of both strings to handle PDF artifacts (soft
    hyphens, en/em dashes, smart quotes), then maps the result back to the
    original chunk_text so the citation text is authentic.
    """
    norm_chunk = _normalize_text(chunk_text)
    norm_excerpt = _normalize_text(excerpt)

    pos = norm_chunk.find(norm_excerpt)
    if pos == -1:
        return excerpt  # can't locate — return the original short excerpt

    norm_excerpt_end = pos + len(norm_excerpt)

    # Find the start of the sentence *before* the one containing the excerpt.
    start = _find_sentence_start(norm_chunk, pos)

    # Find the end of the excerpt's own sentence, then the end of the sentence after it.
    excerpt_sentence_end = _find_sentence_end(norm_chunk, norm_excerpt_end)
    end = _find_sentence_end(norm_chunk, excerpt_sentence_end)

    # Map positions back to original text.  Since normalization can only
    # shorten the string, we use a character-by-character walk to find the
    # corresponding positions in the original.
    orig_start = _map_position(chunk_text, norm_chunk, start)
    orig_end = _map_position(chunk_text, norm_chunk, end)

    return chunk_text[orig_start:orig_end].strip()


def _map_position(original: str, normalized: str, norm_pos: int) -> int:
    """Map a position in `normalized` back to a position in `original`.

    The normalization removes characters (hyphens, dashes, quotes) so we walk
    both strings in parallel, counting only characters that survive in `normalized`.
    """
    if norm_pos == 0:
        return 0
    if norm_pos >= len(normalized):
        return len(original)

    norm_idx = 0
    norm_target = norm_pos

    # Rebuild the normalized string character-by-character from the original
    # to find the correspondence.
    i = 0
    while i < len(original) and norm_idx < norm_target:
        # Simulate the normalization rules
        if original[i] == "\u00ad":  # soft hyphen — removed
            i += 1
            continue
        if i + 1 < len(original) and original[i] == "-" and original[i + 1] == "\n":
            # "-\n" removed
            i += 2
            continue
        if original[i] in "\u2013\u2014\u2012\u2015":  # dash → "-"
            norm_idx += 1
            i += 1
            continue
        if original[i] in "\u2018\u2019\u201b":  # single quote
            norm_idx += 1
            i += 1
            continue
        if original[i] in "\u201c\u201d\u201e\u201f":  # double quote
            norm_idx += 1
            i += 1
            continue
        norm_idx += 1
        i += 1

    return i


def _print_summary(
    extracted: int,
    published: int,
    skipped: int,
    claude_client: BaseLLMClient,
    pages: int = 0,
):
    cost = claude_client.total_cost()
    cost_per_event = (cost / published) if published else 0.0
    cost_per_page = (cost / pages) if pages else 0.0
    print(f"\n{'='*60}")
    print("Pipeline Complete")
    print(f"  Events extracted: {extracted}")
    print(f"  Events published: {published}")
    print(f"  Events skipped:   {skipped}")
    print(f"  Claude cost:      ${cost:.4f}")
    if published:
        print(f"  Cost/event:       ${cost_per_event:.4f}")
    if pages:
        print(f"  Cost/page:        ${cost_per_page:.4f}  ({pages} pages)")
    print(f"{'='*60}")
    log.info(
        f"Pipeline complete — extracted: {extracted}, published: {published}, "
        f"skipped: {skipped}, cost: ${cost:.4f}"
        + (f", cost/event: ${cost_per_event:.4f}" if published else "")
        + (f", cost/page: ${cost_per_page:.4f}" if pages else "")
    )
