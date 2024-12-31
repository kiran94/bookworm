from unittest.mock import Mock, patch, call

import pandas as pd

from bookworm_genai.commands.export import export


@patch("bookworm_genai.commands.export._get_local_store")
@patch("bookworm_genai.commands.export.duckdb")
def test_export(mock_duckdb: Mock, mock_get_local_store: Mock):
    df = pd.DataFrame(
        data={
            "id": ["id"],
            "text": ['{"name": "my_bookmark", "url": "https://bookmark.com"}'],
            "embedding": [1],
            "metadata": ['{"source": "my_source", "browser": "chrome"}'],
        }
    )

    mock_duckdb.connect.return_value.__enter__.return_value.execute.return_value.df.return_value = df

    result = export()

    assert mock_duckdb.connect.call_args_list == [call(mock_get_local_store.return_value, read_only=True)]

    expected_df = pd.DataFrame(data={"name": "my_bookmark", "url": "https://bookmark.com", "browser": "chrome", "source": "my_source"}, index=[0])
    pd.testing.assert_frame_equal(expected_df, result)
