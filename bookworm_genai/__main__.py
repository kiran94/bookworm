import sys
import logging
import argparse

from bookworm_genai.integrations import browsers, Browser
from bookworm_genai.commands.sync import sync
from bookworm_genai.commands.ask import BookmarkChain

logger = logging.getLogger(__name__)


def main():
    logger.info("[bold green]Starting Bookworm 📖")
    logger.debug("Running on platform '%s'", sys.platform)

    argparser = argparse.ArgumentParser(description="Bookworm - A LLM-powered bookmark search engine")

    sub_parsers = argparser.add_subparsers(dest="command", help="Available commands", required=True)

    sync_parser = sub_parsers.add_parser("sync", help="Sync the bookmark database with the latest changes")
    sync_parser.add_argument("--estimate-cost", action="store_true", default=False, help="Estimate the cost of syncing the bookmark database")
    sync_parser.add_argument("--browser-filter", default=[], help='Only sync a subset of browsers', choices=Browser.list())

    ask_parser = sub_parsers.add_parser("ask", help="Search for a bookmark")
    ask_parser.add_argument("-n", "--top-n", type=int, default=3, help="Number of bookmarks to return")
    ask_parser.add_argument("-q", "--query", help="The Search Query")

    args = argparser.parse_args(sys.argv[1:])

    logger.debug("Arguments: %s", args)

    if args.command == "sync":
        sync(browsers, estimate_cost=args.estimate_cost, browser_filter=args.browser_filter)

    elif args.command == "ask":
        if not args.query:
            logger.info("What would you like to search for?")
            query = input("> ")
        else:
            query = args.query

        logger.debug("query: %s", query)

        with BookmarkChain(vector_store_search_n=args.top_n) as bookmark_chain:
            if not bookmark_chain.is_valid():
                logger.debug("bookmark chain is not valid, exiting early.")
                return

            logger.info("Searching for bookmarks...")
            bookmarks = bookmark_chain.ask(query)

        if not bookmarks.bookmarks:
            logger.info("""
            No bookmarks found for the query 🙁. Please ensure you have performed a "bookworm sync" to update the database
            and the query is relevant to the bookmarks stored.
            """)
            return

        for index, bookmark in enumerate(bookmarks.bookmarks):
            if logger.isEnabledFor(logging.DEBUG):
                # also shows the source of the bookmark
                logger.info(f"[green][{index}] [/] {bookmark.title} - [link={bookmark.url}]{bookmark.url}[/link] ({bookmark.source})")  # pragma: no cover
            else:
                logger.info(f"[green][{index}] [/] {bookmark.title} - [link={bookmark.url}]{bookmark.url}[/link]")

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
    main()  # pragma: no cover
