import logging

import fitz  # PyMuPDF

log = logging.getLogger(__name__)

TARGET_CHUNK_SIZE = 25_000  # ~6K tokens — keeps output volume manageable for dense text


class PageText:
    def __init__(self, text: str, page_num: int):
        self.text = text
        self.page_num = page_num


class Chunk:
    def __init__(
        self,
        text: str,
        start_page: int,
        end_page: int,
        page_starts: list[tuple[int, int]] | None = None,
    ):
        self.text = text
        self.start_page = start_page
        self.end_page = end_page
        # (char_offset_within_chunk, page_num) sorted ascending
        self._page_starts: list[tuple[int, int]] = page_starts or []

    def page_for_char(self, char_offset: int) -> int:
        """Return the page number for the given char offset within this chunk."""
        page = self.start_page
        for offset, page_num in self._page_starts:
            if offset <= char_offset:
                page = page_num
            else:
                break
        return page

    def page_for_excerpt(self, excerpt: str) -> int:
        """Find the page number for an excerpt string within this chunk.
        Falls back to start_page if the excerpt is not found."""
        idx = self.text.find(excerpt[:80])  # match on first 80 chars to handle truncation
        if idx != -1:
            return self.page_for_char(idx)
        return self.start_page

    def __repr__(self):
        return (
            f"Chunk(pages {self.start_page}-{self.end_page}, "
            f"{len(self.text)} chars)"
        )


def extract_pages(
    file_path: str,
    start_page: int = 1,
    end_page: int | None = None,
) -> list[PageText]:
    """Extract text from a PDF file, returning text per page."""
    doc = fitz.open(file_path)
    total_pages = len(doc)
    if end_page is None or end_page > total_pages:
        end_page = total_pages

    pages = []
    for page_num in range(start_page - 1, end_page):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            pages.append(PageText(text=text, page_num=page_num + 1))

    doc.close()
    log.info(
        f"Extracted {len(pages)} pages from {file_path} "
        f"(pages {start_page}-{end_page})"
    )
    return pages


def _find_break_point(text: str, target: int) -> int:
    """Find a natural break point near the target position.
    Searches backward from target for paragraph, line, or sentence breaks."""
    # Search backward up to 5000 chars for a break
    search_start = max(0, target - 5000)
    search_region = text[search_start:target]

    # Prefer paragraph break
    para_break = search_region.rfind("\n\n")
    if para_break != -1:
        return search_start + para_break + 2

    # Fall back to line break
    line_break = search_region.rfind("\n")
    if line_break != -1:
        return search_start + line_break + 1

    # Fall back to sentence break
    sentence_break = search_region.rfind(". ")
    if sentence_break != -1:
        return search_start + sentence_break + 2

    # Last resort: break at target
    return target


def chunk_pages(
    pages: list[PageText],
    target_size: int = TARGET_CHUNK_SIZE,
) -> list[Chunk]:
    """Combine pages into chunks of approximately target_size characters.
    Tracks page boundaries for citation purposes."""
    if not pages:
        return []

    # Concatenate all text with page tracking
    full_text = ""
    page_boundaries: list[tuple[int, int]] = []  # (char_offset, page_num)

    for page in pages:
        page_boundaries.append((len(full_text), page.page_num))
        full_text += page.text

    if not full_text.strip():
        return []

    chunks = []
    pos = 0

    while pos < len(full_text):
        end = pos + target_size
        if end >= len(full_text):
            end = len(full_text)
        else:
            end = _find_break_point(full_text, end)

        chunk_text = full_text[pos:end]

        # Determine page range and per-page offsets within this chunk
        start_page = pages[0].page_num
        end_page = pages[-1].page_num
        chunk_page_starts: list[tuple[int, int]] = []
        for offset, page_num in page_boundaries:
            if offset <= pos:
                start_page = page_num
            if offset < end:
                end_page = page_num
            if pos < offset < end:
                chunk_page_starts.append((offset - pos, page_num))

        chunks.append(
            Chunk(
                text=chunk_text,
                start_page=start_page,
                end_page=end_page,
                page_starts=chunk_page_starts,
            )
        )
        pos = end

    log.info(f"Created {len(chunks)} chunks from {len(pages)} pages")
    return chunks
