import os
import logging

import duckdb
from langchain_community.vectorstores import DuckDB as DuckDBVectorStore
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.language_models.chat_models import BaseChatModel

from bookworm_genai.models import Bookmarks
from bookworm_genai.storage import _get_local_store, _get_embedding_store

logger = logging.getLogger(__name__)


_system_message = """
You have knowledge about all the browser bookmarks stored by an individual.
When a user asks a question, you should be able to search the bookmarks and return the most relevant bookmark title and URL.
It could be multiple bookmarks.
If you don't have anything in the context then return empty list

The bookmarks available are from the context:
{context}
"""


class BookmarkChain:
    def __init__(self, vector_store_search_n: int = 3):
        full_database_path = _get_local_store()
        logger.debug("Connecting to vector database at: %s", full_database_path)
        self._duckdb_connection = duckdb.connect(full_database_path, read_only=False)
        self.vector_store = DuckDBVectorStore(connection=self._duckdb_connection, embedding=_get_embedding_store())

        llm = _get_llm()
        llm = llm.with_structured_output(Bookmarks)

        prompt = ChatPromptTemplate.from_messages([("system", _system_message), ("human", "{query}")])

        search_kwargs = {"k": vector_store_search_n}

        self.chain = {"context": self.vector_store.as_retriever(search_kwargs=search_kwargs), "query": RunnablePassthrough()} | prompt | llm

    def ask(self, query: str) -> Bookmarks:
        logger.debug("Searching for bookmarks with query: %s", query)

        return self.chain.invoke(query)

    def is_valid(self) -> bool:
        res = self._duckdb_connection.execute("SELECT COUNT(*) FROM embeddings").fetchall()

        try:
            res = res[0][0]
        except (IndexError, TypeError) as e:
            logger.warning("validation check failed due to unexpected response from the database.")
            logger.debug("Error: %s", e)
            logger.debug("Raw DuckDB Response: %s", res)

            return False

        if res == 0:
            logger.warning("No bookmarks were found in database. Please ensure you run 'bookworm sync' before asking questions")
            return False
        else:
            return True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.debug("Closing DuckDB connection")

        self._duckdb_connection.close()


def _get_llm() -> BaseChatModel:
    kwargs = {
        "temperature": 0.0,
    }

    if os.environ.get("OPENAI_API_KEY"):
        # https://api.python.langchain.com/en/latest/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html
        return ChatOpenAI(**kwargs)

    else:
        raise ValueError('LLM service could not be configured. Ensure you have OPENAI_API_KEY. If you are using OpenAI then please ensure you have the OPENAI_API_KEY environment variable set.')
