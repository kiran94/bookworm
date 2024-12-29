import os
from getpass import getuser
import sys
from unittest.mock import patch, Mock, call, ANY

import pytest

from bookworm_genai.commands.sync import _estimate_cost, sync
from bookworm_genai.integrations import Browser, browsers
from bookworm_genai.metadata import Metadata


def _mock_browsers_config(platform: str = "linux", mocked_documents: list[any] = ["DOC1", "DOC2"]):
    new_browsers = browsers.copy()

    for browser, config in new_browsers.items():
        mock_loader = Mock()
        mock_loader.return_value.lazy_load.return_value = mocked_documents

        for platform in config:
            try:
                config[platform]["bookmark_loader"] = mock_loader
            except KeyError:
                continue

            if "db" in config[platform]["bookmark_loader_kwargs"]:
                mock_sqlite = Mock()
                mock_sqlite.return_value.return_value._engine.url = "mocked_database_connection"

                config[platform]["bookmark_loader_kwargs"]["db"] = mock_sqlite

    return new_browsers


def _collect_browser_calls(platform: str, browsers: dict) -> tuple[list[str], list[call]]:
    collected_file_paths: list[str] = []
    collected_loader_calls: list[call] = []

    for browser, config in browsers.items():
        if platform not in config:
            continue

        if "file_path" in config[platform]["bookmark_loader_kwargs"]:
            collected_file_paths.append(config[platform]["bookmark_loader_kwargs"]["file_path"])
        elif "db" in config[platform]["bookmark_loader_kwargs"]:
            path = config[platform]["bookmark_loader_kwargs"]["db"]
            if callable(path):
                path = path(path)
                collected_file_paths.append(path._engine.url)

        collected_loader_calls.extend(config[platform]["bookmark_loader"].call_args_list)

    return collected_file_paths, collected_loader_calls


@pytest.mark.skipif(sys.platform != 'linux', reason='this test is only for linux')
@patch.dict(browsers, _mock_browsers_config(), clear=True)
@patch("bookworm_genai.commands.sync.glob")
@patch("bookworm_genai.commands.sync.shutil")
@patch("bookworm_genai.commands.sync.os.makedirs")
@patch("bookworm_genai.commands.sync.store_documents")
@patch("bookworm_genai.commands.sync.sys")
def test_sync_linux(mock_sys: Mock, mock_store_documents: Mock, mock_makedirs: Mock, mock_shutil: Mock, mock_glob: Mock):
    platform = "linux"

    mock_sys.platform = platform
    user = getuser()
    mock_glob.glob.return_value = ["/mocked/firefox.sqlite"]

    browsers = _mock_browsers_config()
    sync(browsers)

    collected_file_paths, collected_loader_calls = _collect_browser_calls(platform, browsers)

    assert collected_file_paths == [
        f"/home/{user}/.config/BraveSoftware/Brave-Browser/Default/Bookmarks",
        f"/home/{user}/.config/google-chrome/Default/Bookmarks",
        "mocked_database_connection",
    ]

    assert collected_loader_calls == [
        call(
            file_path=ANY,
            jq_schema='\n  [.roots.bookmark_bar.children, .roots.other.children] |\n  flatten |\n  .. |\n  objects |\n  select(.type == "url")\n',
            text_content=False,
        ),
        call(
            file_path=ANY,
            jq_schema='\n  [.roots.bookmark_bar.children, .roots.other.children] |\n  flatten |\n  .. |\n  objects |\n  select(.type == "url")\n',
            text_content=False,
        ),
        call(db=ANY, query=ANY, source_columns=["id", "dateAdded", "lastModified"], page_content_mapper=ANY),
    ]

    assert mock_store_documents.call_args_list == [call(["DOC1", "DOC2", "DOC1", "DOC2", "DOC1", "DOC2"])]
    assert mock_makedirs.call_args_list == [call("/tmp/bookworm", exist_ok=True)]
    assert mock_shutil.copy.call_args_list == [call(mock_glob.glob.return_value[0], "/tmp/bookworm/firefox.sqlite")]


@pytest.mark.skipif(sys.platform != 'darwin', reason='this test is only for macos')
@patch.dict(browsers, _mock_browsers_config(), clear=True)
@patch("bookworm_genai.commands.sync.glob")
@patch("bookworm_genai.commands.sync.shutil")
@patch("bookworm_genai.commands.sync.os.makedirs")
@patch("bookworm_genai.commands.sync.store_documents")
@patch("bookworm_genai.commands.sync.sys")
def test_sync_macos(mock_sys: Mock, mock_store_documents: Mock, mock_makedirs: Mock, mock_shutil: Mock, mock_glob: Mock):
    platform = "darwin"

    mock_sys.platform = platform
    user = getuser()

    browsers = _mock_browsers_config(platform, mocked_documents=[Mock('DOC1', metadata={}), Mock('DOC2', metadata={})])
    sync(browsers)

    collected_file_paths, collected_loader_calls = _collect_browser_calls(platform, browsers)

    assert collected_file_paths == [
        # brave
        f'/Users/{user}/Library/Application Support/BraveSoftware/Brave-Browser/Default/Bookmarks',
        # chrome
        f"/Users/{user}/Library/Application Support/Google/Chrome/Default/Bookmarks",
        # firefox
        'mocked_database_connection',
    ]
    assert collected_loader_calls == [
        # brave
        call(
            file_path=f"/Users/{user}/Library/Application Support/BraveSoftware/Brave-Browser/Default/Bookmarks",
            jq_schema='\n  [.roots.bookmark_bar.children, .roots.other.children] |\n  flatten |\n  .. |\n  objects |\n  select(.type == "url")\n',
            text_content=False,
        ),
        # chrome
        call(
            file_path=f"/Users/{user}/Library/Application Support/Google/Chrome/Default/Bookmarks",
            jq_schema='\n  [.roots.bookmark_bar.children, .roots.other.children] |\n  flatten |\n  .. |\n  objects |\n  select(.type == "url")\n',
            text_content=False,
        ),
        # firefox
        call(db=ANY, query=ANY, source_columns=["id", "dateAdded", "lastModified"], page_content_mapper=ANY),
    ]


@patch("bookworm_genai.commands.sync.store_documents")
@patch.dict(browsers, _mock_browsers_config(), clear=True)
@patch("bookworm_genai.commands.sync.sys")
def test_sync_platform_unsupported(mock_sys: Mock, mock_store_documents: Mock, caplog):
    platform = "unsupported"

    mock_sys.platform = platform

    browsers = _mock_browsers_config()
    sync(browsers)

    assert not mock_store_documents.called

    logs = [log.message for log in caplog.records if log.levelname == "WARNING"]
    logs.sort()
    assert logs == [
       '🔄 browser brave is not supported on unsupported yet',
       '🔄 browser chrome is not supported on unsupported yet',
       '🔄 browser firefox is not supported on unsupported yet',
    ]


@patch.dict(os.environ, {"OPENAI_API_KEY": "secret"}, clear=True)
@patch.dict(browsers, _mock_browsers_config(), clear=True)
@patch("builtins.input")
@patch("bookworm_genai.commands.sync.tiktoken")
@patch("bookworm_genai.commands.sync.glob")
@patch("bookworm_genai.commands.sync.shutil")
@patch("bookworm_genai.commands.sync.os.makedirs")
@patch("bookworm_genai.commands.sync.store_documents")
@patch("bookworm_genai.commands.sync.sys")
def test_sync_estimate_cost(
    mock_sys: Mock,
    mock_store_documents: Mock,
    mock_makedirs: Mock,
    mock_shutil: Mock,
    mock_glob: Mock,
    mock_tiktoken: Mock,
    mocked_input: Mock,
    caplog,
):
    platform = "linux"
    mock_sys.platform = platform

    mock_encoding = Mock()
    mock_encoding.encode.return_value = "mocked_page_content" * 100  # The multiplier just simulates a larger document
    mock_tiktoken.encoding_for_model.return_value = mock_encoding

    # At the time of writing ada v2 is priced at $0.100 per 1M tokens
    # so this is what we are using for this unit test
    # https://openai.com/api/pricing/
    mocked_input.return_value = "0.100"

    mocked_documents = [
        Mock(page_content="mocked_page_content", metadata={}),
    ]

    browsers = _mock_browsers_config(mocked_documents=mocked_documents)
    cost = sync(browsers, estimate_cost=True)

    assert not mock_store_documents.called
    assert mock_encoding.encode.call_args_list == [
        call("mocked_page_content"),
        call("mocked_page_content"),
        call("mocked_page_content"),
    ]

    assert cost == 0.0005700000000000001

@patch.dict(os.environ, {"OPENAI_API_KEY": "secret"}, clear=True)
@patch("builtins.input")
@patch("bookworm_genai.commands.sync.tiktoken")
def test_sync_estimate_cost_non_interactive(mock_tiktoken: Mock, mock_input: Mock):
    mocked_documents = [
        Mock(page_content="mocked_page_content"),
    ]

    mock_encoding = Mock()
    mock_encoding.encode.return_value = "mocked_page_content" * 100  # The multiplier just simulates a larger document
    mock_tiktoken.encoding_for_model.return_value = mock_encoding

    cost = _estimate_cost(mocked_documents, cost_per_million=0.100)

    assert cost == 0.00019
    assert not mock_input.called


@patch("bookworm_genai.commands.sync.glob")
@patch("bookworm_genai.commands.sync.shutil")
@patch("bookworm_genai.commands.sync.os.makedirs")
@patch("bookworm_genai.commands.sync.store_documents")
@patch("bookworm_genai.commands.sync.sys")
def test_sync_browser_filter(
    mock_sys: Mock,
    mock_store_documents: Mock,
    mock_makedirs: Mock,
    mock_shutil: Mock,
    mock_glob: Mock):

    browser_filter = [Browser.CHROME.value]

    platform = 'darwin'
    mock_sys.platform = platform

    browsers = _mock_browsers_config(mocked_documents=[Mock('DOC1', metadata={}), Mock('DOC2', metadata={})])
    sync(browsers, browser_filter=browser_filter)

    assert browsers[Browser.CHROME][platform]['bookmark_loader'].called
    assert not browsers[Browser.FIREFOX][platform]['bookmark_loader'].called



@patch('bookworm_genai.commands.sync.store_documents')
@patch('bookworm_genai.commands.sync.os')
@patch('bookworm_genai.commands.sync.shutil')
@patch('bookworm_genai.commands.sync.glob')
def test_sync_copy_source_missing(mock_glob: Mock, mock_shutil: Mock, mock_os: Mock, mock_store_documents: Mock):

    path_to_missing_file = "/path/to/missing/file"

    mock_docs_loader = Mock()
    mock_docs_loader.return_value.lazy_load.return_value = [Mock("DOC1", metadata={}), Mock("DOC2", metadata={})]

    browsers = {
        # this one will fail and be skipped due to missing file
        # ensure that even if this one fails, the next one will still be processed
        Browser.FIREFOX: {
            sys.platform: {
                "bookmark_loader": Mock(),
                "bookmark_loader_kwargs": {},
                "copy": {
                    "from": path_to_missing_file,
                    "to": "/path/to/destination",
                },
            }
        },
        # this one will be processed
        Browser.CHROME: {
            sys.platform: {
                "bookmark_loader": mock_docs_loader,
                "bookmark_loader_kwargs": {},
            }
        },
    }

    mock_glob.glob.return_value = []

    sync(browsers=browsers)

    mock_glob.glob.assert_called_once_with(path_to_missing_file)

    # ensures that even if the first browser fails, the second one still extracts docs and submits to storage
    assert mock_store_documents.call_count == 1
    assert len(mock_store_documents.call_args_list[0]) == 2

@patch('bookworm_genai.commands.sync.store_documents')
def test_sync_metadata_attached(store_document: Mock):

    document_mock = Mock('DOC1', metadata={})
    mock_browsers = _mock_browsers_config(sys.platform, [document_mock])

    sync(mock_browsers, browser_filter=Browser.CHROME)

    assert document_mock.metadata == {
        Metadata.Browser.value: Browser.CHROME.value
    }