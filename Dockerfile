# Use the official Python 3.13 slim image as the base image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY src/ ./src/

# Expose the port the server will run on
EXPOSE 8000

# Set the environment variable for the server address and port
ENV SERVER_ADDRESS=0.0.0.0
ENV SERVER_PORT=8000

# Run the Flask app and the server
CMD ["python", "src/app.py"]