from unittest.mock import call, patch, Mock

import pytest

from bookworm_genai.models import Bookmark


@pytest.mark.parametrize(
    "platform, expected_subprocess_call",
    [
        ("linux", call(["xdg-open", "https://www.google.com"])),
        ("win32", call(["start", "https://www.google.com"], shell=True)),
        ("darwin", call(["open", "https://www.google.com"])),
    ],
)
@patch("bookworm_genai.models.subprocess")
@patch("bookworm_genai.models.sys")
def test_bookmark_open(mock_platform: Mock, mock_subprocess: Mock, platform: str, expected_subprocess_call: call):
    mock_platform.platform = platform

    bookmark = Bookmark(title="Google", url="https://www.google.com", source="Google")
    bookmark.open()

    assert mock_subprocess.Popen.call_args == expected_subprocess_call


@patch("bookworm_genai.models.logger")
@patch("bookworm_genai.models.subprocess")
@patch("bookworm_genai.models.sys")
def test_bookmark_unsupported_os(mock_platform: Mock, mock_subprocess: Mock, mock_logger: Mock):
    mock_platform.platform = "chromeos"

    bookmark = Bookmark(title="Google", url="https://www.google.com", source="Google")
    bookmark.open()

    assert mock_logger.warning.call_args == call('Platform "chromeos" not supported. Printing URL instead')
    assert mock_logger.info.call_args == call("https://www.google.com")
