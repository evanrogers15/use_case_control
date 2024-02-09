import os
import subprocess
import sys

def apply_delay(eth_interface, delay=None, action="add"):
    JITTER = "2ms"  # Set the jitter to 2ms

    if action == "add" and delay:
        cmd = ["tc", "qdisc", "add", "dev", eth_interface, "root", "netem", "delay", delay, JITTER]
        print(cmd)
        subprocess.run(cmd)
        print(f"Base delay of {delay} with +/- {JITTER} jitter applied to {eth_interface}")
    elif action == "remove":
        cmd = ["tc", "qdisc", "del", "dev", eth_interface, "root"]
        subprocess.run(cmd)
        print(f"Delay removed from {eth_interface}")


def main():
    # Check for correct number of command-line arguments
    if len(sys.argv) < 3:
        print("Usage: python latency_gen.py [add|remove] [interface] [delay]")
        return

    action = sys.argv[1]
    interface = sys.argv[2]
    delay = sys.argv[3] if len(sys.argv) > 3 else None

    if action not in ["add", "remove"]:
        print("Invalid action. Please use 'add' or 'remove'.")
        return

    if action == "add" and not delay:
        print("You must specify a delay when adding latency.")
        return

    apply_delay(interface, delay, action)

if __name__ == "__main__":
    main()
