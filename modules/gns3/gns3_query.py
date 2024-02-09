import requests
import json

def gns3_query_get_computes_name(server, port):
    url = f"http://{server}:{port}/v2/computes"
    response = requests.get(url)
    if not response.ok:
        print(f"Error retrieving compute servers: {response.status_code}")
        exit()
    try:
        compute_info = response.json()
        server_name = compute_info[0]['name']
        return server_name
    except (ValueError, IndexError) as e:
        print(f"Error parsing JSON: {e}")
        print(f"Response content: {response.content}")
        exit()

def gns3_query_get_projects(server, port):
    url = f"http://{server}:{port}/v2/projects"
    response = requests.get(url)
    if not response.ok:
        print(f"Error retrieving links: {response.status_code}")
        exit()
    try:
        projects = response.json()
    except ValueError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Response content: {response.content}")
        exit()
    return projects

def gns3_query_get_nodes(server, port, project_id):
    url = f"http://{server}:{port}/v2/projects/{project_id}/nodes"
    response = requests.get(url)
    if not response.ok:
        print(f"Error retrieving links: {response.status_code}")
        exit()
    try:
        nodes = response.json()
    except ValueError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Response content: {response.content}")
        exit()
    return nodes

def gns3_query_get_links(server, port, project_id, node_id):
    url = f"http://{server}:{port}/v2/projects/{project_id}/nodes/{node_id}/links"
    response = requests.get(url)
    if not response.ok:
        print(f"Error retrieving links: {response.status_code}")
        exit()
    try:
        links = response.json()
    except ValueError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Response content: {response.content}")
        exit()
    return links

def gns3_query_find_node_by_name(nodes, node_name=None):
    if node_name:
        for node in nodes:
            if node['name'] == node_name:
                node_id = node['node_id']
                console = node['console']
                aux = node['properties'].get('aux')
                return node_id, console, aux
        print(f"Node '{node_name}' not found.")
    else:
        nuttcp_nodes = [node for node in nodes if 'NutTCP-Client' in node['name']]
        if not nuttcp_nodes:
            print("No nodes named with 'NutTCP' found.")
        else:
            print("Available nodes:")
            for i, node in enumerate(nuttcp_nodes):
                print(f"{i+1}. {node['name']}")
            selected_num = int(input("Enter the number of the node to select: "))
            selected_node = nuttcp_nodes[selected_num - 1]
            node_id = selected_node['node_id']
            console = selected_node['console']
            aux = selected_node['properties'].get('aux')
            return node_id, console, aux
    return None, None, None

def gns3_query_get_node_links(nodes, links, server, port, project_id, node_id, remote_node_id=None, adapter_port=None):
    link_id = None  # Initialize link_id as None
    seen_node_ids = set()
    for link in links:
        for node in link['nodes']:
            if adapter_port is not None and node['label']['text'] == adapter_port:
                link_id = link['link_id']
                link_url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link_id}"
                response = requests.get(link_url)
                link_data = response.json()
                return link_id  # Return the matching link_id

    return link_id  # Return None if no matching link_id is found

def gns3_query_get_location_data(server_ip, server_port, project_id, item_type):
    url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/{item_type}"
    response = requests.get(url)
    data = json.loads(response.text)
    nodes = []
    if item_type == 'nodes':
        for node in data:
            name = node['name']
            x = node['x']
            y = node['y']
            z = node['z']
            nodes.append({'name': name, 'x': x, 'y': y, 'z': z})
    elif item_type == 'drawings':
        for node in data:
            svg = node['svg']
            x = node['x']
            y = node['y']
            z = node['z']
            nodes.append({'svg': svg, 'x': x, 'y': y, 'z': z})
    location_data = nodes
    drawing_data = {}
    for i, item_data in enumerate(location_data):
        drawing_key = f"drawing_{i + 1:02}"
        drawing_data[drawing_key] = item_data
    return nodes

def gns3_query_find_nodes_by_field(server_ip, server_port, project_id, search_field, return_field, search_string):
    nodes = gns3_query_get_nodes(server_ip, server_port, project_id)
    if search_string:
        matching_nodes = [node for node in nodes if search_string in node[search_field]]
        if not matching_nodes:
            return []
        else:
            return [(node[return_field]) for node in matching_nodes]
    else:
        return []

def gns3_query_get_project_id(server_ip, server_port, project_name):
    url = f"http://{server_ip}:{server_port}/v2/projects"
    response = requests.get(url)
    projects = json.loads(response.text)
    for project in projects:
        if project['name'] == project_name:
            return project['project_id']
    return None

def gns3_query_get_template_id(server_ip, server_port, template_name):
    url = f"http://{server_ip}:{server_port}/v2/templates"
    response = requests.get(url)
    templates = json.loads(response.text)
    for template in templates:
        if template['name'] == template_name:
            return template['template_id']
    return None

def gns3_query_get_drawings(server_ip, server_port, project_id):
    url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/drawings"
    response = requests.get(url)
    if not response.ok:
        print(f"Error retrieving links: {response.status_code}")
        exit()
    try:
        nodes = response.json()
    except ValueError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Response content: {response.content}")
        exit()
    return nodes

def gns3_query_get_image(server_ip, server_port, image_type, filename):
    url = f"http://{server_ip}:{server_port}/v2/compute/{image_type}/images"
    response = requests.get(url)
    for image in response.json():
        if image['filename'] == filename:
            return 201
    return 200

def gns3_query_get_node_files(server_ip, server_port, project_id, node_id, file_path):
    url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}/files/{file_path}"
    response = requests.get(url)
    if not response.ok:
        print(f"Error retrieving links: {response.status_code}")
        exit()
    try:
        nodes = response.json()
    except ValueError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Response content: {response.content}")
        exit()
    return nodes

def gns3_query_find_nodes_by_name(server_ip, server_port, project_id, search_string=None):
    node_data = gns3_query_get_nodes(server_ip, server_port, project_id)
    if search_string:
        matching_nodes = [node for node in node_data if search_string in node['name']]
        if not matching_nodes:
            return []
        else:
            return [(node['node_id'], node['console'], node['properties'].get('aux')) for node in matching_nodes]
    else:
        return []