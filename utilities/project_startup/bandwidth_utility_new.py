import requests
import telnetlib
import argparse

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
    tn.write(b"bash\n")
    tn.read_until(b"bash-5.1#")
    tn.write(command.encode('ascii') + b"\n")
    output = tn.read_until(b"#", timeout=5).decode('ascii')
    tn.close()
    return output

def main(args):
    projects = list_projects(args.server, args.port)

    project_id = next((project['project_id'] for project in projects if project['name'] == args.project_name), None)
    if not project_id:
        print(f"No project found with name {args.project_name}")
        return

    nodes = list_nodes(args.server, args.port, project_id)
    filtered_nodes = [node for node in nodes if args.node_name_portion in node['name']]

    for node in filtered_nodes:
        console_port = node['properties']['aux']
        if args.action == 'add':
            command = f"python3 /etc/frr/bandwidth_adjuster.py {args.action} {args.interface} {args.speed}"
            output = run_telnet_command(args.server, console_port, command)
            print(f"Output for {node ['name']}:\n{output}")

        elif args.action == 'remove':
            command = f"python3 /etc/frr/bandwidth_adjuster.py {args.action} {args.interface}"
            output = run_telnet_command(args.server, console_port, command)
            print(f"Output for {node ['name']}:\n{output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add or remove latencies on GNS3 nodes.")
    parser.add_argument("server", help="IP address of the GNS3 server.")
    parser.add_argument("port", type=int, help="Port number of the GNS3 server.")
    parser.add_argument("project_name", help="Name of the GNS3 project.")
    parser.add_argument("action", choices=["add", "remove"], help="Action to perform on the nodes (add/remove latency).")
    parser.add_argument("node_name_portion", help="Portion of the node name to filter nodes.")
    parser.add_argument("interface", help="Specify the name of the interface Ex: eth2")
    parser.add_argument("speed", help="Enter the desired interface speed Ex: 50")


    args = parser.parse_args()
    main(args)
