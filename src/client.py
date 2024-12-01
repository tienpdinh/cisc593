from gevent import socket
from socket import error as socket_error
from typing import Any

from protocol import ProtocolHandler, Error
from storage import CommandError

class Client:
    """Client implementation with proper resource management."""
    
    def __init__(self, host='127.0.0.1', port=31337, timeout=30):
        self._protocol = ProtocolHandler()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(timeout)
        self._socket.connect((host, port))
        self._fh = self._socket.makefile('rwb')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        try:
            self._fh.close()
        except:
            pass
        try:
            self._socket.close()
        except:
            pass

    def execute(self, *args) -> Any:
        try:
            self._protocol.write_response(self._fh, args)
            resp = self._protocol.handle_request(self._fh)
            if isinstance(resp, Error):
                raise CommandError(resp.message)
            return resp
        except socket_error as e:
            raise CommandError(f'Connection error: {e}')

    def get(self, key):
        return self.execute('GET', key)

    def set(self, key, value):
        return self.execute('SET', key, value)

    def delete(self, key):
        return self.execute('DELETE', key)

    def flush(self):
        return self.execute('FLUSH')

    def mget(self, *keys):
        return self.execute('MGET', *keys)

    def mset(self, *items):
        if len(items) % 2 != 0:
            raise CommandError('MSET requires pairs of key/value arguments')
        return self.execute('MSET', *items)