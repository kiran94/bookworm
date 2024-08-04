import os

import duckdb
from langchain_community.vectorstores import DuckDB as DuckDBVectorStore
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.language_models.chat_models import BaseChatModel

from bookworm_genai.models import Bookmarks
from bookworm_genai.storage import full_database_path, _get_embedding_store


_system_message = """
You have knowledge about all the browser bookmarks stored by an individual.
When a user asks a question, you should be able to search the bookmarks and return the most relevant bookmark title and URL.
It could be multiple bookmarks.

The bookmarks available are from the context:
{context}
"""


def ask(query: str) -> Bookmarks:
    llm = _get_llm()
    llm = llm.with_structured_output(Bookmarks)

    prompt = ChatPromptTemplate.from_messages([("system", _system_message), ("human", "{query}")])

    with duckdb.connect(full_database_path, read_only=False) as conn:
        vector_store = DuckDBVectorStore(connection=conn, embedding=_get_embedding_store())
        vector_store_rec = vector_store.as_retriever()

        chain = {"context": vector_store_rec, "query": RunnablePassthrough()} | prompt | llm

        response = chain.invoke(query)

        return response


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
