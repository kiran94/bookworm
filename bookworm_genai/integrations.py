import os
from enum import Enum
from typing import Any

from langchain_community.document_loaders import JSONLoader
from langchain_community.document_loaders.sql_database import SQLDatabaseLoader
from langchain_community.utilities.sql_database import SQLDatabase

from bookworm_genai.utils import CHROMIUM_JQ_COMMAND, sql_loader_page_content_mapper, sql_loader_firefox_copy_path, sql_loader_firefox_sql_query


class Browser(str, Enum):
    BRAVE = "brave"
    CHROME = "chrome"
    FIREFOX = "firefox"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


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
                "jq_schema": CHROMIUM_JQ_COMMAND,
                "text_content": False,
            },
        },
        "darwin": {
            "bookmark_loader": JSONLoader,
            "bookmark_loader_kwargs": {
                "file_path": os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser/Default/Bookmarks"),
                "jq_schema": CHROMIUM_JQ_COMMAND,
                "text_content": False,
            },
        },
        # "win32": {},
    },
    Browser.CHROME: {
        "linux": {
            "bookmark_loader": JSONLoader,
            "bookmark_loader_kwargs": {
                "file_path": os.path.expanduser("~/.config/google-chrome/Default/Bookmarks"),
                "jq_schema": CHROMIUM_JQ_COMMAND,
                "text_content": False,
            },
        },
        "darwin": {
            "bookmark_loader": JSONLoader,
            "bookmark_loader_kwargs": {
                "file_path": os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Bookmarks"),
                "jq_schema": CHROMIUM_JQ_COMMAND,
                "text_content": False,
            },
        },
        # "win32": {},
    },
    Browser.FIREFOX: {
        "linux": {
            "bookmark_loader": SQLDatabaseLoader,
            "bookmark_loader_kwargs": {
                "db": lambda _: SQLDatabase.from_uri("sqlite:////tmp/bookworm/firefox.sqlite"),
                "query": sql_loader_firefox_sql_query(),
                "source_columns": ["source"],
                "page_content_mapper": lambda row: sql_loader_page_content_mapper(row),
            },
            "copy": {
                "from": sql_loader_firefox_copy_path(),
                "to": "/tmp/bookworm/firefox.sqlite",
            },
        },
        "darwin": {
            "bookmark_loader": SQLDatabaseLoader,
            "bookmark_loader_kwargs": {
                "db": lambda _: SQLDatabase.from_uri("sqlite:////tmp/bookworm/firefox.sqlite"),
                "query": sql_loader_firefox_sql_query(),
                "source_columns": ["source"],
                "page_content_mapper": lambda row: sql_loader_page_content_mapper(row),
            },
            "copy": {
                "from": sql_loader_firefox_copy_path(),
                "to": "/tmp/bookworm/firefox.sqlite",
            },
        },
        # "win32": {},
    },
}
