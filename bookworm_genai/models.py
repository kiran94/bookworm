import sys
import subprocess
import logging

from langchain_core.pydantic_v1 import BaseModel, Field

logger = logging.getLogger(__name__)


class Bookmark(BaseModel):
    """
    A bookmark to a website
    """

    title: str = Field(description="The title of the bookmark")
    url: str = Field(description="The URL of the bookmark")
    source: str = Field(description="The source of the bookmark")
    browser: str = Field(description="The browser that the bookmark was saved from")

    def open(self):
        if sys.platform == "win32":
            subprocess.Popen(["start", self.url], shell=True)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", self.url])
        elif sys.platform == "linux":
            subprocess.Popen(["xdg-open", self.url])
        else:
            logger.warning(f'Platform "{sys.platform}" not supported. Printing URL instead')
            logger.info(self.url)


class Bookmarks(BaseModel):
    """
    A list of bookmarks
    """

    bookmarks: list[Bookmark] = Field(description="A list of bookmarks")
