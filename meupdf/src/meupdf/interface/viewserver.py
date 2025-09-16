from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
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
    httpd = HTTPServer((host, port), handler)
    httpd.serve_forever()