import os
from enum import Enum
from langchain_community.document_loaders import JSONLoader


class Browser(str, Enum):
    BRAVE = "brave"
    CHROME = "chrome"


_CHROMIUM_JQ_COMMAND = """
  [.roots.bookmark_bar.children, .roots.other.children] |
  flatten |
  .. |
  objects |
  select(.type == "url")
"""

# Configuration for various browsers and details about them
# The bookmark_file_path is the path to the bookmarks file for the browsers, in order for it to be used it must be used in conjunction with
# os.path.expanduser as it may contain environment variables
#
# The platform configuration is keyed off the values from https://docs.python.org/3/library/sys.html#sys.platform
#
browsers = {
    Browser.BRAVE: {
        "linux": {
            "bookmark_loader": JSONLoader,
            "bookmark_loader_kwargs": {
                "file_path": os.path.expanduser("~/.config/BraveSoftware/Brave-Browser/Default/Bookmarks"),
                "jq_schema": _CHROMIUM_JQ_COMMAND,
                "text_content": False,
            },
        },
        "win32": {},
        "darwin": {},
    },
    Browser.CHROME: {
        "linux": {
            "bookmark_loader": JSONLoader,
            "bookmark_loader_kwargs": {
                "file_path": os.path.expanduser("~/.config/google-chrome/Default/Bookmarks"),
                "jq_schema": _CHROMIUM_JQ_COMMAND,
                "text_content": False,
            },
        },
        "win32": {},
        "darwin": {},
    },
}
