import json
import logging

import pandas as pd
import duckdb

from bookworm_genai.storage import _get_local_store

logger = logging.getLogger(__name__)


def export() -> pd.DataFrame:
    store = _get_local_store()

    logger.debug(f"reading from vector store {store}")
    with duckdb.connect(store, read_only=True) as duck:
        df = duck.execute("select * from embeddings").df()

    logger.debug("extracting useful information from structured columns")
    browser_col = df["metadata"].apply(json.loads).apply(lambda x: x["browser"]).rename(index="browser")
    source_col = df["metadata"].apply(json.loads).apply(lambda x: x["source"]).rename(index="source")
    name_col = df["text"].apply(json.loads).apply(lambda x: x["name"]).rename(index="name")
    url_col = df["text"].apply(json.loads).apply(lambda x: x["url"]).rename(index="url")

    logger.debug("dropping unnecessary columns")
    cleaned_df = df.drop(columns=["id", "metadata", "text", "embedding"])

    bookmark_summary_df = pd.concat([cleaned_df, name_col, url_col, browser_col, source_col], axis=1)
    return bookmark_summary_df
