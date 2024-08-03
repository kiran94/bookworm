import sys
import logging
import argparse

import duckdb
from langchain_community.vectorstores import DuckDB as DuckDBVectorStore

from bookworm.commands.sync import sync
from bookworm.storage import full_database_path, _get_embedding_store

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

        from langchain_openai.llms import OpenAI
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.runnables import RunnablePassthrough

        system_message = """
        You have knowledge about all the browser bookmarks stored by an individual.
        When a user asks a question, you should be able to search the bookmarks and return the most relevant bookmark title and URL.

        The bookmarks available are from the context:
        {context}
        """

        llm = OpenAI(temperature=0.0)
        prompt = ChatPromptTemplate.from_messages([("system", system_message), ("human", "{query}")])
        output_parser = StrOutputParser()

        with duckdb.connect(full_database_path, read_only=False) as conn:
            vector_store = DuckDBVectorStore(connection=conn, embedding=_get_embedding_store())
            vector_store_rec = vector_store.as_retriever()

            chain = {"context": vector_store_rec, "query": RunnablePassthrough()} | prompt | llm | output_parser

            response = chain.invoke(query)

            print(response)


if __name__ == "__main__":
    main()
