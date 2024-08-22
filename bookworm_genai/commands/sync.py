import os
import sys
import glob
import logging
import shutil

import tiktoken
from langchain_core.documents import Document

from bookworm_genai.integrations import Browser
from bookworm_genai.storage import store_documents, _get_embedding_store


logger = logging.getLogger(__name__)


def sync(browsers: dict, estimate_cost: bool = False):
    docs: list[Document] = []

    for browser, config in browsers.items():
        try:
            platform_config = config[sys.platform]
        except KeyError:
            logger.warning(f"Platform {sys.platform} not supported for browser {browser.value}")
            continue
        else:
            if "copy" in platform_config:
                _copy(platform_config["copy"])

            _log_bookmark_source(browser, platform_config)

            config = platform_config["bookmark_loader_kwargs"]
            if "db" in config:
                if callable(config["db"]):
                    config["db"] = config["db"](None)

            loader = platform_config["bookmark_loader"](**config)

            docs.extend(loader.lazy_load())

    logger.debug(f"{len(docs)} Bookmarks loaded")

    if estimate_cost:
        return _estimate_cost(docs)

    if docs:
        store_documents(docs)


def _copy(config: dict):
    logger.debug(f"Copying {config['from']} to {config['to']}")

    source = glob.glob(config["from"])
    source = source[0]

    directory = os.path.dirname(config["to"])
    os.makedirs(directory, exist_ok=True)

    shutil.copy(source, config["to"])


def _log_bookmark_source(browser: Browser, platform_config: dict):
    logger.info("Loading bookmarks from %s", browser.value.title())

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


def _estimate_cost(docs: list[Document]) -> float:
    embedding = _get_embedding_store()

    # using _get_embedding_store here means that it's more likely that the model we are using
    # in the actual embedding is the one we use for cost estimation
    # however note that .model here is not part of the contract for Embeddings
    # so this is a bit of a hack
    # if we add more embeddings options in the future, we need to re-evaluate this.
    encoding = tiktoken.encoding_for_model(embedding.model)

    logger.info(f"Estimating cost for {embedding.model}")

    tokens: int = 0
    for doc in docs:
        tokens += len(encoding.encode(doc.page_content))

    price = float(input(f"what is the current cost for {embedding.model} per million? (non-batch) "))

    # price is often advertise per million; so find the price per token
    price_per_token = price / 1_000_000

    # given the number total tokens we have, apply the price per token
    cost = tokens * price_per_token

    logger.info(f"Estimated cost: ${cost} (tokens: {tokens}) ")

    return cost
