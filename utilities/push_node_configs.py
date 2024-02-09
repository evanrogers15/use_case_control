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

def upload_file_to_node(server, port, project_id, node_id, local_file_path, node_file_path):
    with open(local_file_path, 'rb') as file:
        file_content = file.read()
        headers = {'Content-Type': 'application/octet-stream'}
        response = requests.post(
            f"http://{server}:{port}/v2/projects/{project_id}/nodes/{node_id}/files{node_file_path}",
            data=file_content,
            headers=headers
        )
    response.raise_for_status()

def main():
    server = input("Enter the GNS3 server address: ")
    port = input("Enter the GNS3 server port: ")

    projects = list_projects(server, port)
    for idx, project in enumerate(projects):
        print(f"{idx}. {project['name']}")

    project_idx = int(input("Select a project by entering its index: "))
    selected_project = projects[project_idx]

    nodes = list_nodes(server, port, selected_project['project_id'])

    for node in nodes:
        node_dir = node['name']
        if os.path.exists(node_dir):
            for file_name in os.listdir(node_dir):
                local_file_path = os.path.join(node_dir, file_name)
                node_file_path = f"/etc/frr/{file_name}"
                # upload_file_to_node(server, port, selected_project['project_id'], node['node_id'], local_file_path, node_file_path)
                print(f"Uploaded {file_name} to {node['name']}.")

            # Upload latency_gen.py to the node's /etc/frr/ directory
            local_latency_gen_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'latency_generator.py')
            node_latency_gen_path = "/etc/frr/latency_generator.py"
            upload_file_to_node(server, port, selected_project['project_id'], node['node_id'], local_latency_gen_path, node_latency_gen_path)
            print(f"Uploaded latency_generator.py to {node['name']}.")

if __name__ == "__main__":
    main()
