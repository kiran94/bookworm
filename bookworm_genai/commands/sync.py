import sys
import logging


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
            path = platform_config["bookmark_loader_kwargs"]["file_path"]
            logger.info("Loading bookmarks from %s", path)

            loader = platform_config["bookmark_loader"](**platform_config["bookmark_loader_kwargs"])

            docs.extend(loader.lazy_load())

    logger.debug(f"{len(docs)} Bookmarks loaded")

    if docs:
        store_documents(docs)
