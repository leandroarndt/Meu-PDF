from enum import StrEnum
from pathlib import Path

class DocumentFormats(StrEnum):
    PDF = 'PDF'

class FormatInfos(StrEnum):
    FULL_NAME = 'full name'
    SHORT_NAME = 'short name'
    # CAPABILITIES = 'capabilities' # Not used right now

document_formats = {
    DocumentFormats.PDF: {
        FormatInfos.FULL_NAME: _('Portable Document File'),
        FormatInfos.SHORT_NAME: _('PDF document'),
    },
}

class GenericDocument(object):
    format:DocumentFormats
    format_info:dict
    file_path:Path
    pages:list
    page_count:int

    def __init__(self, format):
        self.format = format
        self.format_info = document_formats[format]
    
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
        return NotImplementedError(f'Conversion to image not implemented for pages of {self._document.format} documents.')

