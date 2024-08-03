from langchain_core.pydantic_v1 import BaseModel, Field


class Bookmark(BaseModel):
    """
    A bookmark to a website
    """

    title: str = Field(description="The title of the bookmark")
    url: str = Field(description="The URL of the bookmark")


class Bookmarks(BaseModel):
    """
    A list of bookmarks
    """

    bookmarks: list[Bookmark] = Field(description="A list of bookmarks")
