import os
import duckdb
import logging
from typing import Optional

from platformdirs import PlatformDirs
from langchain_community.vectorstores import DuckDB as DuckDBVectorStore
from langchain_community.vectorstores.duckdb import DEFAULT_TABLE_NAME
from langchain_core.documents import Document
from langchain_core.embeddings.embeddings import Embeddings
from langchain_openai.embeddings import OpenAIEmbeddings

logger = logging.getLogger(__name__)

# single record table tracking the embedding model used during the last sync
EMBEDDING_MODEL_TABLE_NAME = "embedding_model"


def store_documents(docs: list[Document]):
    full_database_path = _get_local_store()

    embeddings = _get_embedding_store()

    logger.info(f"vectorizing and storing {len(docs)} documents locally")
    logger.debug(f"storing into {full_database_path}")

    with duckdb.connect(full_database_path) as conn:
        logger.debug(f"dropping existing embeddings table '{DEFAULT_TABLE_NAME}' if exists")
        conn.execute(f"DROP TABLE IF EXISTS {DEFAULT_TABLE_NAME}")

        # dropped up front so a failed sync does not leave a record for embeddings that were never stored
        logger.debug(f"dropping existing embedding model table '{EMBEDDING_MODEL_TABLE_NAME}' if exists")
        conn.execute(f"DROP TABLE IF EXISTS {EMBEDDING_MODEL_TABLE_NAME}")

        logger.debug(f"loading {len(docs)} documents")
        DuckDBVectorStore.from_documents(docs, embeddings, connection=conn)

        model = _get_embedding_model_name(embeddings)
        logger.debug(f"recording embedding model '{model}' into '{EMBEDDING_MODEL_TABLE_NAME}'")
        # synced_at is stored as a plain TIMESTAMP in UTC; TIMESTAMPTZ would require pytz to read back in python
        conn.execute(f"CREATE TABLE {EMBEDDING_MODEL_TABLE_NAME} AS SELECT ? AS model, current_timestamp AT TIME ZONE 'UTC' AS synced_at", [model])


def get_last_embedding_model(conn: duckdb.DuckDBPyConnection) -> Optional[str]:
    """
    Returns the embedding model recorded during the last sync, or None if no record exists
    (e.g. sync has never been run or the database was created by an older version of bookworm).
    """
    try:
        res = conn.execute(f"SELECT model FROM {EMBEDDING_MODEL_TABLE_NAME} LIMIT 1").fetchone()
    except duckdb.CatalogException:
        logger.debug(f"table '{EMBEDDING_MODEL_TABLE_NAME}' does not exist")
        return None

    return res[0] if res else None


def _get_embedding_model_name(embeddings: Embeddings) -> str:
    # NOTE: .model is not part of the Embeddings contract (see also sync._estimate_cost)
    # if we add more embeddings options in the future, we need to re-evaluate this.
    return embeddings.model


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
        raise ValueError("Embeddings service could not be configured. Ensure you have OPENAI_API_KEY set.")
