from enum import StrEnum
from pathlib import Path

# class DocumentFormats(StrEnum):
#     PDF = 'PDF'

class FormatInfos(StrEnum):
    FULL_NAME = 'full name'
    SHORT_NAME = 'short name'
    # CAPABILITIES = 'capabilities' # Not used right now

class DocumentFormats(object):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = {}
        return cls._instance

document_formats = DocumentFormats()

class GenericDocument(object):
    format:DocumentFormats
    format_info:dict
    file_path:Path
    pages:list
    page_count:int

    def __init__(self, format):
        self.format = format
        self.format_info = document_formats[format]

    def close(self):
        pass # Fail silently, since it must be closed anyway when the object is destroyed

    def merge(self, other):
        raise NotImplementedError(f'Merging not implemented for {self.format} documents.')

class GenericPage(object):
    _document:GenericDocument
    _page = None
    number:int = 0
    width:float
    height:float

    def __init__(self, document:GenericDocument, number:int=0):
        self._document, self.number = document, number

    def to_image(self, zoom:int=1, rotation:int=0):
        raise NotImplementedError(f'Conversion to image not implemented for pages of {self._document.format} documents.')

