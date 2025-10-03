"""
Free Open Source PDF viewer and editor
"""
import threading, sys, socket, zipfile, os
from pathlib import Path

import toga

from meupdf.interface.viewserver import start_httpd
from meupdf.interface.main_content import MainWindow

# toga.Widget.DEBUG_LAYOUT_ENABLED = True

class MeuPDF(toga.App):
    main_window:MainWindow
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
                    self.__class__.port = port
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
        server_files = zipfile.ZipFile(self.paths.app / 'resources/viewserver/pdfjs-5.4.149-dist.zip')
        server_files.extractall(self.server_dir)
        try:
            self.port = self.find_port()
            self.binded_to_port = True
        except OSError:
            self.binded_to_port = False
        self.server_thread = threading.Thread(target=self.start_server)
        self.server_thread.start()

        # Interface contents
        self.main_window = MainWindow(self, title=self.formal_name) # pyright: ignore[reportIncompatibleMethodOverride]
        self.main_window.show()

    def on_running(self, **kwargs):
        class FakeResult(object):
            def __init__(self, arg):
                self.arg = arg
            def result(self):
                return arg
        for arg in sys.argv[1:]:
            path = (Path(os.getcwd()) / arg).resolve()
            if path.exists():
                self.main_window.open_dialog_closed(FakeResult(str(path)))
            else:
                print(f'Could not open "{path}": file does not exist.')
                print(f'Current working directory: {os.getcwd()}')
                print(f'Given file path: {arg}')

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
