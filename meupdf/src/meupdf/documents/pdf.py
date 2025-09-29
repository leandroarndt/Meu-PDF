import sys
from pathlib import Path

try:
    import pymupdf
except ImportError:
    import pypdf

from meupdf.documents.generic import GenericPage, GenericDocument, DocumentFormats, FormatInfos, document_formats

DOCUMENT_FORMAT = 'PDF'

class PDFPage(GenericPage):
    def __init__(self, document, number):
        super().__init__(document, number)
        if 'pymupdf' in sys.modules:
            self._page = document._document[number] # pyright: ignore[reportAttributeAccessIssue]
            self.width = self._page.rect[2] - self._page.rect[0], # pyright: ignore[reportAttributeAccessIssue]
            self.height = self._page.rect[3] - self._page.rect[1], # pyright: ignore[reportAttributeAccessIssue]
        else:
            self._page = document._document.get_page(number) # pyright: ignore[reportAttributeAccessIssue]
            self.width, self.height = self._page.trimbox.width, self._page.trimbox.right
    
    def to_image(self, width:int|None=None, height:int|None=None, zoom:float=1.0, rotation:int=0): # pyright: ignore[reportIncompatibleMethodOverride]
        """Returns page image according to the given parameters in the following dimension
        priority order:
        width > height > zoom
        Rotation must be given in degrees (rotation > 0 rotates right)
        """
        if 'pymupdf' in sys.modules:
            if width:
                zoom = width / (self._page.rect[2] - self._page.rect[0])
            elif height:
                zoom = height / (self._page.rect[3] - self._page.rect[1])
            matrix = pymupdf.Matrix(zoom, zoom).prerotate(rotation) # pyright: ignore[reportPossiblyUnboundVariable]
            return self._page.get_pixmap(matrix=matrix)
        else:
            raise NotImplementedError('PDF page images not implemented without pymupdf yet')

class PDFDocument(GenericDocument):
    pages:list[PDFPage]
    format:str = DOCUMENT_FORMAT # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(self, file_path):
        super().__init__(format=PDFDocument.format)
        self.file_path = Path(file_path
                              )
        if 'pymupdf' in sys.modules:
            self._document = pymupdf.open(file_path) # pyright: ignore[reportPossiblyUnboundVariable]
            self.page_count = self._document.page_count
            self.pages = []
            for p in range(self.page_count):
                self.pages.append(PDFPage(self, p))
        else:
            self._document = pypdf.PdfReader(file_path) # pyright: ignore[reportPossiblyUnboundVariable]
            self.page_count = self._document.get_num_pages()
            self.pages = []
            for p in range(self.page_count):
                self.pages.append(PDFPage(self, p))

    def merge(self, other):
        if 'pymupdf' in sys.modules:
            toc = self._document.get_toc(False) # type: ignore
            toc2 = other._document.get_toc(False)
            self._document.insert_pdf(other._document) # type: ignore
            for t in toc2:
                t[2] += self.page_count
            self.page_count += len(other._document)
            toc = toc + toc2
            self._document.set_toc(toc) # type: ignore
        else:
            raise NotImplementedError('PDF merge not implemented without pymupdf yet')

    def extract_pages(self, new_path:str|None=None, first:int=0, last:int|None=None):
        if 'pymupdf' in sys.modules:
            new_doc = pymupdf.Document() # type: ignore
            new_doc.insert_pdf(self._document, from_page=first, to_page=last or first)
            if new_path is not None:
                new_doc.save(Path(new_path))
        else:
            raise NotImplementedError('Page extraction without pymupdf not implemented yet')

    def save(self, new_path:Path|str|None=None):
        if new_path:
            self.file_path = Path(new_path)
        if 'pymupdf' in sys.modules:
            self._document.save(self.file_path) # type: ignore

document_formats[DOCUMENT_FORMAT] = {
        FormatInfos.FULL_NAME: _('Portable Document File'),
        FormatInfos.SHORT_NAME: _('PDF document'),
        FormatInfos.EXTENSIONS: ['.pdf'],
        FormatInfos.CLASS: PDFDocument,
    }
