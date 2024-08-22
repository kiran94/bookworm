import os
from getpass import getuser
from unittest.mock import patch, Mock, call, ANY

from bookworm_genai.commands.sync import sync
from bookworm_genai.integrations import browsers


def _mock_browsers_config(platform: str = "linux", mocked_documents: list[any] = ["DOC1", "DOC2"]):
    new_browsers = browsers.copy()

    for browser, config in new_browsers.items():
        mock_loader = Mock()
        mock_loader.return_value.lazy_load.return_value = mocked_documents

        config[platform]["bookmark_loader"] = mock_loader

        if "db" in config[platform]["bookmark_loader_kwargs"]:
            mock_sqlite = Mock()
            mock_sqlite.return_value.return_value._engine.url = "mocked_database_connection"

            config[platform]["bookmark_loader_kwargs"]["db"] = mock_sqlite

    return new_browsers


@patch.dict(browsers, _mock_browsers_config(), clear=True)
@patch("bookworm_genai.commands.sync.glob")
@patch("bookworm_genai.commands.sync.shutil")
@patch("bookworm_genai.commands.sync.os.makedirs")
@patch("bookworm_genai.commands.sync.store_documents")
@patch("bookworm_genai.commands.sync.sys")
def test_sync(mock_sys: Mock, mock_store_documents: Mock, mock_makedirs: Mock, mock_shutil: Mock, mock_glob: Mock):
    platform = "linux"

    mock_sys.platform = platform
    user = getuser()
    mock_glob.glob.return_value = ["/mocked/firefox.sqlite"]

    browsers = _mock_browsers_config()
    sync(browsers)

    collected_file_paths: list[str] = []
    collected_loader_calls: list[call] = []

    for browser, config in browsers.items():
        if "file_path" in config[platform]["bookmark_loader_kwargs"]:
            collected_file_paths.append(config[platform]["bookmark_loader_kwargs"]["file_path"])
        elif "db" in config[platform]["bookmark_loader_kwargs"]:
            path = config[platform]["bookmark_loader_kwargs"]["db"]
            if callable(path):
                path = path(path)
                collected_file_paths.append(path._engine.url)

        collected_loader_calls.extend(config[platform]["bookmark_loader"].call_args_list)

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
        "Platform unsupported not supported for browser brave",
        "Platform unsupported not supported for browser chrome",
        "Platform unsupported not supported for browser firefox",
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
        Mock(page_content="mocked_page_content"),
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
