import os
import duckdb
import logging

from platformdirs import PlatformDirs
from langchain_community.vectorstores import DuckDB as DuckDBVectorStore
from langchain_community.vectorstores.duckdb import DEFAULT_TABLE_NAME
from langchain_core.documents import Document
from langchain_core.embeddings.embeddings import Embeddings
from langchain_openai.embeddings import OpenAIEmbeddings

logger = logging.getLogger(__name__)


def store_documents(docs: list[Document]):
    full_database_path = _get_local_store()

    embeddings = _get_embedding_store()

    logger.info(f"vectorizing and storing {len(docs)} documents into {full_database_path}")
    with duckdb.connect(full_database_path) as conn:
        logger.debug(f"dropping existing embeddings table '{DEFAULT_TABLE_NAME}' if exists")
        conn.execute(f"DROP TABLE IF EXISTS {DEFAULT_TABLE_NAME}")

        logger.debug(f"loading {len(docs)} documents")
        DuckDBVectorStore.from_documents(docs, embeddings, connection=conn)


def _get_local_store() -> str:
    appdirs = PlatformDirs("bookworm", "bookworm")
    database_name = "bookmarks.duckdb"
    full_database_path = os.path.join(appdirs.user_data_dir, database_name)

    logger.debug(f"creating folder {appdirs.user_data_dir}")
    os.makedirs(appdirs.user_data_dir, exist_ok=True)

    return full_database_path


def _get_embedding_store() -> Embeddings:
    if os.environ.get("OPENAI_API_KEY", None):
        logger.debug("Using OpenAI Embeddings")
        # https://api.python.langchain.com/en/latest/embeddings/langchain_openai.embeddings.base.OpenAIEmbeddings.html
        return OpenAIEmbeddings()

    else:
        raise ValueError('Embeddings service could not be configured. Ensure you have OPENAI_API_KEY set.')
