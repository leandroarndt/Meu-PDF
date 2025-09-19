"""
Free Open Source PDF viewer and editor
"""
import threading, sys, socket, zipfile
from pathlib import Path

import toga, asyncio
from toga.style.pack import Pack

from meupdf.interface.viewserver import start_httpd
from meupdf.interface.tab import DocumentTab
from meupdf.interface.merge import MergeWindow
from meupdf.interface.commands import create_commands

# toga.Widget.DEBUG_LAYOUT_ENABLED = True

class MeuPDF(toga.App):
    main_box:toga.Box
    tab_area:toga.OptionContainer
    server_dir:Path
    files_uri:Path = Path('files')
    host:str = 'localhost'
    port:int = 8000
    server_thread:threading.Thread
    binded_to_port:bool = False

    def find_port(self, bottom=60000, top=61000):
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
        start_httpd(self.server_dir, self.host, self.port)

    def startup(self):
        # Prepare for non-console running
        try:
            sys.stderr.write('Welcome to Meu PDF!')
        except AttributeError:
            import os
            sink = open(os.devnull, 'w')
            sys.stderr = sink
            sys.stdout = sink

        # Start view server
        self.server_dir = self.paths.cache / 'viewserver'
        print(f'Server dir at {self.server_dir}')
        (self.server_dir / self.files_uri).mkdir(parents=True, exist_ok=True)
        # shutil.copytree(self.paths.app / 'resources/viewserver', self.server_dir, dirs_exist_ok=True)
        server_files = zipfile.ZipFile(self.paths.app / 'resources/viewserver/pdfjs-5.4.149-dist.zip')
        server_files.extractall(self.server_dir)
        try:
            self.port = self.find_port()
            self.binded_to_port = True
        except OSError:
            self.binded_to_port = False
        self.server_thread = threading.Thread(target=self.start_server)
        self.server_thread.start()

        # Prepare interface contents
        self.main_box = toga.Box()
        self.tab_area = toga.OptionContainer(style=Pack(flex=1), content=[
            toga.OptionItem(text=_('Welcome'), content=toga.Label(_('Welcome to Meu PDF'))),
        ], on_select=self.on_select_tab)

        self.main_box.add(self.tab_area)

        self.main_window = toga.MainWindow(title=self.formal_name)

        # Toolbar and menus
        self.commands.clear()
        self.main_window.toolbar.clear()
        # create_menus(self, self.commands)
        # create_toolbar(self, self.main_window.toolbar)
        create_commands(self, self.commands, self.main_window.toolbar)

        # Add main box
        self.main_window.content = self.main_box
        self.main_window.show()

    def open_dialog(self, widget, **kwargs):
        dialog = toga.OpenFileDialog(_('Open PDF file'), file_types=['PDF'])
        
        task = asyncio.create_task(self.main_window.dialog(dialog))
        task.add_done_callback(self.open_dialog_closed)

    def open_dialog_closed(self, task):
        file = task.result()
        if file:
            new_tab = DocumentTab(file, self.server_dir, self.files_uri, self.host, self.port)
            self.tab_area.content.append(new_tab)
            self.tab_area.current_tab = new_tab
        if not self.binded_to_port:
            dialog = toga.ErrorDialog(_('Network error!'), _('It was not possible to bind to a network port. Document contents will not be displayed.'))
            task = asyncio.create_task(self.main_window.dialog(dialog))
    
    def open_merge_window(self, widget, **kwargs):
        merge_window = MergeWindow()
        merge_window.show()
        merge_window.open_dialog(widget, first_selection=True)
    
    def on_select_tab(self, widget, **kwargs):
        if self.tab_area.content.index(self.tab_area.current_tab) == 0:
            self.commands['close_tab'].enabled = False
        else:
            self.commands['close_tab'].enabled = True

    def close_tab(self, widget, **kwargs):
        if self.tab_area.current_tab.index == 0: # Do not close welcome page
            return
        try:
            tab = self.tab_area.current_tab
            i = self.tab_area.content.index(tab)
            if i == len(self.tab_area.content) - 1:
                self.tab_area.current_tab = i - 1
            else:
                self.tab_area.current_tab = i + 1
            self.tab_area.content.remove(tab)
        except Exception as e:
            print(e)

    def on_exit(self, **kwargs):
        # Delete server cache
        files = (self.server_dir / self.files_uri).glob('**', recurse_symlinks=False)
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
    
    def request_exit(self, *args, **kwargs):
        super().request_exit()

def main():
    return MeuPDF()
