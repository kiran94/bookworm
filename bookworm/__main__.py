import sys
import logging
import argparse

from rich.console import Console
from bookworm.commands.sync import sync
from bookworm.commands.ask import ask

logger = logging.getLogger(__name__)


def main():
    logger.info("Starting Bookworm")
    logger.debug("Running on platform '%s'", sys.platform)

    argparser = argparse.ArgumentParser(description="Bookworm - A LLM-powered bookmark search engine")

    sub_parsers = argparser.add_subparsers(dest="command", help="Available commands")
    sub_parsers.add_parser("sync", help="Sync the bookmark database with the latest changes")
    sub_parsers.add_parser("ask", help="Search for a bookmark")

    args = argparser.parse_args()

    logger.debug("Arguments: %s", args)

    if args.command == "sync":
        sync()

    elif args.command == "ask":
        logger.info("What would you like to search for?")
        query = input("> ")

        logger.debug("query: %s", query)
        bookmarks = ask(query)

        console = Console()

        for index, bookmark in enumerate(bookmarks.bookmarks):
            console.print(f"[green][{index}] [/] {bookmark.title} - [link={bookmark.url}]{bookmark.url}[/link]")  # {bookmark.url}")

        logger.info("Press a number to open the bookmark:")
        while True:
            try:
                raw_input = input("> ")
                selected_index = int(raw_input)
                bookmarks.bookmarks[selected_index].open()

                break
            except ValueError:
                logger.warning(f"Invalid input: '{raw_input}'. Please enter a number.")
            except IndexError:
                logger.warning(f"Invalid index: '{selected_index}'. Please select a valid index.")


if __name__ == "__main__":
    main()
