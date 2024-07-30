#!/bin/bash

# Function to print error messages
error() {
    echo "Error: $1" >&2
    exit 1
}

# Check if Docker is installed
command -v docker >/dev/null 2>&1 || error "Docker is not installed. Please install Docker and try again."

# Get the current directory
CURRENT_DIR="$(pwd)"

# Ensure CURRENT_DIR is not empty
[ -z "$CURRENT_DIR" ] && error "Failed to get current directory."

# Pull the latest image
echo "Pulling the latest dockerizer image..."
docker pull saracenrhue/dockerizer:latest 2>&1 | grep -v -e "What's Next?" -e "View a summary of image vulnerabilities" || error "Failed to pull the latest image."


# Run the dockerized tool
echo "Analyzing project in $CURRENT_DIR..."
docker run --rm -v "$CURRENT_DIR":/app saracenrhue/dockerizer:latest

# Check if the docker command was successful
if [ $? -eq 0 ]; then
    echo "Dockerfile generation completed successfully."
else
    error "An error occurred while generating the Dockerfile."
fi