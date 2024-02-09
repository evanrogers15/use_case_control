#!/bin/bash

# Function to display help
function show_help() {
    echo "Usage: deploy.sh [OPTIONS]"
    echo "Deploy the network_test_tool container"
    echo ""
    echo "Options:"
    echo "  -d, --detach      Run the container in detached mode"
    echo "  --help            Display this help message"
    echo "  debug             Run the container in debug mode with bash"
}

# Function to stop and remove the existing container
function stop_existing_container() {
    existing_container=$(docker ps -a --filter "name=network_test_tool" --format '{{.Names}}' | grep -q '^network_test_tool$' && echo "true" || echo "false")
    if [ $existing_container == "true" ]; then
        echo "Stopping the existing network_test_tool container..."
        docker stop network_test_tool
        docker rm network_test_tool
    fi
}

# Check for the --help option
if [[ " $* " == *" --help "* ]]; then
    show_help
    exit 0
fi

# Stop and remove the existing container if it is running
stop_existing_container

# Check if the network_test_tool directory exists in the current directory
if [ -d "network_test_tool" ]; then
    rm -rf network_test_tool
fi

# Check if the network_test_tool directory exists in the parent directory
if [ -d "../network_test_tool" ]; then
    rm -rf ../network_test_tool
fi

# Clone the git project with the specified branch
git clone https://github.com/evanrogers15/network_test_tool.git

# Navigate to the network_test_tool directory
cd network_test_tool

# Build the Docker container with the test tag
docker build -t evanrogers719/network_test_tool:test .


# Check if the -d flag is passed
if [[ " $* " == *" -d "* ]]; then
    # Run the Docker container in detached mode with the specified port mapping(s) and container name
    docker run -d --name network_test_tool evanrogers719/network_test_tool:test
else
    # Run the Docker container in foreground with the specified port mapping(s) and container name
    docker run --name network_test_tool evanrogers719/network_test_tool:test
fi
