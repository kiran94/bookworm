from getpass import getuser
from unittest.mock import patch, Mock, call, ANY

from bookworm_genai.commands.sync import sync
from bookworm_genai.integrations import browsers


def _mock_browsers_config(platform: str = "linux"):
    new_browsers = browsers.copy()

    for browser, config in new_browsers.items():
        mock_loader = Mock()
        mock_loader.return_value.lazy_load.return_value = ["DOC1", "DOC2"]

        config[platform]["bookmark_loader"] = mock_loader

    return new_browsers


@patch("bookworm_genai.commands.sync.store_documents")
@patch.dict(browsers, _mock_browsers_config(), clear=True)
@patch("bookworm_genai.commands.sync.sys")
def test_sync(mock_sys: Mock, mock_store_documents: Mock):
    platform = "linux"

    mock_sys.platform = platform
    user = getuser()

    browsers = _mock_browsers_config()
    sync(browsers)

    collected_file_paths: list[str] = []
    collected_loader_calls: list[call] = []

    for browser, config in browsers.items():
        collected_file_paths.append(config[platform]["bookmark_loader_kwargs"]["file_path"])
        collected_loader_calls.extend(config[platform]["bookmark_loader"].call_args_list)

    assert collected_file_paths == [
        f"/home/{user}/.config/BraveSoftware/Brave-Browser/Default/Bookmarks",
        f"/home/{user}/.config/google-chrome/Default/Bookmarks",
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
    ]

    assert mock_store_documents.call_args_list == [call(["DOC1", "DOC2", "DOC1", "DOC2"])]


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
    assert logs == ["Platform unsupported not supported for browser brave", "Platform unsupported not supported for browser chrome"]
