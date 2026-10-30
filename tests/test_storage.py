import os
from unittest.mock import patch, Mock, call

import duckdb
import pytest
from langchain_core.embeddings import FakeEmbeddings
from langchain_openai.embeddings import OpenAIEmbeddings

from bookworm_genai.storage import store_documents, get_last_embedding_model, _get_embedding_model_name, _get_embedding_store


@patch.dict(os.environ, {"OPENAI_API_KEY": "secret"}, clear=True)
@patch("bookworm_genai.storage.DuckDBVectorStore")
@patch("bookworm_genai.storage.duckdb")
@patch("bookworm_genai.storage.PlatformDirs")
@patch("bookworm_genai.storage.os.makedirs")
def test_store_documents(
    mock_os_makedirs: Mock,
    mock_platform_dirs: Mock,
    mock_duckdb: Mock,
    mock_duckdb_vector: Mock,
):
    docs = [Mock(), Mock()]

    mock_user_data_dir = "/test"
    mock_platform_dirs.return_value.user_data_dir = mock_user_data_dir

    store_documents(docs)

    assert mock_platform_dirs.call_args_list == [call("bookworm", "bookworm")]
    assert mock_duckdb.connect.call_args_list == [call(f"{mock_user_data_dir}/bookmarks.duckdb")]
    assert mock_os_makedirs.call_args_list == [call(mock_user_data_dir, exist_ok=True)]

    embeddings = mock_duckdb_vector.from_documents.call_args.args[1]
    assert isinstance(embeddings, OpenAIEmbeddings)

    mock_duckb_connection = mock_duckdb.connect.return_value.__enter__.return_value
    assert mock_duckb_connection.execute.call_args_list == [
        call("DROP TABLE IF EXISTS embeddings"),
        call("DROP TABLE IF EXISTS embedding_model"),
        call("CREATE TABLE embedding_model AS SELECT ? AS model, current_timestamp AT TIME ZONE 'UTC' AS synced_at", [embeddings.model]),
    ]
    assert mock_duckdb_vector.from_documents.call_args_list == [call(docs, embeddings, connection=mock_duckb_connection)]


@patch.dict(os.environ, {}, clear=True)
@patch("bookworm_genai.storage.PlatformDirs")
@patch("bookworm_genai.storage.os.makedirs")
def test_no_proper_embedding_environment(
    mock_os_makedirs: Mock,
    mock_platform_dirs: Mock,
):
    docs = [Mock(), Mock()]

    with pytest.raises(ValueError, match="Embeddings service could not be configured"):
        store_documents(docs)


@patch("bookworm_genai.storage._get_embedding_store")
@patch("bookworm_genai.storage.DuckDBVectorStore")
@patch("bookworm_genai.storage._get_local_store")
def test_store_documents_records_embedding_model(
    mock_local_store: Mock,
    mock_duckdb_vector: Mock,
    mock_embedding_store: Mock,
    tmp_path,
):
    database = str(tmp_path / "bookmarks.duckdb")
    mock_local_store.return_value = database
    mock_embedding_store.return_value = Mock(spec=OpenAIEmbeddings, model="text-embedding-ada-002")

    # repeated syncs replace the single record rather than appending to it, including when the model changes
    for _ in range(2):
        store_documents([Mock()])

    mock_embedding_store.return_value = Mock(spec=OpenAIEmbeddings, model="text-embedding-3-small")
    store_documents([Mock()])

    with duckdb.connect(database) as conn:
        rows = conn.execute("SELECT model, synced_at FROM embedding_model").fetchall()

    assert len(rows) == 1
    assert rows[0][0] == "text-embedding-3-small"
    assert rows[0][1] is not None


def test_get_last_embedding_model():
    with duckdb.connect(":memory:") as conn:
        conn.execute("CREATE TABLE embedding_model AS SELECT 'text-embedding-ada-002' AS model, current_timestamp AS synced_at")

        assert get_last_embedding_model(conn) == "text-embedding-ada-002"


def test_get_last_embedding_model_no_table():
    with duckdb.connect(":memory:") as conn:
        assert get_last_embedding_model(conn) is None


def test_get_last_embedding_model_empty_table():
    with duckdb.connect(":memory:") as conn:
        conn.execute("CREATE TABLE embedding_model (model VARCHAR, synced_at TIMESTAMPTZ)")

        assert get_last_embedding_model(conn) is None


@patch.dict(os.environ, {"OPENAI_API_KEY": "secret"}, clear=True)
def test_get_embedding_model_name():
    assert _get_embedding_model_name(OpenAIEmbeddings(model="text-embedding-3-small")) == "text-embedding-3-small"


def test_get_embedding_model_name_unsupported_embeddings():
    with pytest.raises(TypeError, match="cannot get model name from <class 'langchain_core.embeddings.fake.FakeEmbeddings'>"):
        _get_embedding_model_name(FakeEmbeddings(size=8))


@patch.dict(os.environ, {"OPENAI_API_KEY": "secret"}, clear=True)
@patch("bookworm_genai.storage.OpenAIEmbeddings")
def test_embedding_store_default_model(mock_openai_embeddings: Mock):
    assert _get_embedding_store() == mock_openai_embeddings.return_value
    mock_openai_embeddings.assert_called_once_with(model="text-embedding-3-small")


@patch.dict(os.environ, {"OPENAI_API_KEY": "secret", "BOOKWORM_EMBEDDING_MODEL": "text-embedding-3-large"}, clear=True)
@patch("bookworm_genai.storage.OpenAIEmbeddings")
def test_embedding_store_model_override(mock_openai_embeddings: Mock):
    _get_embedding_store()
    mock_openai_embeddings.assert_called_once_with(model="text-embedding-3-large")
