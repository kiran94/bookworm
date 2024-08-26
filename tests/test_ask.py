import os
from unittest.mock import patch, Mock

import pytest
from langchain_openai import AzureChatOpenAI

from bookworm_genai.commands.ask import BookmarkChain, _system_message, _get_llm
from bookworm_genai.models import Bookmarks


@patch.dict(os.environ, {"OPENAI_API_KEY": "secret"}, clear=True)
@patch("bookworm_genai.commands.ask.ChatPromptTemplate")
@patch("bookworm_genai.commands.ask.ChatOpenAI")
@patch("bookworm_genai.commands.ask.DuckDBVectorStore")
@patch("bookworm_genai.commands.ask.duckdb")
@patch("bookworm_genai.commands.ask._get_embedding_store")
@patch("bookworm_genai.commands.ask._get_local_store")
def test_bookmark_chain_ask(
    mock_local_store: Mock,
    mock_embedding_store: Mock,
    mock_duckdb: Mock,
    mock_duckdb_vector: Mock,
    mock_chatopenai: Mock,
    mock_chat_prompt_template: Mock,
):
    mock_local_store.return_value = "/test/bookmark.duckdb"

    mock_duckdb_connection = Mock()
    mock_duckdb.connect.return_value = mock_duckdb_connection

    mock_embedding = Mock()
    mock_embedding_store.return_value = mock_embedding

    mock_llm = Mock()
    mock_chatopenai.return_value = mock_llm

    mock_chain = Mock(name="chain")
    mock_chat_prompt_template.from_messages.return_value.__ror__.return_value.__or__.return_value = mock_chain

    with BookmarkChain() as bc:
        # If this checks fails then most likely the chain constructed in the BookmarkChain has changed
        # review the mock_chain
        assert mock_chain == bc.chain

        bc.ask("test")

    mock_duckdb.connect.assert_called_once_with("/test/bookmark.duckdb", read_only=False)
    mock_duckdb_vector.assert_called_once_with(connection=mock_duckdb_connection, embedding=mock_embedding)
    mock_duckdb_vector.return_value.as_retriever.assert_called_once_with(search_kwargs={"k": 3})
    assert mock_duckdb_connection.close.called

    mock_chatopenai.assert_called_once_with(temperature=0.0)
    mock_llm.with_structured_output.assert_called_once_with(Bookmarks)
    mock_chat_prompt_template.from_messages.assert_called_once_with([("system", _system_message), ("human", "{query}")])

    mock_chain.invoke.assert_called_once_with("test")


@patch.dict(os.environ, {"OPENAI_API_KEY": "secret"}, clear=True)
@patch("bookworm_genai.commands.ask.ChatPromptTemplate")
@patch("bookworm_genai.commands.ask.ChatOpenAI")
@patch("bookworm_genai.commands.ask.DuckDBVectorStore")
@patch("bookworm_genai.commands.ask.duckdb")
@patch("bookworm_genai.commands.ask._get_embedding_store")
@patch("bookworm_genai.commands.ask._get_local_store")
def test_bookmark_chain_ask_n_parameter(
    mock_local_store: Mock,
    mock_embedding_store: Mock,
    mock_duckdb: Mock,
    mock_duckdb_vector: Mock,
    mock_chatopenai: Mock,
    mock_chat_prompt_template: Mock,
):
    n = 15
    with BookmarkChain(vector_store_search_n=n):
        pass

    mock_duckdb_vector.return_value.as_retriever.assert_called_once_with(search_kwargs={"k": n})


@patch.dict(os.environ, {"OPENAI_API_KEY": "secret"}, clear=True)
@patch("bookworm_genai.commands.ask.ChatPromptTemplate")
@patch("bookworm_genai.commands.ask.ChatOpenAI")
@patch("bookworm_genai.commands.ask.DuckDBVectorStore")
@patch("bookworm_genai.commands.ask.duckdb")
@patch("bookworm_genai.commands.ask._get_embedding_store")
@patch("bookworm_genai.commands.ask._get_local_store")
def test_bookmark_chain_is_valid(
    mock_local_store: Mock,
    mock_embedding_store: Mock,
    mock_duckdb: Mock,
    mock_duckdb_vector: Mock,
    mock_chatopenai: Mock,
    mock_chat_prompt_template: Mock,
):
    mock_duckdb_connection = Mock()
    mock_duckdb.connect.return_value = mock_duckdb_connection

    mock_duckdb_connection.execute.return_value.fetchall.return_value = [(1,)]

    with BookmarkChain() as bc:
        assert bc.is_valid()

    mock_duckdb_connection.execute.assert_called_once_with("SELECT COUNT(*) FROM embeddings")


@patch.dict(os.environ, {"OPENAI_API_KEY": "secret"}, clear=True)
@patch("bookworm_genai.commands.ask.ChatPromptTemplate")
@patch("bookworm_genai.commands.ask.ChatOpenAI")
@patch("bookworm_genai.commands.ask.DuckDBVectorStore")
@patch("bookworm_genai.commands.ask.duckdb")
@patch("bookworm_genai.commands.ask._get_embedding_store")
@patch("bookworm_genai.commands.ask._get_local_store")
def test_bookmark_chain_is_valid_zero_count(
    mock_local_store: Mock,
    mock_embedding_store: Mock,
    mock_duckdb: Mock,
    mock_duckdb_vector: Mock,
    mock_chatopenai: Mock,
    mock_chat_prompt_template: Mock,
):
    mock_duckdb_connection = Mock()
    mock_duckdb.connect.return_value = mock_duckdb_connection

    mock_duckdb_connection.execute.return_value.fetchall.return_value = [(0,)]

    with BookmarkChain() as bc:
        assert not bc.is_valid()


@patch.dict(os.environ, {"OPENAI_API_KEY": "secret"}, clear=True)
@patch("bookworm_genai.commands.ask.ChatPromptTemplate")
@patch("bookworm_genai.commands.ask.ChatOpenAI")
@patch("bookworm_genai.commands.ask.DuckDBVectorStore")
@patch("bookworm_genai.commands.ask.duckdb")
@patch("bookworm_genai.commands.ask._get_embedding_store")
@patch("bookworm_genai.commands.ask._get_local_store")
@pytest.mark.parametrize(
    "duckdb_response",
    [[], None],
)
def test_bookmark_chain_is_valid_invalid_response(
    mock_local_store: Mock,
    mock_embedding_store: Mock,
    mock_duckdb: Mock,
    mock_duckdb_vector: Mock,
    mock_chatopenai: Mock,
    mock_chat_prompt_template: Mock,
    duckdb_response,
):
    mock_duckdb_connection = Mock()
    mock_duckdb.connect.return_value = mock_duckdb_connection

    mock_duckdb_connection.execute.return_value.fetchall.return_value = duckdb_response

    with BookmarkChain() as bc:
        assert not bc.is_valid()


@patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "secret", "OPENAI_API_VERSION": "version", "AZURE_OPENAI_ENDPOINT": "endpoint"}, clear=True)
def test_get_llm_azure():
    assert isinstance(_get_llm(), AzureChatOpenAI)


@patch.dict(os.environ, {}, clear=True)
def test_get_llm_no_env():
    with pytest.raises(ValueError, match="LLM service could not be configured"):
        _get_llm()


@patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "secret", "AZURE_OPENAI_DEPLOYMENT": "DUMMY"}, clear=True)
@patch("bookworm_genai.commands.ask.AzureChatOpenAI")
def test_get_llm_azure_deployment(mock_azure_chat_openai: Mock):
    _get_llm()

    assert mock_azure_chat_openai.call_count == 1

    _, kwargs = mock_azure_chat_openai.call_args_list[0]
    assert kwargs["deployment_name"] == "DUMMY"
