import os
from enum import Enum
from typing import Any

from langchain_community.document_loaders import JSONLoader
from langchain_community.document_loaders.sql_database import SQLDatabaseLoader
from langchain_community.utilities.sql_database import SQLDatabase


class Browser(str, Enum):
    BRAVE = "brave"
    CHROME = "chrome"
    FIREFOX = "firefox"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


_CHROMIUM_JQ_COMMAND = """
  [.roots.bookmark_bar.children, .roots.other.children] |
  flatten |
  .. |
  objects |
  select(.type == "url")
"""

BrowserManifest = dict[Browser, dict[str, dict[str, Any]]]

# Configuration for various browsers and details about them
# The bookmark_file_path is the path to the bookmarks file for the browsers, in order for it to be used it must be used in conjunction with
# os.path.expanduser as it may contain environment variables
#
# The platform configuration is keyed off the values from https://docs.python.org/3/library/sys.html#sys.platform
#
browsers: BrowserManifest = {
    Browser.BRAVE: {
        "linux": {
            "bookmark_loader": JSONLoader,
            "bookmark_loader_kwargs": {
                "file_path": os.path.expanduser("~/.config/BraveSoftware/Brave-Browser/Default/Bookmarks"),
                "jq_schema": _CHROMIUM_JQ_COMMAND,
                "text_content": False,
            },
        },
        # "win32": {},
        "darwin": {
            "bookmark_loader": JSONLoader,
            "bookmark_loader_kwargs": {
                "file_path": os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser/Default/Bookmarks"),
                "jq_schema": _CHROMIUM_JQ_COMMAND,
                "text_content": False,
            },
        },
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
        # "win32": {},
        "darwin": {
            "bookmark_loader": JSONLoader,
            "bookmark_loader_kwargs": {
                "file_path": os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Bookmarks"),
                "jq_schema": _CHROMIUM_JQ_COMMAND,
                "text_content": False,
            },
        },
    },
    Browser.FIREFOX: {
        "linux": {
            "bookmark_loader": SQLDatabaseLoader,
            "bookmark_loader_kwargs": {
                "db": lambda _: SQLDatabase.from_uri("sqlite:////tmp/bookworm/firefox.sqlite"),
                "query": """
                    SELECT
                       CAST(moz_places.id AS TEXT) AS id,
                       moz_bookmarks.title,
                       moz_places.url,
                       CAST(moz_bookmarks.dateAdded AS TEXT) AS dateAdded,
                       CAST(moz_bookmarks.lastModified AS TEXT) AS lastModified
                    FROM
                       moz_bookmarks
                    LEFT JOIN
                       moz_places
                    ON
                       moz_bookmarks.fk = moz_places.id
                    WHERE
                       moz_bookmarks.type = 1
                    AND
                       moz_bookmarks.title IS NOT NULL
                """,
                "source_columns": ["id", "dateAdded", "lastModified"],
                "page_content_mapper": lambda row: row["title"] + row["url"],
            },
            "copy": {
                "from": os.path.expanduser("~/.mozilla/firefox/*.default-release/places.sqlite"),
                "to": "/tmp/bookworm/firefox.sqlite",
            },
        },
        # "win32": {},
        "darwin": {
            "bookmark_loader": SQLDatabaseLoader,
            "bookmark_loader_kwargs": {
                "db": lambda _: SQLDatabase.from_uri("sqlite:////tmp/bookworm/firefox.sqlite"),
                "query": """
                    SELECT
                       CAST(moz_places.id AS TEXT) AS id,
                       moz_bookmarks.title,
                       moz_places.url,
                       CAST(moz_bookmarks.dateAdded AS TEXT) AS dateAdded,
                       CAST(moz_bookmarks.lastModified AS TEXT) AS lastModified
                    FROM
                       moz_bookmarks
                    LEFT JOIN
                       moz_places
                    ON
                       moz_bookmarks.fk = moz_places.id
                    WHERE
                       moz_bookmarks.type = 1
                    AND
                       moz_bookmarks.title IS NOT NULL
                """,
                "source_columns": ["id", "dateAdded", "lastModified"],
                "page_content_mapper": lambda row: row["title"] + row["url"],
            },
            "copy": {
                "from": os.path.expanduser('~/Library/Application Support/Firefox/Profiles/*.default-release/places.sqlite'),
                "to": "/tmp/bookworm/firefox.sqlite",
            },
        },
    },
}
