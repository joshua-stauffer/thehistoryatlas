"""Tests for PDF reader chunking logic."""

import pytest

from text_reader.pdf_reader import (
    PageText,
    Chunk,
    _find_break_point,
    chunk_pages,
)


class TestFindBreakPoint:
    def test_prefers_paragraph_break(self):
        text = "Hello world.\n\nNext paragraph starts here."
        target = 20

        result = _find_break_point(text, target)

        assert result == text.index("\n\n") + 2

    def test_falls_back_to_line_break(self):
        text = "First line.\nSecond line continues for a while."
        target = 20

        result = _find_break_point(text, target)

        assert result == text.index("\n") + 1

    def test_falls_back_to_sentence_break(self):
        text = "First sentence. Second sentence continues."
        target = 25

        result = _find_break_point(text, target)

        assert result == text.index(". ") + 2

    def test_returns_target_when_no_break_found(self):
        text = "abcdefghijklmnopqrstuvwxyz"
        target = 15

        result = _find_break_point(text, target)

        assert result == target


class TestChunkPages:
    def test_returns_empty_for_empty_input(self):
        result = chunk_pages([])

        assert result == []

    def test_returns_empty_for_whitespace_only(self):
        pages = [PageText(text="   \n\n  ", page_num=1)]

        result = chunk_pages(pages)

        assert result == []

    def test_single_small_page_is_one_chunk(self):
        pages = [PageText(text="Short text.", page_num=1)]

        result = chunk_pages(pages, target_size=1000)

        assert len(result) == 1

    def test_preserves_text_content(self):
        pages = [PageText(text="Hello world.", page_num=1)]

        result = chunk_pages(pages, target_size=1000)

        assert result[0].text == "Hello world."

    def test_tracks_start_page(self):
        pages = [PageText(text="Page five text.", page_num=5)]

        result = chunk_pages(pages, target_size=1000)

        assert result[0].start_page == 5

    def test_tracks_end_page(self):
        pages = [
            PageText(text="a" * 100, page_num=1),
            PageText(text="b" * 100, page_num=2),
        ]

        result = chunk_pages(pages, target_size=10000)

        assert result[0].end_page == 2

    def test_splits_large_text_into_multiple_chunks(self):
        pages = [PageText(text="word " * 500, page_num=1)]

        result = chunk_pages(pages, target_size=100)

        assert len(result) > 1

    def test_all_text_is_preserved_across_chunks(self):
        original_text = "Hello. " * 200
        pages = [PageText(text=original_text, page_num=1)]

        result = chunk_pages(pages, target_size=100)
        reconstructed = "".join(c.text for c in result)

        assert reconstructed == original_text

    def test_chunk_repr(self):
        chunk = Chunk(text="some text", start_page=1, end_page=3)

        assert "1-3" in repr(chunk)
        assert "9 chars" in repr(chunk)
