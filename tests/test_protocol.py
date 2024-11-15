import sys
import os
import pytest
from unittest.mock import MagicMock
from io import BytesIO

# Add the parent directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from protocol import ProtocolHandler, ProtocolError, Error

@pytest.fixture
def protocol_handler():
    return ProtocolHandler()

def test_handle_integer(protocol_handler):
    mock_socket_file = MagicMock()
    mock_socket_file.readline.return_value = b'123\r\n'
    assert protocol_handler.handle_integer(mock_socket_file) == 123

def test_handle_string(protocol_handler):
    mock_socket_file = MagicMock()
    mock_socket_file.readline.return_value = b'5\r\n'
    mock_socket_file.read.return_value = b'hello\r\n'
    assert protocol_handler.handle_string(mock_socket_file) == 'hello'

def test_handle_string_none(protocol_handler):
    mock_socket_file = MagicMock()
    mock_socket_file.readline.return_value = b'-1\r\n'
    assert protocol_handler.handle_string(mock_socket_file) is None

def test_handle_array(protocol_handler):
    mock_socket_file = MagicMock()
    # First send array length
    mock_socket_file.readline.side_effect = [b'2\r\n', b'5\r\n', b'5\r\n']
    mock_socket_file.read.side_effect = [b'$', b'hello\r\n', b'$', b'world\r\n']

    assert protocol_handler.handle_array(mock_socket_file) == ['hello', 'world']

# Fix for test_handle_dict
def test_handle_dict(protocol_handler):
    mock_socket_file = MagicMock()
    mock_socket_file.readline.side_effect = [
        b'2\r\n',          
        b'3\r\n',           
        b'5\r\n',           
        b'4\r\n',          
        b'6\r\n'            
    ]
    mock_socket_file.read.side_effect = [
        b'$',               
        b'key\r\n',         
        b'$',               
        b'value\r\n',       
        b'$',              
        b'key2\r\n',        
        b'$',               
        b'value2\r\n'       
    ]
    assert protocol_handler.handle_dict(mock_socket_file) == {'key': 'value', 'key2': 'value2'}

def test_write_response(protocol_handler):
    mock_socket_file = MagicMock()
    data = 'hello'
    protocol_handler.write_response(mock_socket_file, data)
    mock_socket_file.write.assert_called_once_with(b'$5\r\nhello\r\n')
    mock_socket_file.flush.assert_called_once()

def test_write(protocol_handler):
    buf = BytesIO()
    protocol_handler._write(buf, 'hello')
    assert buf.getvalue() == b'$5\r\nhello\r\n'

def test_write_bytes(protocol_handler):
    buf = BytesIO()
    protocol_handler._write(buf, b'hello')
    assert buf.getvalue() == b'$5\r\nhello\r\n'

def test_write_int(protocol_handler):
    buf = BytesIO()
    protocol_handler._write(buf, 123)
    assert buf.getvalue() == b':123\r\n'

def test_write_float(protocol_handler):
    buf = BytesIO()
    protocol_handler._write(buf, 123.45)
    assert buf.getvalue() == b'$6\r\n123.45\r\n'

def test_write_error(protocol_handler):
    buf = BytesIO()
    protocol_handler._write(buf, Error('error message'))
    assert buf.getvalue() == b'-error message\r\n'

def test_write_list(protocol_handler):
    buf = BytesIO()
    protocol_handler._write(buf, ['hello', 'world'])
    assert buf.getvalue() == b'*2\r\n$5\r\nhello\r\n$5\r\nworld\r\n'

def test_write_dict(protocol_handler):
    buf = BytesIO()
    protocol_handler._write(buf, {'key': 'value', 'key2': 'value2'})
    assert buf.getvalue() == b'%2\r\n$3\r\nkey\r\n$5\r\nvalue\r\n$4\r\nkey2\r\n$6\r\nvalue2\r\n'

def test_write_none(protocol_handler):
    buf = BytesIO()
    protocol_handler._write(buf, None)
    assert buf.getvalue() == b'$-1\r\n'