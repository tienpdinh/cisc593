import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Add the parent directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server import Server, CommandError
from protocol import ProtocolHandler
from storage import KeyValueStore

@pytest.fixture
def server():
    with patch('server.KeyValueStore') as mock_kv_store:
        mock_kv_store_inst = mock_kv_store.return_value
        yield Server()

def test_get_response(server):
    with patch.object(server, '_commands', {'GET': MagicMock(return_value='value')}) as mock_commands:
        assert server.get_response(['GET', 'key']) == 'value'
        mock_commands['GET'].assert_called_once_with('key')

def test_get(server):
    with patch.object(server._kv, 'get', return_value='value') as mock_get:
        assert server.get('key') == 'value'
        mock_get.assert_called_once_with('key')

def test_set(server):
    with patch.object(server._kv, 'set', return_value=True) as mock_set:
        assert server.set('key', 'value') == 1
        mock_set.assert_called_once_with('key', 'value')

def test_delete(server):
    with patch.object(server._kv, 'delete', return_value=True) as mock_delete:
        assert server.delete('key') == 1
        mock_delete.assert_called_once_with('key')

def test_flush(server):
    with patch.object(server._kv, 'flush', return_value=2) as mock_flush:
        assert server.flush() == 2
        mock_flush.assert_called_once()

def test_mget(server):
    with patch.object(server._kv, 'get', side_effect=['value1', 'value2']) as mock_get:
        assert server.mget('key1', 'key2') == ['value1', 'value2']
        mock_get.assert_any_call('key1')
        mock_get.assert_any_call('key2')

def test_mset(server):
    with patch.object(server._kv, 'set', return_value=True) as mock_set:
        assert server.mset('key1', 'value1', 'key2', 'value2') == 2
        mock_set.assert_any_call('key1', 'value1')
        mock_set.assert_any_call('key2', 'value2')

def test_mset_odd_number_of_arguments(server):
    with pytest.raises(CommandError, match='MSET requires pairs of key/value arguments'):
        server.mset('key1', 'value1', 'key2')

def test_get_response_invalid_command(server):
    with pytest.raises(CommandError, match='Unrecognized command: INVALID'):
        server.get_response(['INVALID', 'key'])

def test_get_response_missing_command(server):
    with pytest.raises(CommandError, match='Missing command'):
        server.get_response([])

def test_get_response_invalid_request_type(server):
    with pytest.raises(CommandError, match='Request must be list or simple string'):
        server.get_response(None)