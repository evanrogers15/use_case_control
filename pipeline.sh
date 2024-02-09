#!/bin/bash

# Function to display help
function show_help() {
    echo "Usage: deploy.sh [OPTIONS]"
    echo "Deploy the use_case_control container"
    echo ""
    echo "Options:"
    echo "  -d, --detach      Run the container in detached mode"
    echo "  --help            Display this help message"
    echo "  debug             Run the container in debug mode with bash"
}

# Function to stop and remove the existing container
function stop_existing_container() {
    existing_container=$(docker ps -a --filter "name=use_case_control" --format '{{.Names}}' | grep -q '^use_case_control$' && echo "true" || echo "false")
    if [ $existing_container == "true" ]; then
        echo "Stopping the existing use_case_control container..."
        docker stop use_case_control
        docker rm use_case_control
    fi
}

# Check for the --help option
if [[ " $* " == *" --help "* ]]; then
    show_help
    exit 0
fi

# Stop and remove the existing container if it is running
stop_existing_container

# Check if the use_case_control directory exists in the current directory
if [ -d "use_case_control" ]; then
    rm -rf use_case_control
fi

# Check if the use_case_control directory exists in the parent directory
if [ -d "../use_case_control" ]; then
    rm -rf ../use_case_control
fi

# Clone the git project with the specified branch
git clone https://github.com/evanrogers15/use_case_control.git

# Navigate to the use_case_control directory
cd use_case_control

# Build the Docker container with the test tag
docker build -t evanrogers15/use_case_control:test .


# Check if the -d flag is passed
if [[ " $* " == *" -d "* ]]; then
    # Run the Docker container in detached mode with the specified port mapping(s) and container name
    docker run -d --name use_case_control evanrogers15/use_case_control:test
else
    # Run the Docker container in foreground with the specified port mapping(s) and container name
    docker run --name use_case_control evanrogers15/use_case_control:test
fi
