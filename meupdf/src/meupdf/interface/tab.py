import shutil
from pathlib import Path

import toga
from toga.style import pack

from meupdf.documents.pdf import PDFDocument

class DocumentTab(toga.OptionItem):
    file_path:Path
    document:PDFDocument
    view:toga.WebView
    server_dir:Path
    files_uri:Path
    host:str
    port:int

    def __init__(self, file_path, server_dir, files_uri, host, port, *args, **kwargs):
        self.view = toga.WebView(style=pack.Pack(flex=1))
        super().__init__(text=Path(file_path).name, content=self.view, *args, **kwargs)
        self.server_dir, self.files_uri, self.host, self.port = server_dir, files_uri, host, port
        self.file_path = file_path
        self.document = PDFDocument(self.file_path)
        shutil.copyfile(file_path, server_dir / files_uri / self.file_path.name )
        self.view.url = f'http://{host}:{port}/{files_uri}/{self.file_path.name}'
