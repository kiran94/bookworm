import sys
import logging
import argparse

from bookworm.commands.sync import sync
from bookworm.commands.ask import ask

logger = logging.getLogger(__name__)


def main():
    logger.info("Starting Bookworm")
    logger.debug("Running on platform '%s'", sys.platform)

    argparser = argparse.ArgumentParser(description="Bookworm - A bookmark manager")

    sub_parsers = argparser.add_subparsers(dest="command", help="Available commands")
    sub_parsers.add_parser("sync", help="Sync the bookmark database with the latest changes")
    sub_parsers.add_parser("ask", help="Ask about a bookmark")

    args = argparser.parse_args()

    logger.debug("Arguments: %s", args)

    if args.command == "sync":
        sync()

    elif args.command == "ask":
        query = input("What do you want to search for? ")
        logger.debug("query: %s", query)

        bookmarks = ask(query)

        for bookmark in bookmarks.bookmarks:
            print(bookmark.title, " - ", bookmark.url)
            print("**********")


if __name__ == "__main__":
    main()
