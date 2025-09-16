"""
Free Open Source PDF viewer and editor
"""
import threading, shutil, os, socket
from pathlib import Path

import toga, asyncio, sys
from toga.style.pack import COLUMN, ROW, Pack

from meupdf.interface.viewserver import start_httpd
from meupdf.interface.tab import DocumentTab
from meupdf.interface.merge import MergeWindow

# toga.Widget.DEBUG_LAYOUT_ENABLED = True

class MeuPDF(toga.App):
    main_box:toga.Box
    tab_area:toga.OptionContainer
    server_dir:Path
    files_uri:Path = Path('files')
    host:str = 'localhost'
    port:int = 8000
    # server:ViewServer
    server_thread:threading.Thread

    def find_port(self, bottom=8000, top=9000):
        for port in range(bottom, top):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((self.host, port))
                    self.port = port
                    print(f'Binded to port {port}')
                    return port
            except OSError:
                pass
        raise OSError(f'No available port from {bottom} to {top-1}')
    
    def start_server(self):
        # self.server = ViewServer(self.server_dir, self.host, self.port)
        # self.server.serve()
        start_httpd(self.server_dir, self.host, self.port)

    def startup(self):
        # Start view server
        self.server_dir = self.paths.cache / 'viewserver'
        print(f'Server dir at {self.server_dir}')
        (self.server_dir / self.files_uri).mkdir(parents=True, exist_ok=True)
        shutil.copytree(self.paths.app / 'resources/viewserver', self.server_dir, dirs_exist_ok=True)
        self.port = self.find_port()
        self.server_thread = threading.Thread(target=self.start_server)
        self.server_thread.start()

        # toga.Button('Open', on_press=self.open_dialog)# tab_area.content.append(DocumentTab(toga.OpenFileDialog('Open PDF file', file_types='*.pdf'))))

        self.main_box = toga.Box()
        self.tab_area = toga.OptionContainer(style=Pack(flex=1), content=[
            toga.OptionItem(text=_('Welcome'), content=toga.Label(_('Welcome to Meu PDF'))),
        ])

        self.main_box.add(self.tab_area)

        self.main_window = toga.MainWindow(title=self.formal_name)

        self.main_window.toolbar.clear()
        self.main_window.toolbar.add(
            toga.Command(
                self.open_dialog,
                text=_('Open'),
                icon='resources/icons/open.png',
                shortcut=toga.Key.MOD_1 + 'O',
                tooltip=_('Open a PDF file'),
                order=0,
                group=toga.Group.FILE
            ),
            toga.Command(
                self.open_merge_window,
                text=_('Merge'),
                shortcut=toga.Key.MOD_1 + 'M',
                icon='resources/icons/merge.png',
                tooltip=_('Merge two or more PDF documents'),
                order=1,
                group=toga.Group.FILE
            ),
        )

        self.main_window.content = self.main_box
        self.main_window.show()

    def open_dialog(self, widget):
        dialog = toga.OpenFileDialog(_('Open PDF file'), file_types=['PDF'])
        
        task = asyncio.create_task(self.main_window.dialog(dialog))
        task.add_done_callback(self.open_dialog_closed)

    def open_dialog_closed(self, task):
        file = task.result()
        if file:
            new_tab = DocumentTab(file, self.server_dir, self.files_uri, self.host, self.port)
            self.tab_area.content.append(new_tab)
            self.tab_area.current_tab = new_tab
    
    def open_merge_window(self, widget):
        merge_window = MergeWindow()
        merge_window.show()
        merge_window.open_dialog(widget, first_selection=True)
    
    def on_close(self, window, **kwargs):
        # Delete server cache
        files = self.server_dir.glob('**', recurse_symlinks=False)
        for f in files:
            try:
                if f.is_file():
                    f.unlink()
                    print(f'Deleted file {f}')
                if f.is_dir():
                    f.rmdir()
                    print(f'Removed folder {f}')
            except:
                pass
        return True

def main():
    return MeuPDF()
