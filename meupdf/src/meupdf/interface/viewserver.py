from functools import partial
from http.server import HTTPServer, ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path


class ViewServer(SimpleHTTPRequestHandler):
    extensions_map = {
        '.html': 'text/html',
        '.css': 'text/css',
        '.mjs': 'text/javascript',
        '.js': 'text/javascript',
        '.svg': 'image/svg+xml',
        '.pdf': 'application/pdf',
    }

def start_httpd(directory: Path, host:str='localhost', port:int=8000):
    handler = partial(ViewServer, directory=str(directory))
    # handler = SimpleHTTPRequestHandler(directory=directory)
    # handler.extensions_map = {
    #     '': 'text/plain',
    #     '*.mjs': 'text/javascript',
    # }
    # # httpd = HTTPServer(('localhost', port), handler)
    httpd = ThreadingHTTPServer((host, port), handler)
    httpd.serve_forever()