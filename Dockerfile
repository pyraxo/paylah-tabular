# Use a lightweight base image
FROM eclipse-temurin:11-alpine

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache build-base gcc musl-dev python3 py3-pip python3-dev libffi-dev openssl-dev

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY server.py .

# Expose the port
EXPOSE 9119

# Set the JAVA_HOME environment variable
ENV JAVA_HOME=/opt/java/openjdk

# Update the LD_LIBRARY_PATH to include the Java library path
ENV LD_LIBRARY_PATH=$JAVA_HOME/lib/server

# Set the entrypoint command
CMD ["python", "server.py"]
