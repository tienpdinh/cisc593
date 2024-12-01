# Miniature Redis Server
Source code for a miniature Redis server with API endpoints in Flask
## Build the Docker image
You need `docker` installed for this step
```
docker build -t miniature-redis-server .
```
## Run the server container to start the app
```
docker compose up -d
```
## API usage
Example `mset` request
```
curl -X POST http://localhost:8000/mset \
     -H "Content-Type: application/json" \
     -d '{
           "k1": "v1",
           "k2": ["v2-0", 1, "v2-2"],
           "k3": "v3"
         }'
```