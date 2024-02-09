import sys
import subprocess

def usage():
    print("Usage:")
    print("script.py add <interface> <speed in mbps>")
    print("script.py remove <interface>")

def run_command(command, ignore_error=False):
    process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if process.returncode != 0 and not ignore_error:
        print(f"Error executing command: {command}")
        print(process.stderr)
        sys.exit(1)
    return process

def add_limitation(interface, speed):
    ifb_device = f"ifb-{interface}"

    # Check if IFB device exists
    result = run_command(f"ip link show {ifb_device}", ignore_error=True)
    if ifb_device not in result.stdout:
        # Create IFB device for inbound limit if not exists
        run_command(f"ip link add {ifb_device} type ifb")
        run_command(f"ip link set up dev {ifb_device}")

    # Redirect interface ingress traffic to IFB device
    run_command(f"tc qdisc add dev {interface} handle ffff: ingress")
    run_command(f"tc filter add dev {interface} parent ffff: protocol ip u32 match u32 0 0 action mirred egress redirect dev {ifb_device}")

    # Limit inbound bandwidth on IFB device
    run_command(f"tc qdisc add dev {ifb_device} root handle 1: htb default 10")
    run_command(f"tc class add dev {ifb_device} parent 1: classid 1:1 htb rate {speed}mbit ceil {speed}mbit")
    run_command(f"tc class add dev {ifb_device} parent 1: classid 1:10 htb rate {speed}mbit ceil {speed}mbit")

    # Limit outbound bandwidth on interface
    run_command(f"tc qdisc add dev {interface} root handle 1: htb default 10")
    run_command(f"tc class add dev {interface} parent 1: classid 1:1 htb rate {speed}mbit ceil {speed}mbit")
    run_command(f"tc class add dev {interface} parent 1: classid 1:10 htb rate {speed}mbit ceil {speed}mbit")

    print(f"Bandwidth limited to {speed}Mbps on interface {interface}")

def remove_limitation(interface):
    ifb_device = f"ifb-{interface}"

    # Remove bandwidth limitation from the interface
    run_command(f"tc qdisc del dev {interface} root")
    run_command(f"tc qdisc del dev {interface} handle ffff: ingress")

    # Remove bandwidth limitation from the IFB device
    run_command(f"tc qdisc del dev {ifb_device} root", ignore_error=True)

    # Delete IFB device
    run_command(f"ip link del {ifb_device}", ignore_error=True)

    print(f"Removed bandwidth limitation from interface {interface}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        usage()
        sys.exit(1)

    operation = sys.argv[1]
    interface = sys.argv[2]

    if operation == "add":
        if len(sys.argv) != 4:
            usage()
            sys.exit(1)
        speed = sys.argv[3]
        add_limitation(interface, speed)

    elif operation == "remove":
        remove_limitation(interface)

    else:
        usage()
        sys.exit(1)
