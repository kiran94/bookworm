import os
import sys
import glob
import logging
import shutil

from bookworm_genai.storage import store_documents


logger = logging.getLogger(__name__)


def sync(browsers: dict):
    docs = []

    for browser, config in browsers.items():
        try:
            platform_config = config[sys.platform]
        except KeyError:
            logger.warning(f"Platform {sys.platform} not supported for browser {browser.value}")
            continue
        else:
            if "copy" in platform_config:
                _copy(platform_config["copy"])

            _log_bookmark_source(platform_config)

            config = platform_config["bookmark_loader_kwargs"]
            if "db" in config:
                if callable(config["db"]):
                    config["db"] = config["db"](None)

            loader = platform_config["bookmark_loader"](**config)

            docs.extend(loader.lazy_load())

    logger.debug(f"{len(docs)} Bookmarks loaded")

    if docs:
        store_documents(docs)


def _copy(config: dict):
    logger.debug(f"Copying {config['from']} to {config['to']}")

    directory = os.path.dirname(config["to"])

    source = glob.glob(config["from"])
    source = source[0]

    os.makedirs(directory, exist_ok=True)

    shutil.copy(source, config["to"])


def _log_bookmark_source(platform_config: dict):
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

    logger.info("Loading bookmarks from %s", path)
