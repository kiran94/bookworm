import os
import sys
import logging

from langchain_community.document_loaders import JSONLoader

from bookworm_genai.integrations import browsers
from bookworm_genai.storage import store_documents

logger = logging.getLogger(__name__)


def sync():
    docs = []

    for browser, config in browsers.items():
        try:
            platform_config = config[sys.platform]
        except KeyError:
            logger.warning(f"Platform {sys.platform} not supported for browser {browser}")
            continue
        else:
            expanded_path = os.path.expanduser(platform_config["bookmark_file_path"])

            jq_command = """
              [.roots.bookmark_bar.children, .roots.other.children] |
              flatten |
              .. |
              objects |
              select(.type == "url")
            """

            logger.info("Loading bookmarks from %s", expanded_path)
            bookmark_bar = JSONLoader(expanded_path, jq_command, text_content=False)
            docs.extend(bookmark_bar.lazy_load())

    logger.debug(f"{len(docs)} Bookmarks loaded")

    store_documents(docs)
