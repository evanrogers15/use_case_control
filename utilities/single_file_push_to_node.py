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

    search_string = input("Enter a string to search for GNS3 nodes: ")
    nodes = list_nodes(server, port, selected_project['project_id'])
    nodes = [node for node in nodes if search_string.lower() in node['name'].lower()]

    for node in nodes:
        node_dir = node['name']
        if os.path.exists(node_dir):
            for file_name in os.listdir(node_dir):
                local_file_path = os.path.join(node_dir, file_name)
                node_file_path = f"/etc/frr/{file_name}"
                upload_file_to_node(server, port, selected_project['project_id'], node['node_id'], local_file_path, node_file_path)
                print(f"Uploaded {file_name} to {node['name']}.")

            # Prompt user for file to upload
            user_file = input(f"Enter the path of the file you want to push to {node['name']} (or press enter to skip): ")
            if user_file:
                if os.path.exists(user_file):
                    node_file_path = f"/etc/frr/{os.path.basename(user_file)}"
                    upload_file_to_node(server, port, selected_project['project_id'], node['node_id'], user_file, node_file_path)
                    print(f"Uploaded {os.path.basename(user_file)} to {node['name']}.")
                else:
                    print(f"File {user_file} not found.")

if __name__ == "__main__":
    main()
