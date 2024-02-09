from scapy.all import *
import os
import subprocess
import re
import time

# Define constants
flow_target_ip = os.getenv("FLOW_TARGET_IP")
# flow_target_ip = "10.6.0.18"
full_management_subnet_ip = os.getenv("MGMT_SUBNET")  # example 172.16.253.0
# full_management_subnet_ip = "172.16.30.0"
flow_target_port = 9995

# Convert the full_management_subnet_ip to a string, if necessary
full_management_subnet_ip = str(full_management_subnet_ip)

# Extract the first three octets from the full management subnet IP
management_subnet_match = re.match(r"(\d+\.\d+\.\d+)\.\d+", full_management_subnet_ip)
if management_subnet_match:
    MANAGEMENT_SUBNET = management_subnet_match.group(1)
else:
    raise ValueError("Invalid MGMT_SUBNET format. Please provide a valid IPv4 address.")

def set_eth1_ip():
    # Calculate the new IP address for eth1 (30 added to the last octet of MANAGEMENT_SUBNET)
    eth1_ip = f"{MANAGEMENT_SUBNET}.30"

    # Set the IP address of eth1 using ifconfig
    subprocess.run(["ifconfig", "eth1", eth1_ip, "netmask", "255.255.255.0", "up"])

def add_route_to_flow_target():
    gateway_ip = f"{MANAGEMENT_SUBNET}.1"

    # Add a route to the FLOW_TARGET using the gateway IP
    subprocess.run(["route", "add", "-host", flow_target_ip, "gw", gateway_ip])

def is_netflow_packet(packet):
    # Check if the packet is a UDP packet and contains the NetflowHeader
    return UDP in packet and NetflowHeader in packet

def create_modified_packet(packet):
    if is_netflow_packet(packet):
        # Extract the third octet from the original source IP address
        original_source_ip = packet[IP].src
        third_octet = original_source_ip.split(".")[2]

        # Construct the new source IP address with the first three octets from MANAGEMENT_SUBNET and the third octet from the original source IP
        new_source_ip = f"{MANAGEMENT_SUBNET}.{third_octet}"

        flow_new_packet = IP(src=new_source_ip, dst=flow_target_ip) / UDP(sport=packet[UDP].sport, dport=flow_target_port) / \
                     packet[NetflowHeader]

        del flow_new_packet[IP].chksum
        del flow_new_packet[UDP].chksum

        # Forward the modified packet to the new target
        send(flow_new_packet, iface="eth1", verbose=0)

# Set the IP address of eth1
print("Setting eth1 IP Address.. Waiting 5 seconds...")
set_eth1_ip()
print("Waiting 5 seconds...")
time.sleep(5)
# Add a route to the specified FLOW_TARGET
print("Setting route to target.. Waiting 5 seconds...")
add_route_to_flow_target()
time.sleep(5)
print("Waiting 5 seconds...")
# Use the custom filter function to capture Netflow-related traffic
print("Starting packet forwarding...")
sniff(prn=create_modified_packet, iface="eth0", lfilter=is_netflow_packet)