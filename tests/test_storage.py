import os
from unittest.mock import patch, Mock, call

import pytest
from langchain_openai.embeddings import AzureOpenAIEmbeddings

from bookworm_genai.storage import store_documents, _get_embedding_store


@patch.dict(os.environ, {"OPENAI_API_KEY": "secret"}, clear=True)
@patch("bookworm_genai.storage.OpenAIEmbeddings")
@patch("bookworm_genai.storage.DuckDBVectorStore")
@patch("bookworm_genai.storage.duckdb")
@patch("bookworm_genai.storage.PlatformDirs")
@patch("bookworm_genai.storage.os.makedirs")
def test_store_documents(
    mock_os_makedirs: Mock,
    mock_platform_dirs: Mock,
    mock_duckdb: Mock,
    mock_duckdb_vector: Mock,
    mock_openai_embeddings: Mock,
):
    docs = [Mock(), Mock()]

    mock_user_data_dir = "/test"
    mock_platform_dirs.return_value.user_data_dir = mock_user_data_dir

    store_documents(docs)

    assert mock_platform_dirs.call_args_list == [call("bookworm", "bookworm")]
    assert mock_duckdb.connect.call_args_list == [call(f"{mock_user_data_dir}/bookmarks.duckdb")]
    assert mock_os_makedirs.call_args_list == [call(mock_user_data_dir, exist_ok=True)]

    mock_duckb_connection = mock_duckdb.connect.return_value.__enter__.return_value
    assert mock_duckb_connection.execute.call_args_list == [call("DROP TABLE IF EXISTS embeddings")]
    assert mock_duckdb_vector.from_documents.call_args_list == [call(docs, mock_openai_embeddings.return_value, connection=mock_duckb_connection)]


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


@patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "secret", "AZURE_OPENAI_ENDPOINT": "https://example-resource.azure.openai.com/"}, clear=True)
def test_get_embedding_store_azure():
    assert isinstance(_get_embedding_store(), AzureOpenAIEmbeddings)
