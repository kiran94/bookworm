import os
import logging

import duckdb
from langchain_community.vectorstores import DuckDB as DuckDBVectorStore
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.language_models.chat_models import BaseChatModel

from bookworm_genai.models import Bookmarks
from bookworm_genai.storage import full_database_path, _get_embedding_store

logger = logging.getLogger(__name__)


_system_message = """
You have knowledge about all the browser bookmarks stored by an individual.
When a user asks a question, you should be able to search the bookmarks and return the most relevant bookmark title and URL.
It could be multiple bookmarks.

The bookmarks available are from the context:
{context}
"""


class BookmarkChain:
    def __init__(self):
        self._duckdb_connection = duckdb.connect(full_database_path, read_only=False)
        self.vector_store = DuckDBVectorStore(connection=self._duckdb_connection, embedding=_get_embedding_store())

        llm = _get_llm()
        llm = llm.with_structured_output(Bookmarks)

        prompt = ChatPromptTemplate.from_messages([("system", _system_message), ("human", "{query}")])

        self.chain = {"context": self.vector_store.as_retriever(), "query": RunnablePassthrough()} | prompt | llm

    def ask(self, query: str) -> Bookmarks:
        logger.debug("Searching for bookmarks with query: %s", query)

        return self.chain.invoke(query)

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

    elif os.environ.get("AZURE_OPENAI_API_KEY"):
        # https://api.python.langchain.com/en/latest/chat_models/langchain_openai.chat_models.azure.AzureChatOpenAI.html
        return AzureChatOpenAI(**kwargs)

    else:
        raise ValueError("No OpenAI API key found in environment variables")