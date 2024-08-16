import os
import duckdb
import logging

from platformdirs import PlatformDirs
from langchain_community.vectorstores import DuckDB as DuckDBVectorStore
from langchain_core.documents import Document
from langchain_core.embeddings.embeddings import Embeddings
from langchain_openai.embeddings import OpenAIEmbeddings, AzureOpenAIEmbeddings

logger = logging.getLogger(__name__)


def store_documents(docs: list[Document]):
    full_database_path = _get_local_store()

    embeddings = _get_embedding_store()

    logger.info(f"vectorizing and storing {len(docs)} documents into {full_database_path}")
    with duckdb.connect(full_database_path) as conn:
        logger.debug("dropping existing embeddings table if exists")
        conn.execute("DROP TABLE IF EXISTS embeddings")

        logger.debug("loading documents")
        DuckDBVectorStore.from_documents(docs, embeddings, connection=conn)


def _get_local_store() -> str:
    appdirs = PlatformDirs("bookworm", "bookworm")
    database_name = "bookmarks.duckdb"
    full_database_path = os.path.join(appdirs.user_data_dir, database_name)

    logger.debug(f"creating folder {appdirs.user_data_dir}")
    os.makedirs(appdirs.user_data_dir, exist_ok=True)

    return full_database_path


def _get_embedding_store() -> Embeddings:
    if os.environ.get("AZURE_OPENAI_API_KEY", None):
        logger.debug("Using Azure OpenAI Embeddings")
        # https://api.python.langchain.com/en/latest/embeddings/langchain_openai.embeddings.azure.AzureOpenAIEmbeddings.html
        return AzureOpenAIEmbeddings()

    elif os.environ.get("OPENAI_API_KEY", None):
        logger.debug("Using OpenAI Embeddings")
        # https://api.python.langchain.com/en/latest/embeddings/langchain_openai.embeddings.base.OpenAIEmbeddings.html
        return OpenAIEmbeddings()

    else:
        raise ValueError("""
            Embeddings service could not be configured. Ensure you have OPENAI_API_KEY or AZURE_OPENAI_API_KEY.

            If you are using OpenAI then please ensure you have the OPENAI_API_KEY environment variable set.
            If you are using Azure OpenAI then please ensure you have the AZURE_OPENAI_API_KEY + AZURE_OPENAI_ENDPOINT environment variable set.
        """)
