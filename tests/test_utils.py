from unittest.mock import Mock, patch

import pytest
from bookworm_genai.utils import sql_loader_firefox_copy_path, sql_loader_page_content_mapper


def test_sql_loader_page_content_mapper():
    row = {"id": 1, "title": "title", "url": "url", "dateAdded": "dateAdded", "lastModified": "lastModified", "source": "source"}

    result = sql_loader_page_content_mapper(row)
    assert result == '{"id": 1, "url": "url", "dateAdded": "dateAdded", "lastModified": "lastModified", "source": "source", "name": "title"}'


@pytest.mark.parametrize(
    "platform,mocked_expanduser",
    [
        pytest.param("linux", "/home/user/.mozilla/firefox/*.default-release/places.sqlite", id="linux"),
        pytest.param("darwin", "/Users/user/Library/Application Support/Firefox/Profiles/*.default-release/places.sqlite", id="darwin"),
    ],
)
@patch("bookworm_genai.utils.os.path.expanduser")
@patch("bookworm_genai.utils.sys")
def test_sql_loader_firefox_copy_path_linux(mock_sys: Mock, mock_expanduser: Mock, platform: str, mocked_expanduser: str):
    sql_loader_firefox_copy_path.cache_clear()

    mock_sys.platform = platform
    mock_expanduser.return_value = mocked_expanduser

    assert sql_loader_firefox_copy_path() == mocked_expanduser


@patch("bookworm_genai.utils.sys")
def test_sql_loader_firefox_copy_path_unknown(mock_sys: Mock):
    sql_loader_firefox_copy_path.cache_clear()

    mock_sys.platform = "unknown"

    with pytest.raises(NotImplementedError, match="Platform unknown is not supported"):
        sql_loader_firefox_copy_path()
