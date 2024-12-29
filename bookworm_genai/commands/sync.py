import os
import sys
import glob
import logging
import shutil
from typing import Optional, Union

import tiktoken
from langchain_core.documents import Document

from bookworm_genai.integrations import Browser, browsers, BrowserManifest
from bookworm_genai.storage import store_documents, _get_embedding_store
from bookworm_genai.metadata import attach_metadata


logger = logging.getLogger(__name__)


def sync(browsers: BrowserManifest = browsers, estimate_cost: bool = False, browser_filter: list[str] = []) -> Union[None, float]:
    docs: list[Document] = []

    for browser, config in browsers.items():
        browser: Browser = browser

        if browser_filter and (browser.value not in browser_filter):
            logger.debug(f'browser {browser.value} skipped due to filter')
            continue

        try:
            platform_config = config[sys.platform]
        except KeyError:
            logger.warning(f'🔄 browser {browser.value} is not supported on {sys.platform} yet')
            continue
        else:
            if "copy" in platform_config:
                try:
                    _copy(platform_config["copy"])
                except BrowserBookmarkFileNotFound as e:
                    logger.warning(f"🔄 browser {browser.value} skipped due to missing file '{e.file}'")
                    continue

            _log_bookmark_source(browser, platform_config)

            config = platform_config["bookmark_loader_kwargs"]
            if "db" in config:
                if callable(config["db"]):
                    config["db"] = config["db"](None)

            loader = platform_config["bookmark_loader"](**config)

            current_docs: list[Document] = list(loader.lazy_load())

            for index, doc in enumerate(current_docs):
                current_docs[index] = attach_metadata(current_docs[index], browser)

            docs.extend(current_docs)

    logger.debug(f"{len(docs)} Bookmarks loaded")

    if estimate_cost:
        return _estimate_cost(docs)

    if docs:
        store_documents(docs)


def _copy(config: dict):
    logger.debug(f"Copying {config['from']} to {config['to']}")

    source = glob.glob(config["from"])

    try:
        source = source[0]
    except IndexError as e:
        logger.debug(f"source {config['from']} not found")
        raise BrowserBookmarkFileNotFound(config["from"]) from e

    directory = os.path.dirname(config["to"])
    os.makedirs(directory, exist_ok=True)

    shutil.copy(source, config["to"])


def _log_bookmark_source(browser: Browser, platform_config: dict):
    logger.info(f'✅ browser {browser.value} bookmarks loaded!')

    path = ""

    try:
        path = platform_config["bookmark_loader_kwargs"]["file_path"]
    except KeyError:
        pass

    try:
        path = platform_config["bookmark_loader_kwargs"]["db"]
        if callable(path):
            path = path(path)

        path = path._engine.url

    except KeyError:
        pass

    logger.debug("Loading bookmarks from %s", path)


def _estimate_cost(docs: list[Document], cost_per_million: Optional[float] = None) -> float:
    embedding = _get_embedding_store()

    # NOTE: using _get_embedding_store here means that it's more likely that the model we are using
    # in the actual embedding is the one we use for cost estimation
    # however note that .model here is not part of the contract for Embeddings
    # so this is a bit of a hack
    # if we add more embeddings options in the future, we need to re-evaluate this.
    encoding = tiktoken.encoding_for_model(embedding.model)

    logger.info(f"Estimating cost for {embedding.model}")

    tokens: int = 0
    for doc in docs:
        tokens += len(encoding.encode(doc.page_content))

    if not cost_per_million:
        # https://openai.com/api/pricing/
        price = float(input(f"what is the current cost for {embedding.model} per million? (non-batch) "))
    else:
        price = cost_per_million

    # price is often advertise per million; so find the price per token
    price_per_token = price / 1_000_000

    # given the number total tokens we have, apply the price per token
    cost = tokens * price_per_token

    logger.info(f"Estimated cost: ${cost} (tokens: {tokens}) ")

    return cost


class BrowserBookmarkFileNotFound(Exception):
    '''
    Represents that a bookmark file on the local file system could not be found.
    For example if a configuration is defined with a glob expression /my/path/*.sqlite but that path resolves to nothing.
    '''
    def __init__(self, file: str):
        self.file = file
        super().__init__(f"Could not resolve file: {file}")