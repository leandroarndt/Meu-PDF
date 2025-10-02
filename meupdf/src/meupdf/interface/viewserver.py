import sys
from random import randint
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

class ViewServer(SimpleHTTPRequestHandler):
    port:int = 0
    host:str = 'localhost'
    _expectations:dict = {}
    content_types = ('application/pdf',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extensions_map.update({
            '.html': 'text/html',
            '.css': 'text/css',
            '.mjs': 'text/javascript',
            '.js': 'text/javascript',
            '.svg': 'image/svg+xml',
            '.pdf': 'application/pdf',
        })
        if not self.__class__.port:
            from meupdf.app import MeuPDF
            self.__class__.port = MeuPDF.port
            self.__class__.host = MeuPDF.host

    @classmethod
    def create_expectation(cls, path:str|Path, hash:int) -> int:
        key:int = randint(0, sys.maxsize)
        while key in cls._expectations:
            key = randint(0, sys.maxsize)
        cls._expectations[key] = path, hash
        return key
    
    @classmethod
    def retrieve_expectation(cls, key:int):
        """
        Returns expected values for key while poping them from the expectations.
        
        :param key: expected key
        """
        key = int(key)
        if key not in cls._expectations:
            raise KeyError(f'{key} is not expected')
        return cls._expectations.pop(key)

    def do_POST(self):
        try:
            key = int(self.headers['key'])
            path, hash = self.__class__.retrieve_expectation(key)
            try:
                if hash != int(self.headers['hash']):
                    raise ValueError(f'Hash differs from expected: {self.headers['hash']} != {hash}')
                # if path != self.headers['path']: # TODO: understand why is it different: encoding?
                #     raise ValueError(f'Path differs from expected: {self.headers['path']} != {path}')
                if self.headers['content-type'] not in self.__class__.content_types:
                    raise ValueError(f'Content type not accepted: {self.headers['content-type']} not in {self.__class__.content_types}')
                if self.headers['referer'] != f'http://{self.__class__.host}:{self.__class__.port}/web/viewer.html?file=/files/{hash}.pdf':
                    raise ValueError(f'Referer not expected: {self.headers['referer']} != http://{self.__class__.host}:{self.__class__.port}/web/viewer.html?file=/files/{hash}.pdf')
            except ValueError as e:
                self.log_error(f'POST error: handshake not accepted ({e})')
                self.send_response_only(403, 'Handshake not accepted')
                return
            with open(path, 'wb') as f:
                f.write(self.rfile.read(int(self.headers['Content-Length'])))
            self.wfile.write(bytes('Ok', 'utf-8'))
            self.send_response(200, 'Ok')
        except KeyError as e:
            self.log_error('POST error (Key not found: %s)', e)
            self.send_response_only(403, 'Key error')
        except FileNotFoundError as e:
            self.log_error('POST error (File not found: "%s")', e.strerror)
            self.send_response_only(404, 'File not found')
        except IsADirectoryError as e:
            self.log_error('POST error (Path is a directory: "%s")', e.strerror)
            self.send_response_only(418, 'Path is a directory')
        except OSError as e:
            self.log_error('POST error (unkwon OSError: "%s")', e.strerror)
            self.send_response_only(500, 'OSError')
        except Exception as e:
            self.log_error('POST error (unkown exception: "%s")', e)
            self.send_response_only(500, 'Unknown error')

def start_httpd(directory: Path, host:str='localhost', port:int=8000):
    handler = partial(ViewServer, directory=str(directory))
    httpd = HTTPServer((host, port), handler)
    httpd.serve_forever()