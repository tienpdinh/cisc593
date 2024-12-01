from collections import namedtuple
from io import BytesIO
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

Error = namedtuple('Error', ('message',))

class ProtocolError(Exception):
    """Raised when protocol parsing fails."""
    pass

class Disconnect(Exception):
    """Raised when a client disconnects."""
    pass

class ProtocolHandler:
    """Handles RESP protocol encoding/decoding with support for nested data structures."""
    
    def __init__(self):
        self.handlers = {
            b'+': self.handle_simple_string,
            b'-': self.handle_error,
            b':': self.handle_integer,
            b'$': self.handle_string,
            b'*': self.handle_array,
            b'%': self.handle_dict
        }

    def handle_request(self, socket_file) -> Any:
        """Read and parse a request from the socket file."""
        first_byte = socket_file.read(1)
        if not first_byte:
            raise Disconnect()

        try:
            handler = self.handlers[first_byte]
        except KeyError:
            raise ProtocolError(f'Invalid first byte: {first_byte!r}')

        return handler(socket_file)

    def handle_simple_string(self, socket_file) -> str:
        return socket_file.readline().rstrip(b'\r\n').decode('utf-8')

    def handle_error(self, socket_file) -> Error:
        return Error(socket_file.readline().rstrip(b'\r\n').decode('utf-8'))

    def handle_integer(self, socket_file) -> int:
        return int(socket_file.readline().rstrip(b'\r\n'))

    def handle_string(self, socket_file) -> Any:
        length = int(socket_file.readline().rstrip(b'\r\n'))
        if length == -1:
            return None
        data = socket_file.read(length + 2)  # Include \r\n
        if len(data) != length + 2:
            raise ProtocolError('Failed to read complete string')
        
        value = data[:-2]
        try:
            return value.decode('utf-8')
        except UnicodeDecodeError:
            return value

    def handle_array(self, socket_file) -> List:
        num_elements = int(socket_file.readline().rstrip(b'\r\n'))
        if num_elements == -1:
            return None
        result = []
        for _ in range(num_elements):
            element = self.handle_request(socket_file)
            if isinstance(element, bytes):
                try:
                    element = element.decode('utf-8')
                except UnicodeDecodeError:
                    pass
            result.append(element)
        return result

    def handle_dict(self, socket_file) -> Dict:
        num_items = int(socket_file.readline().rstrip(b'\r\n'))
        if num_items == -1:
            return None
        elements = [self.handle_request(socket_file) for _ in range(num_items * 2)]
        return dict(zip(elements[::2], elements[1::2]))

    def write_response(self, socket_file, data: Any) -> None:
        buf = BytesIO()
        self._write(buf, data)
        buf.seek(0)
        socket_file.write(buf.getvalue())
        socket_file.flush()

    def _write(self, buf: BytesIO, data: Any) -> None:
        if isinstance(data, str):
            data = data.encode('utf-8')
            buf.write(b'$%d\r\n' % len(data))
            buf.write(data)
            buf.write(b'\r\n')
        elif isinstance(data, bytes):
            buf.write(b'$%d\r\n' % len(data))
            buf.write(data)
            buf.write(b'\r\n')
        elif isinstance(data, int):
            buf.write(b':%d\r\n' % data)
        elif isinstance(data, float):
            str_data = str(data).encode('utf-8')
            buf.write(b'$%d\r\n' % len(str_data))
            buf.write(str_data)
            buf.write(b'\r\n')
        elif isinstance(data, Error):
            buf.write(b'-%s\r\n' % data.message.encode('utf-8'))
        elif isinstance(data, (list, tuple)):
            if data is None:
                buf.write(b'*-1\r\n')
            else:
                buf.write(b'*%d\r\n' % len(data))
                for item in data:
                    self._write(buf, item)
        elif isinstance(data, dict):
            if data is None:
                buf.write(b'%-1\r\n')
            else:
                buf.write(b'%%%d\r\n' % len(data))
                for key, value in data.items():
                    self._write(buf, str(key))
                    self._write(buf, value)
        elif data is None:
            buf.write(b'$-1\r\n')
        else:
            str_data = str(data).encode('utf-8')
            buf.write(b'$%d\r\n' % len(str_data))
            buf.write(str_data)
            buf.write(b'\r\n')