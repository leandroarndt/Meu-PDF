import shutil, asyncio
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
        ready_script = '''
            var injectedCSS = "#downloadButton {display: none;}";
            var css = document.createElement("style");
            css.textContent = injectedCSS;
            document.body.append(css);
        '''
        self.view = toga.WebView(style=pack.Pack(flex=1))
        self.view.on_webview_load = lambda widget, **kwargs: widget.evaluate_javascript(ready_script)
        super().__init__(text=Path(file_path).name, content=self.view, *args, **kwargs)
        self.server_dir, self.files_uri, self.host, self.port = server_dir, files_uri, host, port
        self.file_path = file_path
        self.document = PDFDocument(self.file_path)
        shutil.copyfile(file_path, server_dir / files_uri / self.document.hashed_path('.pdf'))
        # self.view.url = f'http://{host}:{port}/web/viewer.html?file=/{files_uri}/{self.document.hashed_path('.pdf')}'
        task = asyncio.create_task(self.view.load_url(f'http://{host}:{port}/web/viewer.html?file=/{files_uri}/{self.document.hashed_path('.pdf')}'))
        task.add_done_callback(lambda task: self.view.evaluate_javascript(ready_script))
