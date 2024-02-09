#!/bin/bash

# Check if both SITES_COUNT and PORTS are defined
if [ -n "$SITES_COUNT" ] && [ -n "$PORTS" ]; then
    python3 /home/scripts/traffic_generator.py sites ${SITES_COUNT} ${PORTS} &
fi

# Check if both MGMT_SUBNET and FLOW_TARGET_IP are defined
if [ -n "$MGMT_SUBNET" ] && [ -n "$FLOW_TARGET_IP" ]; then
    python3 /home/netflow_forwarder_setup.py
    python3 /home/netflow_wrapper.py &
fi

# Start a shell to keep the Docker container running
/bin/bash
