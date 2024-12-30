import enum
from langchain_core.documents import Document

from bookworm_genai import __version__
from bookworm_genai.integrations import Browser

class Metadata(str, enum.Enum):
    Browser = 'browser'
    BookwormVersion = 'bookworm_version'


def attach_metadata(doc: Document, browser: Browser) -> Document:
    doc.metadata[Metadata.Browser.value] = browser.value
    doc.metadata[Metadata.BookwormVersion.value] = __version__
    return doc