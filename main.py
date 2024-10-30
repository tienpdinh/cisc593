from gevent import monkey
import logging

from server import Server

if __name__ == '__main__':
    # Patch stdlib with gevent alternatives
    monkey.patch_all()
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start server
    server = Server()
    server.run()