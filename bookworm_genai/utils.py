import json
import sys
import os
from sqlalchemy import RowMapping
from functools import cache


## CHROMIUM

CHROMIUM_JQ_COMMAND = """
  [.roots.bookmark_bar.children, .roots.other.children] |
  flatten |
  .. |
  objects |
  select(.type == "url")
"""

## SQL LOADER


def sql_loader_page_content_mapper(row: RowMapping) -> str:
    """
    Dictates how a SQL Loader row maps into page content stored into the vector database.

    This is required because the langchain SQLLoader and JSONLoader output different formats so this function is inplace
    to ensure that the output is consistent.
    """
    row = dict(row)
    row["name"] = row["title"]
    del row["title"]

    return json.dumps(row)


@cache
def sql_loader_firefox_copy_path() -> str:
    """
    Returns the path to the Firefox database file for the SQL Loader.
    """
    if sys.platform == "linux":
        return os.path.expanduser("~/.mozilla/firefox/*.default-release/places.sqlite")
    elif sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/Firefox/Profiles/*.default-release/places.sqlite")
    else:
        raise NotImplementedError(f"Platform {sys.platform} is not supported")


@cache
def sql_loader_firefox_sql_query() -> str:
    """
    Generates the SQL query for the SQL Loader to extract the bookmarks from the Firefox database.
    This query also embeds a literal column called 'source' which is the path to the database file. This is needed in the query so
    that when the SQL Loader runs we can tell it to put this source into the metadata.
    """
    return f"""
        SELECT
            CAST(moz_places.id AS TEXT) AS id,
            moz_bookmarks.title,
            moz_places.url,
            CAST(moz_bookmarks.dateAdded AS TEXT) AS dateAdded,
            CAST(moz_bookmarks.lastModified AS TEXT) AS lastModified,
            '{sql_loader_firefox_copy_path()}' as source
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
    """
