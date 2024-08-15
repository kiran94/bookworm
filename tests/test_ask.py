import os
from unittest.mock import patch, Mock

from bookworm_genai.commands.ask import BookmarkChain, _system_message
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
        assert bc.is_valid() == True

    mock_duckdb_connection.execute.assert_called_once_with("SELECT COUNT(*) FROM embeddings")
