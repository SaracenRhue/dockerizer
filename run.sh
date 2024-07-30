#!/bin/bash

CURRENT_DIR=$(pwd)
# Run the dockerized tool
docker run --rm -v "$CURRENT_DIR":/app saracenrhue/dockerizer:latest

# Check if the docker command was successful
if [ $? -eq 0 ]; then
    echo "Dockerfile generation completed successfully."
else
    echo "An error occurred while generating the Dockerfile."
fi