import duckdb
from langchain_community.vectorstores import DuckDB as DuckDBVectorStore
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from bookworm.models import Bookmarks
from bookworm.storage import full_database_path, _get_embedding_store


_system_message = """
You have knowledge about all the browser bookmarks stored by an individual.
When a user asks a question, you should be able to search the bookmarks and return the most relevant bookmark title and URL.
It could be multiple bookmarks.

The bookmarks available are from the context:
{context}
"""


def ask(query: str) -> Bookmarks:
    llm = ChatOpenAI(temperature=0.0)
    llm = llm.with_structured_output(Bookmarks)

    prompt = ChatPromptTemplate.from_messages([("system", _system_message), ("human", "{query}")])

    with duckdb.connect(full_database_path, read_only=False) as conn:
        vector_store = DuckDBVectorStore(connection=conn, embedding=_get_embedding_store())
        vector_store_rec = vector_store.as_retriever()

        chain = {"context": vector_store_rec, "query": RunnablePassthrough()} | prompt | llm

        response = chain.invoke(query)

        return response
