#!/bin/bash

# Function to display help
function show_help() {
    echo "Usage: deploy.sh [OPTIONS]"
    echo "Deploy the gns3_auto_deploy container"
    echo ""
    echo "Options:"
    echo "  -d, --detach      Run the container in detached mode"
    echo "  -p, --port PORT   Specify the port to expose (default: 8080)"
    echo "  --help            Display this help message"
    echo "  debug             Run the container in debug mode with bash"
}

# Function to stop and remove the existing container
function stop_existing_container() {
    existing_container=$(docker ps -a --filter "name=gns3_auto_deploy_test" --format '{{.Names}}' | grep -q '^gns3_auto_deploy_test$' && echo "true" || echo "false")
    if [ $existing_container == "true" ]; then
        echo "Stopping the existing gns3_auto_deploy_test container..."
        docker stop gns3_auto_deploy_test
        docker rm gns3_auto_deploy_test
    fi
}

# Check for the --help option
if [[ " $* " == *" --help "* ]]; then
    show_help
    exit 0
fi

# Stop and remove the existing container if it is running
stop_existing_container

# Check if the gns3_auto_deploy directory exists in the current directory
if [ -d "gns3_auto_deploy" ]; then
    rm -rf gns3_auto_deploy
fi

# Check if the gns3_auto_deploy directory exists in the parent directory
if [ -d "../gns3_auto_deploy" ]; then
    rm -rf ../gns3_auto_deploy
fi

# Clone the git project with the specified branch
git clone --branch prod_multi_deployment https://github.com/evanrogers15/gns3_auto_deploy.git

# Navigate to the gns3_auto_deploy directory
cd gns3_auto_deploy

# Build the Docker container with the test tag
docker build -t evanrogers719/gns3_auto_deploy:test .

# Check if the -p flag is passed
if [[ " $* " == *" -p "* ]]; then
    # Extract the port value(s) using grep and awk
    port_values=$(echo "$*" | grep -o -P '(?<=-p\s)\S+' | awk '{print " -p "$1":8080"}')
else
    # Default port mapping: 8080:8080
    port_values=" -p 8080:8080"
fi

# Check if the -d flag is passed
if [[ " $* " == *" -d "* ]]; then
    # Run the Docker container in detached mode with the specified port mapping(s) and container name
    docker run -d --name gns3_auto_deploy_test $port_values evanrogers719/gns3_auto_deploy:test
else
    # Run the Docker container in foreground with the specified port mapping(s) and container name
    docker run --name gns3_auto_deploy_test $port_values evanrogers719/gns3_auto_deploy:test
fi
