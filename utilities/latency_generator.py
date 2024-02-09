import os
import subprocess
import sys
import socket

LATENCY_DATA = {
    "core_bgp_newyork": [{"interface": "eth1", "delay": "16ms"}, {"interface": "eth2", "delay": "20ms"}],
    "core_bgp_detroit": [{"interface": "eth1", "delay": "9ms"}],
    "core_bgp_chicago": [{"interface": "eth1", "delay": "15ms"}, {"interface": "eth2", "delay": "20ms"}],
    "core_bgp_nashville": [{"interface": "eth1", "delay": "8ms"}, {"interface": "eth2", "delay": "6ms"}],
    "core_bgp_atlanta": [{"interface": "eth2", "delay": "15ms"}, {"interface": "eth3", "delay": "18ms"}],
    "core_bgp_miami": [{"interface": "eth2", "delay": "25ms"}],
    "core_bgp_houston": [{"interface": "eth2", "delay": "22ms"}],
    "isp-houston": [{"interface": "eth2", "delay": "20ms"}],
    "core_bgp_kansascity": [{"interface": "eth2", "delay": "10ms"}],
    "core_bgp_denver": [{"interface": "eth1", "delay": "20ms"}, {"interface": "eth2", "delay": "8ms"},
        {"interface": "eth3", "delay": "5ms"}, {"interface": "eth4", "delay": "12ms"}],
    "core_bgp_minneapolis": [{"interface": "eth1", "delay": "8ms"}],
    "core_bgp_billings": [{"interface": "eth2", "delay": "5ms"}, {"interface": "eth3", "delay": "6ms"}],
    "core_bgp_saltlakecity": [{"interface": "eth1", "delay": "6ms"}, {"interface": "eth3", "delay": "6ms"},
        {"interface": "eth4", "delay": "6ms"}], "core_bgp_phoenix": [{"interface": "eth1", "delay": "6ms"}],
    "core_bgp_sanfrancisco": [{"interface": "eth1", "delay": "6ms"}]
}

def apply_delay(eth_interface, delay=None, action="add"):
    JITTER = "2ms"  # Set the jitter to 2ms

    if action == "add" and delay:
        cmd = ["tc", "qdisc", "add", "dev", eth_interface, "root", "netem", "delay", delay, JITTER]
        subprocess.run(cmd)
        print(f"Base delay of {delay} with +/- {JITTER} jitter applied to {eth_interface}")
    elif action == "remove":
        cmd = ["tc", "qdisc", "del", "dev", eth_interface, "root", "netem"]
        subprocess.run(cmd)
        print(f"Delay removed from {eth_interface}")


def main():
    # Check for correct command-line arguments
    if len(sys.argv) != 2 or sys.argv[1] not in ["add", "remove"]:
        print("Usage: python latency_gen.py [add|remove]")
        return

    action = sys.argv[1]

    # Get the hostname of the local system
    hostname = socket.gethostname()

    # Check if the hostname matches an object in the LATENCY_DATA dictionary
    if hostname in LATENCY_DATA:
        for entry in LATENCY_DATA[hostname]:
            if action == "add":
                apply_delay(entry['interface'], entry['delay'], action)
            elif action == "remove":
                apply_delay(entry['interface'], action=action)
    else:
        print(f"No latency configuration found for hostname: {hostname}")


if __name__ == "__main__":
    main()
