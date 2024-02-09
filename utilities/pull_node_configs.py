import os
import requests


def list_projects(server, port):
    response = requests.get(f"http://{server}:{port}/v2/projects")
    response.raise_for_status()
    return response.json()


def list_nodes(server, port, project_id):
    response = requests.get(f"http://{server}:{port}/v2/projects/{project_id}/nodes")
    response.raise_for_status()
    return response.json()


def get_node_config(server, port, project_id, node_id, filename):
    response = requests.get(f"http://{server}:{port}/v2/projects/{project_id}/nodes/{node_id}/files/{filename}")
    response.raise_for_status()
    return response.content.decode('utf-8')


def main():
    server = input("Enter the GNS3 server address: ")
    port = input("Enter the GNS3 server port: ")

    projects = list_projects(server, port)
    for idx, project in enumerate(projects):
        print(f"{idx}. {project ['name']}")

    project_idx = int(input("Select a project by entering its index: "))
    selected_project = projects [project_idx]

    # Ask for the desired filename
    desired_filename = input("Enter the filename you want to retrieve (e.g., /etc/frr/frr.conf): ")

    partial_node_name = input("Enter a portion of the node name: ")
    nodes = [node for node in list_nodes(server, port, selected_project ['project_id']) if
             partial_node_name in node ['name']]

    for node in nodes:
        node_config = get_node_config(server, port, selected_project ['project_id'], node ['node_id'], desired_filename)

        # Create directory with the node name
        node_dir = node ['name']
        if not os.path.exists(node_dir):
            os.mkdir(node_dir)

        # Save the configuration inside the directory
        local_file_name = os.path.basename(desired_filename)
        with open(os.path.join(node_dir, local_file_name), 'w') as file:
            file.write(node_config)

        print(f"Config from {desired_filename} for {node ['name']} saved successfully!")


if __name__ == "__main__":
    main()
