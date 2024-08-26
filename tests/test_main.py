from unittest.mock import Mock, patch, call

import pytest

from bookworm_genai.__main__ import main


@patch("bookworm_genai.__main__.sys")
def test_main_no_arguments(mock_sys: Mock):
    mock_sys.argv = ["script"]
    with pytest.raises(SystemExit, match="2"):
        main()


@patch("bookworm_genai.__main__.browsers")
@patch("bookworm_genai.__main__.sync")
@patch("bookworm_genai.__main__.sys")
def test_main_sync(mock_sys: Mock, mock_sync: Mock, mock_browsers: Mock):
    mock_sys.argv = ["script", "sync"]

    main()

    assert mock_sync.call_args_list == [call(mock_browsers, estimate_cost=False)]


@patch("builtins.input")
@patch("bookworm_genai.__main__.BookmarkChain")
@patch("bookworm_genai.__main__.sys")
def test_main_ask(mock_sys: Mock, mock_bookmark_chain: Mock, mock_input: Mock):
    mock_sys.argv = ["script", "ask"]
    mock_input.side_effect = ["pandas column", "0"]

    bc = Mock()
    mock_bookmark_chain.return_value.__enter__.return_value = bc

    bc.is_valid.return_value = True
    bc.ask.return_value = Mock(
        bookmarks=[
            Mock(title="first", url="http://google.com", source="/file/hello.txt"),
            Mock(title="second", url="http://google.com", source="/file/hello.txt"),
        ]
    )

    main()

    # We expect that this is called because in the mock_input above we are selecting index 0 to open
    assert bc.ask.return_value.bookmarks[0].open.called


@patch("builtins.input")
@patch("bookworm_genai.__main__.BookmarkChain")
@patch("bookworm_genai.__main__.sys")
def test_main_ask_query(mock_sys: Mock, mock_bookmark_chain: Mock, mock_input: Mock):
    query = "dummy search query"

    mock_sys.argv = ["script", "ask", "-q", query]
    mock_input.side_effect = ["0"]

    bc = Mock()
    bc.is_valid.return_value = True
    bc.ask.return_value = Mock(
        bookmarks=[
            Mock(title="first", url="http://google.com", source="/file/hello.txt"),
            Mock(title="second", url="http://google.com", source="/file/hello.txt"),
        ]
    )

    mock_bookmark_chain.return_value.__enter__.return_value = bc

    main()

    assert bc.ask.call_args_list == [call(query)]


@patch("builtins.input")
@patch("bookworm_genai.__main__.BookmarkChain")
@patch("bookworm_genai.__main__.sys")
def test_main_ask_not_valid(mock_sys: Mock, mock_bookmark_chain: Mock, mock_input: Mock):
    mock_sys.argv = ["script", "ask"]
    mock_input.side_effect = ["pandas column", "0"]

    bc = Mock()
    mock_bookmark_chain.return_value.__enter__.return_value = bc

    bc.is_valid.return_value = False

    main()

    assert not bc.ask.called


@patch("builtins.input")
@patch("bookworm_genai.__main__.BookmarkChain")
@patch("bookworm_genai.__main__.sys")
def test_main_ask_no_results(mock_sys: Mock, mock_bookmark_chain: Mock, mock_input: Mock, caplog):
    mock_sys.argv = ["script", "ask"]
    mock_input.side_effect = ["pandas column", "0"]

    bc = Mock()
    bc.ask.return_value = Mock(bookmarks=[])
    bc.is_valid.return_value = True

    mock_bookmark_chain.return_value.__enter__.return_value = bc

    main()


@patch("builtins.input")
@patch("bookworm_genai.__main__.BookmarkChain")
@patch("bookworm_genai.__main__.sys")
def test_main_ask_invalid_input(mock_sys: Mock, mock_bookmark_chain: Mock, mock_input: Mock):
    mock_sys.argv = ["script", "ask"]

    # This simulates asking for a bookmark related to pandas columns
    # Then entering an invalid non-numberic input
    # Then entering a out of range index
    # and then entering a valid number to open the bookmark
    mock_input.side_effect = ["pandas column", "NOT_A_NUMBER", "999", "1"]

    bc = Mock()
    mock_bookmark_chain.return_value.__enter__.return_value = bc

    bc.is_valid.return_value = True
    bc.ask.return_value = Mock(
        bookmarks=[
            Mock(title="first", url="http://google.com", source="/file/hello.txt"),
            Mock(title="second", url="http://google.com", source="/file/hello.txt"),
        ]
    )

    main()

    assert bc.ask.return_value.bookmarks[1].open.called
