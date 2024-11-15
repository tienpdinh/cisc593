import sys
import os
import pytest
from unittest.mock import patch, MagicMock
from socket import error as socket_error

# Add the parent directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from client import Client
from protocol import ProtocolHandler, Error
from storage import CommandError

@pytest.fixture
def client():
    with patch('client.socket.socket') as mock_socket:
        mock_socket_inst = mock_socket.return_value
        mock_socket_inst.makefile.return_value = MagicMock()
        yield Client()

def test_get(client):
    with patch.object(ProtocolHandler, 'write_response') as mock_write, \
         patch.object(ProtocolHandler, 'handle_request', return_value='value') as mock_handle:
        assert client.get('key') == 'value'
        mock_write.assert_called_once_with(client._fh, ('GET', 'key'))
        mock_handle.assert_called_once_with(client._fh)

def test_set(client):
    with patch.object(ProtocolHandler, 'write_response') as mock_write, \
         patch.object(ProtocolHandler, 'handle_request', return_value='OK') as mock_handle:
        assert client.set('key', 'value') == 'OK'
        mock_write.assert_called_once_with(client._fh, ('SET', 'key', 'value'))
        mock_handle.assert_called_once_with(client._fh)

def test_delete(client):
    with patch.object(ProtocolHandler, 'write_response') as mock_write, \
         patch.object(ProtocolHandler, 'handle_request', return_value='OK') as mock_handle:
        assert client.delete('key') == 'OK'
        mock_write.assert_called_once_with(client._fh, ('DELETE', 'key'))
        mock_handle.assert_called_once_with(client._fh)

def test_flush(client):
    with patch.object(ProtocolHandler, 'write_response') as mock_write, \
         patch.object(ProtocolHandler, 'handle_request', return_value='OK') as mock_handle:
        assert client.flush() == 'OK'
        mock_write.assert_called_once_with(client._fh, ('FLUSH',))
        mock_handle.assert_called_once_with(client._fh)

def test_mget(client):
    with patch.object(ProtocolHandler, 'write_response') as mock_write, \
         patch.object(ProtocolHandler, 'handle_request', return_value=['value1', 'value2']) as mock_handle:
        assert client.mget('key1', 'key2') == ['value1', 'value2']
        mock_write.assert_called_once_with(client._fh, ('MGET', 'key1', 'key2'))
        mock_handle.assert_called_once_with(client._fh)

def test_mset(client):
    with patch.object(ProtocolHandler, 'write_response') as mock_write, \
         patch.object(ProtocolHandler, 'handle_request', return_value='OK') as mock_handle:
        assert client.mset('key1', 'value1', 'key2', 'value2') == 'OK'
        mock_write.assert_called_once_with(client._fh, ('MSET', 'key1', 'value1', 'key2', 'value2'))
        mock_handle.assert_called_once_with(client._fh)

def test_mset_odd_number_of_arguments(client):
    with pytest.raises(CommandError, match='MSET requires pairs of key/value arguments'):
        client.mset('key1', 'value1', 'key2')

def test_close(client):
    with patch.object(client._fh, 'close') as mock_fh_close, \
         patch.object(client._socket, 'close') as mock_socket_close:
        client.close()
        mock_fh_close.assert_called_once()
        mock_socket_close.assert_called_once()

def test_execute_command_error(client):
    with patch.object(ProtocolHandler, 'write_response') as mock_write, \
         patch.object(ProtocolHandler, 'handle_request', return_value=Error('error message')) as mock_handle:
        with pytest.raises(CommandError, match='error message'):
            client.execute('COMMAND')
        mock_write.assert_called_once_with(client._fh, ('COMMAND',))
        mock_handle.assert_called_once_with(client._fh)

def test_execute_socket_error(client):
    with patch.object(ProtocolHandler, 'write_response') as mock_write, \
         patch.object(ProtocolHandler, 'handle_request', side_effect=socket_error('socket error')) as mock_handle:
        with pytest.raises(CommandError, match='Connection error: socket error'):
            client.execute('COMMAND')
        mock_write.assert_called_once_with(client._fh, ('COMMAND',))
        mock_handle.assert_called_once_with(client._fh)

def test_client_init():
    with patch('client.socket.socket') as mock_socket:
        mock_socket_inst = mock_socket.return_value
        mock_socket_inst.makefile.return_value = MagicMock()
        client = Client()
        mock_socket_inst.connect.assert_called_once_with(('127.0.0.1', 31337))
        mock_socket_inst.makefile.assert_called_once_with('rwb')