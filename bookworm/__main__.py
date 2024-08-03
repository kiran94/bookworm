import sys
import logging
import argparse

import duckdb
from langchain_community.vectorstores import DuckDB as DuckDBVectorStore
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from bookworm.commands.sync import sync
from bookworm.storage import full_database_path, _get_embedding_store
from bookworm.models import Bookmarks

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

    # sync = refresh the bookmark database with the latest changes
    if args.command == "sync":
        sync()

    elif args.command == "ask":
        query = input("What do you want to search for? ")
        print(query)

        system_message = """
        You have knowledge about all the browser bookmarks stored by an individual.
        When a user asks a question, you should be able to search the bookmarks and return the most relevant bookmark title and URL.
        It could be multiple bookmarks.

        The bookmarks available are from the context:
        {context}
        """

        llm = ChatOpenAI(temperature=0.0)
        llm = llm.with_structured_output(Bookmarks)

        prompt = ChatPromptTemplate.from_messages([("system", system_message), ("human", "{query}")])

        with duckdb.connect(full_database_path, read_only=False) as conn:
            vector_store = DuckDBVectorStore(connection=conn, embedding=_get_embedding_store())
            vector_store_rec = vector_store.as_retriever()

            chain = {"context": vector_store_rec, "query": RunnablePassthrough()} | prompt | llm

            response = chain.invoke(query)

            for bookmark in response.bookmarks:
                print(bookmark.title, " - ", bookmark.url)
                print("**********")


if __name__ == "__main__":
    main()
