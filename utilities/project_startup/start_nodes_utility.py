import requests
import time
import argparse


def get_project_id(base_url, project_name):
    # Fetch the list of projects
    response = requests.get(f"{base_url}/projects")
    response.raise_for_status()

    projects = response.json()
    for project in projects:
        if project["name"] == project_name:
            return project["project_id"]

    raise Exception(f"No project found with name {project_name}")

def list_projects(server, port):
    response = requests.get(f"http://{server}:{port}/v2/projects")
    response.raise_for_status()
    return response.json()

def get_matching_nodes(base_url, project_id, match_string):
    response = requests.get(f"{base_url}/projects/{project_id}/nodes")
    response.raise_for_status()

    nodes = response.json()
    return [node for node in nodes if match_string in node["name"]]


def start_or_stop_node(base_url, project_id, node_id, action):
    response = requests.post(f"{base_url}/projects/{project_id}/nodes/{node_id}/{action}")
    response.raise_for_status()

    # Wait until node has started or stopped successfully
    while True:
        time.sleep(1)
        node_status = requests.get(f"{base_url}/projects/{project_id}/nodes/{node_id}").json()
        if action == "start" and node_status["status"] == "started":
            break
        elif action == "stop" and node_status["status"] == "stopped":
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start or stop nodes in GNS3 projects.")
    parser.add_argument("server_ip", help="IP address of the server.")
    parser.add_argument("server_port", type=int, help="Port number of the server.")
    parser.add_argument("project_name", help="Name of the GNS3 project.")
    parser.add_argument("action", choices=["start", "stop"], help="Action to perform on matching devices (start/stop).")
    parser.add_argument("match_strings", help="Comma-separated strings to match nodes.")


    args = parser.parse_args()

    base_url = f"http://{args.server_ip}:{args.server_port}/v2"
    project_id = get_project_id(base_url, args.project_name)

    for match_string in args.match_strings.split(','):
        match_string = match_string.strip()  # Remove any spaces

        # Get nodes matching the current string
        matching_nodes = get_matching_nodes(base_url, project_id, match_string)
        if not matching_nodes:
            print(f"No nodes found matching string '{match_string}'.")
            continue

        # Start or stop nodes
        for node in matching_nodes:
            print(f"{args.action.capitalize()}ing {node['name']}...")
            start_or_stop_node(base_url, project_id, node["node_id"], args.action)
            print(f"{node['name']} {args.action}ed successfully.")
