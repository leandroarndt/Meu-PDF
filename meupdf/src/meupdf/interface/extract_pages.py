import toga

from meupdf.documents.pdf import PDFDocument

class PageRange(toga.Box):
    document:PDFDocument
    first_miniature:toga.ImageView
    first_page:toga.TextInput
    to_label:toga.Label
    last_page:toga.TextInput
    last_miniature:toga.ImageView
    delete_button:toga.Button

    def __init__(self, document, first_page:int=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

class ExtractPagesWindow(toga.Window):
    document:PDFDocument

    def __init__(self, document, first_page=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
    