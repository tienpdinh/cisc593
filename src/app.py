from flask import Flask, request, jsonify
from client import Client, CommandError
from gevent import monkey
import logging
from server import Server
from threading import Thread
import time

# Patch stdlib with gevent alternatives
monkey.patch_all()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize Flask app
app = Flask(__name__)

# Function to start the server
def start_server():
    server = Server()
    server.run()

# Start the server in a separate thread
server_thread = Thread(target=start_server)
server_thread.start()

# Wait for the server to start
time.sleep(2)

@app.route('/get/<key>', methods=['GET'])
def get_key(key):
    client = Client()
    try:
        value = client.get(key)
        return jsonify({'key': key, 'value': value}), 200
    except CommandError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/set', methods=['POST'])
def set_key():
    client = Client()
    data = request.json
    key = data.get('key')
    value = data.get('value')
    try:
        result = client.set(key, value)
        return jsonify({'result': result}), 200
    except CommandError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/delete/<key>', methods=['DELETE'])
def delete_key(key):
    client = Client()
    try:
        result = client.delete(key)
        return jsonify({'result': result}), 200
    except CommandError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/flush', methods=['POST'])
def flush():
    client = Client()
    try:
        result = client.flush()
        return jsonify({'result': result}), 200
    except CommandError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/mget', methods=['POST'])
def mget_keys():
    client = Client()
    data = request.json
    keys = data.get('keys')
    try:
        values = client.mget(*keys)
        return jsonify({'keys': keys, 'values': values}), 200
    except CommandError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/mset', methods=['POST'])
def mset_keys():
    client = Client()
    data = request.json
    items = []
    for key, value in data.items():
        items.append(key)
        items.append(value)
    try:
        result = client.mset(*items)
        return jsonify({'result': result}), 200
    except CommandError as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    # Start the Flask app
    app.run(host='0.0.0.0', port=8000)