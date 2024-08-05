import os
import duckdb
import logging

from platformdirs import PlatformDirs
from langchain_community.vectorstores import DuckDB as DuckDBVectorStore
from langchain_core.documents import Document
from langchain_core.embeddings.embeddings import Embeddings
from langchain_openai.embeddings import OpenAIEmbeddings, AzureOpenAIEmbeddings

appdirs = PlatformDirs("bookworm", "bookworm")
database_name = "bookmark.duckdb"
full_database_path = os.path.join(appdirs.user_data_dir, database_name)

logger = logging.getLogger(__name__)


def store_documents(docs: list[Document]):
    logger.debug(f"creating folder {appdirs.user_data_dir}")
    os.makedirs(appdirs.user_data_dir, exist_ok=True)

    embeddings = _get_embedding_store()

    logger.info(f"vectorizing and storing {len(docs)} documents into {full_database_path}")
    with duckdb.connect(full_database_path) as conn:
        logger.debug("dropping existing embeddings table if exists")
        conn.execute("DROP TABLE IF EXISTS embeddings")

        logger.debug("loading documents")
        DuckDBVectorStore.from_documents(docs, embeddings, connection=conn)


def _get_embedding_store() -> Embeddings:
    if os.environ.get("AZURE_OPENAI_API_KEY"):
        logger.debug("Using Azure OpenAI Embeddings")
        return AzureOpenAIEmbeddings()

    elif os.environ.get("OPENAI_API_KEY"):
        logger.debug("Using OpenAI Embeddings")
        return OpenAIEmbeddings()

    else:
        raise ValueError("No OpenAI API key found in environment variables")
