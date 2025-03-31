from unittest.mock import patch, Mock
import pytest

from wiki_service.wiki_service import WikiService
from main import main


@patch("main.create_wiki_service")
def test_main_with_works_of_art(mock_create_service):
    mock_service = Mock(spec=WikiService)
    mock_create_service.return_value = mock_service

    # Test with both num_people and num_works
    main(num_people=5, num_works=3)
    mock_service.run.assert_called_once_with(num_people=5, num_works=3)

    # Reset mocks
    mock_service.reset_mock()

    # Test with only num_people
    main(num_people=5)
    mock_service.run.assert_called_once_with(num_people=5, num_works=None)

    # Reset mocks
    mock_service.reset_mock()

    # Test with only num_works
    main(num_works=3)
    mock_service.run.assert_called_once_with(num_people=None, num_works=3)

    # Reset mocks
    mock_service.reset_mock()

    # Test with no arguments
    main()
    mock_service.run.assert_called_once_with(num_people=None, num_works=None) 