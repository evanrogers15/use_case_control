import requests
import telnetlib
import argparse
import time

def list_projects(server, port):
    response = requests.get(f"http://{server}:{port}/v2/projects")
    response.raise_for_status()
    return response.json()

def list_nodes(server, port, project_id):
    response = requests.get(f"http://{server}:{port}/v2/projects/{project_id}/nodes")
    response.raise_for_status()
    return response.json()

def run_telnet_command(host, port, command):
    tn = telnetlib.Telnet(host, port)
    tn.write(b"\n")
    tn.read_until(b"#")
    tn.write(command.encode('ascii') + b"\n")
    output = tn.read_until(b"#", timeout=5).decode('ascii')
    tn.write(b"\n")
    time.sleep(.5)
    tn.close()
    return output

def main(args):
    projects = list_projects(args.server, args.port)

    project_id = next((project['project_id'] for project in projects if project['name'] == args.project_name), None)
    if not project_id:
        print(f"No project found with name {args.project_name}")
        return

    command_1 = f"ip route add 172.16.6.0/24 via 172.16.254.2"
    command_2 = f"ip route add 172.16.7.0/24 via 172.16.254.2"
    command_3 = f"ip route add 172.16.8.0/24 via 172.16.254.2"
    command_4 = f"ip route add 172.16.9.0/24 via 172.16.254.2"

    nodes = list_nodes(args.server, args.port, project_id)
    filtered_nodes = [node for node in nodes if args.node_name_portion in node['name']]

    for node in filtered_nodes:
        console_port = node['properties']['aux']
        output = run_telnet_command(args.server, console_port, command_1)
        output = run_telnet_command(args.server, console_port, command_2)
        output = run_telnet_command(args.server, console_port, command_3)
        output = run_telnet_command(args.server, console_port, command_4)
        print(f"Output for {node['name']}:\n{output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy Routes to Cloud ISP Router")
    parser.add_argument("server", help="IP address of the GNS3 server.")
    parser.add_argument("port", type=int, help="Port number of the GNS3 server.")
    parser.add_argument("project_name", help="Name of the GNS3 project.")
    parser.add_argument("node_name_portion", help="Portion of the node name to filter nodes.")

    args = parser.parse_args()
    main(args)