from gevent.pool import Pool
from gevent.server import StreamServer
from socket import error as socket_error
import logging
from typing import Dict

from protocol import ProtocolHandler, Error, Disconnect, ProtocolError
from storage import KeyValueStore, CommandError

logger = logging.getLogger(__name__)

class Server:
    """Key-value store server implementation."""

    def __init__(self, host='127.0.0.1', port=31337, max_clients=64, max_memory_mb=100):
        self._pool = Pool(max_clients)
        self._server = StreamServer(
            (host, port),
            self.connection_handler,
            spawn=self._pool)
        self._protocol = ProtocolHandler()
        self._kv = KeyValueStore(max_memory_mb)
        self._commands = self.get_commands()

    def get_commands(self) -> Dict:
        return {
            'GET': self.get,
            'SET': self.set,
            'DELETE': self.delete,
            'FLUSH': self.flush,
            'MGET': self.mget,
            'MSET': self.mset
        }

    def connection_handler(self, conn, address):
        logger.info('Connection received: %s:%s', *address)
        try:
            conn.settimeout(60)
            socket_file = conn.makefile('rwb')
            try:
                while True:
                    try:
                        data = self._protocol.handle_request(socket_file)
                    except Disconnect:
                        logger.info('Client disconnected: %s:%s', *address)
                        break
                    except ProtocolError as e:
                        logger.error('Protocol error: %s', e)
                        self._protocol.write_response(socket_file, Error(str(e)))
                        continue

                    try:
                        resp = self.get_response(data)
                    except CommandError as exc:
                        logger.exception('Command error')
                        resp = Error(str(exc))
                    except Exception as exc:
                        logger.exception('Unexpected error')
                        resp = Error('Internal server error')

                    try:
                        self._protocol.write_response(socket_file, resp)
                    except socket_error:
                        logger.error('Failed to write response')
                        break
            finally:
                socket_file.close()
        except socket_error as e:
            logger.error('Socket error with client %s:%s: %s', *(address + (e,)))
        finally:
            conn.close()

    def run(self):
        logger.info('Starting server on %s:%s', *self._server.address)
        self._server.serve_forever()

    def get_response(self, data):
        if not isinstance(data, (list, tuple)):
            try:
                data = data.split()
            except AttributeError:
                raise CommandError('Request must be list or simple string')

        if not data:
            raise CommandError('Missing command')

        command = data[0].upper() if isinstance(data[0], str) else data[0].decode('utf-8').upper()
        if command not in self._commands:
            raise CommandError(f'Unrecognized command: {command}')

        logger.debug('Received %s', command)
        return self._commands[command](*data[1:])

    def get(self, key):
        return self._kv.get(key)

    def set(self, key, value):
        return 1 if self._kv.set(key, value) else 0

    def delete(self, key):
        return 1 if self._kv.delete(key) else 0

    def flush(self):
        return self._kv.flush()

    def mget(self, *keys):
        return [self._kv.get(key) for key in keys]

    def mset(self, *items):
        if len(items) % 2 != 0:
            raise CommandError('MSET requires pairs of key/value arguments')
        count = 0
        for key, value in zip(items[::2], items[1::2]):
            if self._kv.set(key, value):
                count += 1
        return count