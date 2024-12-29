import enum
from langchain_core.documents import Document

from bookworm_genai.integrations import Browser

class Metadata(str, enum.Enum):
    Browser = 'browser'


def attach_metadata(doc: Document, browser: Browser) -> Document:
    doc.metadata[Metadata.Browser.value] = browser.value
    return doc