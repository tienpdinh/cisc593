import sys
import os
import pytest

# Add the parent directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from storage import KeyValueStore, CommandError

@pytest.fixture
def store():
    return KeyValueStore()

def test_set_new_key(store):
    assert store.set('key1', 'value1') is True
    assert store.get('key1') == 'value1'

def test_set_existing_key(store):
    store.set('key1', 'value1')
    assert store.set('key1', 'value2') is True
    assert store.get('key1') == 'value2'

def test_set_value_too_large(store):
    large_value = 'x' * (store._max_memory + 1)
    with pytest.raises(CommandError, match='Value too large'):
        store.set('key1', large_value)

def test_set_eviction(store):
    small_store = KeyValueStore(max_memory_mb=1)
    small_store.set('key1', 'x' * 512 * 1024)
    small_store.set('key2', 'x' * 512 * 1024)
    assert small_store.get('key1') is None  # key1 should be evicted
    assert small_store.get('key2') == 'x' * 512 * 1024

def test_get_existing_key(store):
    store.set('key1', 'value1')
    assert store.get('key1') == 'value1'

def test_get_non_existing_key(store):
    assert store.get('key2') is None

def test_get_after_delete(store):
    store.set('key3', 'value3')
    store.delete('key3')
    assert store.get('key3') is None

def test_delete_existing_key(store):
    store.set('key1', 'value1')
    assert store.delete('key1') is True
    assert store.get('key1') is None

def test_delete_non_existing_key(store):
    assert store.delete('key2') is False

def test_flush(store):
    store.set('key1', 'value1')
    store.set('key2', 'value2')
    assert store.flush() == 2
    assert store.get('key1') is None
    assert store.get('key2') is None

def test_evict_oldest_empty(store):
    assert store._evict_oldest() is False