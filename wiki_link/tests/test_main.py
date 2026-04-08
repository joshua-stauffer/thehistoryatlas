from unittest.mock import patch, Mock
import pytest

from wiki_service.wiki_service import WikiService
from main import main

NUM_PEOPLE = 5
NUM_WORKS = 3
NUM_BOOKS = 2
NUM_ORATIONS = 4


class TestMain:
    @patch("main.create_wiki_service")
    def test_build_options(self, mock_create_service):
        mock_service = Mock(spec=WikiService)
        mock_create_service.return_value = mock_service

        main(
            num_people=NUM_PEOPLE,
            num_works=NUM_WORKS,
            num_books=NUM_BOOKS,
            num_orations=NUM_ORATIONS,
        )
        mock_service.build.assert_called_once_with(
            num_people=NUM_PEOPLE,
            num_works=NUM_WORKS,
            num_books=NUM_BOOKS,
            num_orations=NUM_ORATIONS,
        )

    @patch("main.create_wiki_service")
    def test_people(self, mock_create_service):
        mock_service = Mock(spec=WikiService)
        mock_create_service.return_value = mock_service

        main(num_people=NUM_PEOPLE)
        mock_service.build.assert_called_once_with(
            num_people=NUM_PEOPLE, num_works=None, num_books=None, num_orations=None
        )

    @patch("main.create_wiki_service")
    def test_works(self, mock_create_service):
        mock_service = Mock(spec=WikiService)
        mock_create_service.return_value = mock_service

        main(num_works=NUM_WORKS)
        mock_service.build.assert_called_once_with(
            num_people=None, num_works=NUM_WORKS, num_books=None, num_orations=None
        )

    @patch("main.create_wiki_service")
    def test_books(self, mock_create_service):
        mock_service = Mock(spec=WikiService)
        mock_create_service.return_value = mock_service

        main(num_books=NUM_BOOKS)
        mock_service.build.assert_called_once_with(
            num_people=None, num_works=None, num_books=NUM_BOOKS, num_orations=None
        )

    @patch("main.create_wiki_service")
    def test_orations(self, mock_create_service):
        mock_service = Mock(spec=WikiService)
        mock_create_service.return_value = mock_service

        # Test with only num_orations
        main(num_orations=NUM_ORATIONS)
        mock_service.build.assert_called_once_with(
            num_people=None, num_works=None, num_books=None, num_orations=NUM_ORATIONS
        )

    @patch("main.create_wiki_service")
    def test_run(self, mock_create_service):
        mock_service = Mock(spec=WikiService)
        mock_create_service.return_value = mock_service

        # Test with no arguments
        main(run=True)
        mock_service.run.assert_called_once_with()
