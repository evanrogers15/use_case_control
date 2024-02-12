import datetime
import urllib3
import os
import logging.handlers
import sqlite3
import re
import telnetlib
import socket
import time

from modules.gns3.gns3_variables import *
from modules.gns3.gns3_query import *

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# region Functions: Utilities
def make_request(method, url, data=None):
    if method == "GET":
        response = requests.get(url)
    elif method == "POST":
        response = requests.post(url, json=data)  # Add json=data here
    elif method == "PUT":
        response = requests.put(url, json=data)
    elif method == "DELETE":
        response = requests.delete(url)
    else:
        raise ValueError("Invalid method")
    response.raise_for_status()
    if response.content:
        return response.json()
    else:
        return {}

def log_and_update_db(server_name=None, project_name=None, deployment_type=None, deployment_status=None, deployment_step=None, log_message=None):
    # Log the message using logging.info
    logging.info(log_message)

    # Insert a new record into the deployments table
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    insert_query = '''
        INSERT INTO deployments (timestamp, server_name, project_name, deployment_type, deployment_status, deployment_step, log_message)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    '''
    current_time = util_current_time()
    c.execute(insert_query, (current_time, server_name, project_name, deployment_type, deployment_status, deployment_step, log_message))
    conn.commit()
    conn.close()

def util_extract_csr(response):
    json_data = response.json()
    if 'data' in json_data:
        return json_data['data']
    else:
        raise Exception(f"Failed to extract CSR. Response: {json_data}")

def util_print_response(response_data):
    if response_data.content:
        json_data = response_data.json()
        logging.info(json.dumps(json_data, indent=4))
    else:
        logging.info("Response content is empty.")

def util_get_file_size(file_path):
    size = os.path.getsize(file_path)
    size_name = ["B", "KB", "MB", "GB"]
    i = 0
    while size > 1024:
        size = size / 1024
        i += 1
    return f"{size:.2f} {size_name[i]}"

def util_resume_time(delay_time):
    resume_time = (datetime.datetime.now() + datetime.timedelta(minutes=delay_time)).strftime("%H:%M:%S")
    return resume_time

def util_current_time():
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return current_time
# endregion

# region Functions: GNS3 API Functions
def gns3_create_project(server_ip, server_port, project_name):
    template_data = {"name": project_name}
    node_url = f"http://{server_ip}:{server_port}/v2/projects"
    node_response = make_request("POST", node_url, data=template_data)
    project_id = node_response["project_id"]
    return project_id

def gns3_create_drawing(gns3_server_data, project_id, node_data):
    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, deployment_type, deployment_status, deployment_step = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Server Name'], server_record['Project Name'], server_record['Deployment Type'], server_record['Deployment Status'], server_record['Deployment Step']
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/drawings"
        node_response = make_request("POST", node_url, data=node_data)
        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                          f"Created Drawing")

def gns3_create_node(gns3_server_data, project_id, template_id, node_data):
    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, deployment_type, deployment_status, deployment_step = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Server Name'], server_record['Project Name'], server_record['Deployment Type'], server_record['Deployment Status'], server_record['Deployment Step']
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/templates/{template_id}"
        node_response = make_request("POST", node_url, data=node_data)
        node_name = node_response["name"]
        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Created Node {node_name}")
        node_id = node_response["node_id"]
        return node_id

def gns3_create_node_multi_return(gns3_server_data, project_id, template_id, node_data):
    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, deployment_type, deployment_status, deployment_step = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Server Name'], server_record['Project Name'], server_record['Deployment Type'], server_record['Deployment Status'], server_record['Deployment Step']
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/templates/{template_id}"
        node_response = make_request("POST", node_url, data=node_data)
        node_name = node_response["name"]
        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Created Node {node_name}")
        node_id = node_response["node_id"]
        return node_id, node_name

def gns3_create_cloud_node(gns3_server_data, project_id, node_data):
    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, deployment_type, deployment_status, deployment_step = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Server Name'], server_record['Project Name'], server_record['Deployment Type'], server_record['Deployment Status'], server_record['Deployment Step']
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes"
        node_response = make_request("POST", node_url, data=node_data)
        node_name = node_response["name"]
        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Created Node {node_name}")
        node_id = node_response["node_id"]
        return node_id

def gns3_create_template(gns3_server_data, template_data):
    for server_record in gns3_server_data:
        server_ip = server_record['GNS3 Server']
        server_port = server_record['Server Port']
        server_name = server_record['Server Name']
        project_name = server_record['Project Name']
        deployment_type = server_record['Deployment Type']
        deployment_status = server_record['Deployment Status']
        deployment_step = server_record['Deployment Step']

        node_url = f"http://{server_ip}:{server_port}/v2/templates"
        node_response = make_request("POST", node_url, data=template_data)

        if "template_id" in node_response and "name" in node_response:
            template_id = node_response["template_id"]
            template_name = node_response["name"]
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Created template {template_name}")
            return template_id
        else:
            error_message = f"Failed to create template on {server_name} - {project_name}. Error: {node_response.get('error', 'Unknown error')}"
            log_and_update_db(server_name, project_name, deployment_type, 'Failed', deployment_step, error_message)
            raise Exception(error_message)

def gns3_connect_nodes(gns3_server_data, project_id, node_a, adapter_a, port_a, node_b, adapter_b, port_b):
    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, deployment_type, deployment_status, deployment_step = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Server Name'], server_record['Project Name'], server_record['Deployment Type'], server_record['Deployment Status'], server_record['Deployment Step']
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/links"
        node_data = {"nodes": [{"adapter_number": adapter_a, "node_id": node_a, "port_number": port_a},
                               {"adapter_number": adapter_b, "node_id": node_b, "port_number": port_b}]}
        node_a_name = gns3_query_find_nodes_by_field(server_ip, server_port, project_id, 'node_id', 'name', node_a)
        node_b_name = gns3_query_find_nodes_by_field(server_ip, server_port, project_id, 'node_id', 'name', node_b)
        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Connected (adapter/port) {adapter_a}/{port_a} of {node_a_name[0]} to (adapter/port) {adapter_b}/{port_b} of {node_b_name[0]}")
        node_response = make_request("POST", node_url, data=node_data)
        return node_response["link_id"]

def gns3_delete_nodes(gns3_server_data, project_id, delete_node_name):
    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, deployment_type, deployment_status, deployment_step = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Server Name'], server_record['Project Name'], server_record['Deployment Type'], server_record['Deployment Status'], server_record['Deployment Step']
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, delete_node_name)
        if matching_nodes:
            for node_id, console_port, aux in matching_nodes:
                delete_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}"
                response = make_request("DELETE", delete_url)
                node_name = response["name"]
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Deleted node {node_name} on GNS3 Server {server_ip}")
        else:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"No nodes with '{delete_node_name}' in their name were found in project {project_name} on GNS3 Server {server_ip}")

def gns3_delete_all_nodes(server_ip, server_port, project_id):
    nodes = gns3_query_get_nodes(server_ip, server_port, project_id)
    for node in nodes:
        node_id = node['node_id']
        delete_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}"
        response = make_request("DELETE", delete_url)
        node_name = node["name"]
    log_and_update_db(deployment_status='Running', deployment_step='Setup', log_message=f"Deleted node all nodes on GNS3 Server {server_ip}")

def gns3_delete_all_drawings(server_ip, server_port, project_id):
    drawings = gns3_query_get_drawings(server_ip, server_port, project_id)
    for drawing in drawings:
        drawing_id = drawing['drawing_id']
        delete_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/drawings/{drawing_id}"
        response = make_request("DELETE", delete_url)
    log_and_update_db(deployment_status='Running', deployment_step='Setup', log_message=f"Deleted all drawings on GNS3 Server {server_ip}")

def gns3_delete_template(gns3_server_data, template_name):
    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, deployment_type, deployment_status, deployment_step = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Server Name'], server_record['Project Name'], server_record['Deployment Type'], server_record['Deployment Status'], server_record['Deployment Step']
        template_id = gns3_query_get_template_id(server_ip, server_port, template_name)
        if template_id:
            delete_url = f"http://{server_ip}:{server_port}/v2/templates/{template_id}"
            make_request("DELETE", delete_url)
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Deleted template ID {template_name} on GNS3 Server {server_ip}")
        else:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"No templates with '{template_name}' in their name were found on GNS3 Server {server_ip}")

def gns3_delete_project(gns3_server_data):
    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, deployment_type, deployment_status, deployment_step = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Server Name'], server_record['Project Name'], server_record['Deployment Type'], server_record['Deployment Status'], server_record['Deployment Step']
        project_id = gns3_query_get_project_id(server_ip, server_port)
        if project_id:
            delete_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}"
            make_request("DELETE", delete_url)
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Deleted project ID {project_name} on GNS3 Server {server_ip}")
        else:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"No projects with '{project_name}' in their name were found on GNS3 Server {server_ip}")

def gns3_delete_project_static(server_ip, server_port, project_name, project_id):
    if project_id:
        delete_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}"
        make_request("DELETE", delete_url)
        log_and_update_db(f"Deleted project ID {project_name} on GNS3 Server {server_ip}")
    else:
        log_and_update_db(f"No projects with '{project_name}' in their name were found on GNS3 Server {server_ip}")

def gns3_reload_node(gns3_server_data, project_id, node_id):
    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, deployment_type, deployment_status, deployment_step = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Server Name'], server_record['Project Name'], server_record['Deployment Type'], server_record['Deployment Status'], server_record['Deployment Step']
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}/reload"
        response = make_request("POST", node_url, data={})
        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Reloaded node {node_id}")

def gns3_upload_symbol(gns3_server_data, symbol_file, symbol_name):
    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, deployment_type, deployment_status, deployment_step = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Server Name'], server_record['Project Name'], server_record['Deployment Type'], server_record['Deployment Status'], server_record['Deployment Step']
        url = f'http://{server_ip}:{server_port}/v2/symbols/{symbol_name}/raw'
        headers = {"accept": "*/*"}
        response = requests.post(url, headers=headers, data=symbol_file)
        if response.status_code == 204:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f'Uploaded symbol {symbol_name}')
            return
        else:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f'Failed to upload {symbol_name}. Status code: {response.status_code}')

def gns3_upload_file_to_node(gns3_server_data, project_id, node_id, file_path_var, filename_temp):
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), '../configs/')
    file_path = os.path.join(configs_path, filename_temp)
    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, deployment_type, deployment_status, deployment_step = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Server Name'], server_record['Project Name'], server_record['Deployment Type'], server_record['Deployment Status'], server_record['Deployment Step']
        # Set the file path and name to be written to the node
        node_name = gns3_query_find_nodes_by_field(server_ip, server_port, project_id, 'node_id', 'name', node_id)

        # Set the API endpoint URL for the node file write
        url = f'http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}/files/{file_path_var}'

        # Open the local file and read its content
        with open(file_path, 'r') as f:
            file_content = f.read()

        # Set the API request headers and payload
        headers = {"accept": "application/json"}
        request_data = file_content.encode('utf-8')

        # Send the API request to write the file to the node
        response = requests.post(url, headers=headers, data=request_data)

        # Check if the API request was successful
        if response.status_code == 201:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f'File - {filename_temp} successfully written to the node {node_name[0]}')
            return
        else:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f'Failed to write file to the node {node_name[0]}. Status code: {response.status_code}')

def gns3_upload_image(gns3_server_data, image_type, filename):
    image_file_path = f'/app/images/{image_type}'
    file_path = os.path.join(image_file_path, filename)
    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, deployment_type, deployment_status, deployment_step = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Server Name'], server_record['Project Name'], server_record['Deployment Type'], server_record['Deployment Status'], server_record['Deployment Step']
        url = f'http://{server_ip}:{server_port}/v2/compute/{image_type}/images/{filename}'
        response = gns3_query_get_image(server_ip, server_port, image_type, filename)
        if response == 200:
            headers = {"accept": "*/*"}
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f'Image - {filename} being uploaded to server. Please wait..')
            response = requests.post(url, headers=headers, data=open(file_path, "rb"))
            if response.status_code == 204:
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f'Image - {filename} successfully written to server')
                return
            else:
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f'Failed to write file to the server. Status code: {response.status_code}')

def gns3_check_for_image(server_ip, server_port, version, image):
    url = f"http://{server_ip}:{server_port}/v2/computes/local/{version}/images"
    try:
        response = requests.get(url)
        data = response.json()

        # Filter filenames containing "pathview"
        image_names = [item['filename'] for item in data if image in item['filename']]

        # Extract version numbers using regular expressions
        version_numbers = [re.findall(r'\d+\.\d+\.\d+(?:\.\d+)?', filename) for filename in image_names]

        # Sort filenames based on the highest version number
        sorted_files = sorted(zip(image_names, version_numbers), key=lambda x: tuple(map(str, x[1])), reverse=True)

        # Return the filename with the highest version number
        if sorted_files:
            log_and_update_db(deployment_status='Running', deployment_step='Image Verification',
                              log_message=f'{image} found on GNS3 server.')
            return sorted_files[0][0]
        else:
            log_and_update_db(deployment_status='Failed', deployment_step='Image Verification',
                              log_message=f'{image} not found on GNS3 server.')
            raise Exception(f'{image} not found on GNS3 Server')

    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None

def gns3_update_nodes(gns3_server_data, project_id, node_id, request_data):
    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, deployment_type, deployment_status, deployment_step = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Server Name'], server_record['Project Name'], server_record['Deployment Type'], server_record['Deployment Status'], server_record['Deployment Step']
        request_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}"
        node_name = gns3_query_find_nodes_by_field(server_ip, server_port, project_id, 'node_id', 'name', node_id)
        request_response = make_request("PUT", request_url, data=request_data)
        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Updated deploy data for node {node_name[0]}")


def gns3_start_node(gns3_server_data, project_id, node_id):
    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, deployment_type, deployment_status, deployment_step = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Server Name'], server_record['Project Name'], server_record['Deployment Type'], server_record['Deployment Status'], server_record['Deployment Step']
        template_data = {}
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}/start"
        node_response = make_request("POST", node_url, data=template_data)


def gns3_stop_node(gns3_server_data, project_id, node_id):
    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, deployment_type, deployment_status, deployment_step = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Server Name'], server_record['Project Name'], server_record['Deployment Type'], server_record['Deployment Status'], server_record['Deployment Step']
        template_data = {}
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}/stop"
        node_response = make_request("POST", node_url, data=template_data)


def gns3_start_all_nodes(gns3_server_data, project_id):
    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, deployment_type, deployment_status, deployment_step = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Server Name'], server_record['Project Name'], server_record['Deployment Type'], server_record['Deployment Status'], server_record['Deployment Step']
        template_data = {}
        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting all nodes in project {project_name}")
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/start"
        node_response = make_request("POST", node_url, data=template_data)
        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Started all nodes in project {project_name}")

def gns3_stop_all_nodes(gns3_server_data, project_id):
    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, deployment_type, deployment_status, deployment_step = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Server Name'], server_record['Project Name'], server_record['Deployment Type'], server_record['Deployment Status'], server_record['Deployment Step']
        template_data = {}
        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Stopping all nodes in project {project_name}")
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/stop"
        node_response = make_request("POST", node_url, data=template_data)
        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Stopping all nodes in project {project_name}")

def gns3_set_project(gns3_server_data, project_id):
    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, deployment_type, deployment_status, deployment_step, vedge_count = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Server Name'], server_record['Project Name'], server_record['Deployment Type'], server_record['Deployment Status'], server_record['Deployment Step'], server_record['Site Count']
        if vedge_count is None:
            project_zoom = 80
            project_scene_height = 1000
            project_scene_width = 2000
        elif vedge_count <= 30:
            project_zoom = 57
            project_scene_height = 1000
            project_scene_width = 2000
        else:
            project_zoom = 30
            project_scene_height = 1500
            project_scene_width = 4200
        template_data = {"auto_close": False, "scene_height": project_scene_height,
                         "scene_width": project_scene_width,
                         "zoom": project_zoom}
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}"
        node_response = make_request("PUT", node_url, data=template_data)
        project_id = node_response["project_id"]
        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Update project settings for {project_name}")
        return project_id


def gns3_actions_upload_images(gns3_server_data):
    for root, dirs, files in os.walk("images/"):
        for file_name in files:
            image_type = os.path.basename(root)
            gns3_upload_image(gns3_server_data, image_type, file_name)

# endregion

# region Previous API
def gns3_export_project(server, port, project_id):
    url = f"http://{server}:{port}/v2/projects/{project_id}/export"
    response = requests.get(url)
    print(response)
    if not response.ok:
        print(f"Error retrieving links: {response.status_code}")
        exit()
    try:
        projects = response.json()
    except ValueError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Response content: {response.content}")
        exit()

def gns3_set_single_packet_filter(server, port, project_id, link_id, filter_type=None, filter_value=None):
    # Get available packet filter types
    url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link_id}/available_filters"
    response = requests.get(url)
    available_filters = [f["type"] for f in response.json()]

    # Select the filter type
    if filter_type is None:
        print("Available packet filter types:")
        for i, filter_type in enumerate(available_filters):
            print(f"{i + 1}. {filter_type}")
        selected_filter_type = input("Enter the number of the packet filter type you want to set: ")
        while not selected_filter_type.isdigit() or int(selected_filter_type) < 1 or int(selected_filter_type) > len(
                available_filters):
            print("Invalid selection.")
            selected_filter_type = input("Enter the number of the packet filter type you want to set: ")
        selected_filter_type = available_filters[int(selected_filter_type) - 1]
    else:
        if filter_type not in available_filters:
            print(f"Filter type {filter_type} is not available for this link.")
            return None, None
        selected_filter_type = filter_type

    # Enter the filter value
    if filter_value is None:
        selected_filter_value = input(f"Enter the value for the '{selected_filter_type}' packet filter: ")
        while not selected_filter_value.isdigit():
            print("Invalid input. Please enter a numerical value.")
            selected_filter_value = input(f"Enter the value for the '{selected_filter_type}' packet filter: ")
    else:
        selected_filter_value = filter_value

    # Construct the payload for the PUT request
    payload = {
        "filters": {
            selected_filter_type: [int(selected_filter_value)]
        }
    }

    # Submit the PUT request
    url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link_id}"
    response = requests.put(url, json=payload)

    # Check the response status code and print a message if successful
    if response.status_code == 200 or response.status_code == 201:
        # print(f"\nFilter {selected_filter_type} has been successfully added.")
        return selected_filter_type, selected_filter_value
    elif response.status_code == 400:
        print("\nThe request could not be processed. Check your request parameters and try again.")
        return None, None
    elif response.status_code == 404:
        print("\nThe specified link or project was not found. Check the link and project IDs and try again.")
        return None, None
    else:
        print(f"\nAn unexpected error occurred: {response.status_code}")
        return None, None

def gns3_set_single_packet_filter_simple(server, port, project_id, link_id, filter_type, filter_value):
    selected_filter_type = filter_type
    selected_filter_value = filter_value

    payload = {
        "filters": {
            selected_filter_type: [int(selected_filter_value)]
        }
    }
    # Submit the PUT request
    url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link_id}"
    response = requests.put(url, json=payload)

def gns3_remove_single_packet_filter(server, port, project_id, link_id):
    # Remove all filters
    payload = {"filters": {}}

    # Submit the PUT request
    url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link_id}"
    response = requests.put(url, json=payload)

    # Parse the output of the response for the filters
    output = response.json()

    # Check the response status code and print a message if successful
    if response.status_code == 200 or response.status_code == 201:
        # print("\nAll packet filters have been successfully removed.")
        return
    elif response.status_code == 400:
        print("\nThe request could not be processed. Check your request parameters and try again.")
        return
    elif response.status_code == 404:
        print("\nThe specified link or project was not found. Check the link and project IDs and try again.")
        return
    else:
        print(f"\nAn unexpected error occurred: {response.status_code}")
        return

def gns3_set_suspend_old(server, port, project_id, link_id):
    # Get the current state of the link
    url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link_id}"
    response = requests.get(url)
    link_data = response.json()
    # Check if the "suspend" key exists in the link_data dictionary
    if "suspend" in link_data:
        current_suspend = link_data["suspend"]
        if current_suspend:
            selected_suspend = False
        else:
            selected_suspend = True
    else:
        selected_suspend = False
    # Update the state of the link
    url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link_id}"
    data = {"suspend": selected_suspend}
    response = requests.put(url, json=data)
    if response.ok:
        if selected_suspend:
            print("Link suspended.")
        else:
            print("Link enabled.")
    else:
        print("Error updating link state.")

def gns3_set_suspend(server, port, project_id, link_id):
    # Get the current state of the link
    url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link_id}"
    response = requests.get(url)

    if not response.ok:
        print("Error retrieving link state.")
        return

    link_data = response.json()

    # Check if the link is currently active (not suspended)
    if "suspend" in link_data and not link_data ["suspend"]:
        # The link is active; proceed to suspend it
        data = {"suspend": True}
        response = requests.put(url, json=data)
        if response.ok:
            print("Link suspended.")
        else:
            print("Error suspending link.")
    else:
        # The link is either already suspended or the "suspend" key does not exist
        print("Link is already suspended or cannot be suspended.")


def gns3_reset_single_suspend(server, port, project_id, link_id):
    # Get the current state of the link
    url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link_id}"
    response = requests.get(url)
    link_data = response.json()
    # Check if the "suspend" key exists in the link_data dictionary
    if "suspend" in link_data:
        current_suspend = link_data["suspend"]
        if current_suspend:
            selected_suspend = False
        else:
            selected_suspend = True
    else:
        selected_suspend = False
    # Set the suspend value to False
    selected_suspend = False
    # Update the state of the link
    url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link_id}"
    data = {"suspend": selected_suspend}
    response = requests.put(url, json=data)
    if response.ok:
        if selected_suspend:
            print("Link suspended.")
        else:
            print("Link enabled.")
    else:
        print("Error updating link state.")

def gns3_reset_all_packet_filters(server, port, project_id):
    # Get links in the project
    links_url = f"http://{server}:{port}/v2/projects/{project_id}/links"
    response = requests.get(links_url)
    links = response.json()
    for link in links:
        # Get available packet filter types
        available_filters_url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link['link_id']}/available_filters"
        response = requests.get(available_filters_url)
        available_filters = [f["type"] for f in response.json()]
        payload = {"filters": {filter_type: [0] for filter_type in available_filters}}
        # Submit the PUT request
        url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link['link_id']}"
        response = requests.put(url, json=payload)
    # Check the response status code and print a message if successful
    if response.status_code == 200 or response.status_code == 201:
        print("\nAll packet filters have been successfully removed.")
    elif response.status_code == 400:
        print("\nThe request could not be processed. Check your request parameters and try again.")
    elif response.status_code == 404:
        print("\nThe specified link or project was not found. Check the link and project IDs and try again.")
    else:
        print(f"\nAn unexpected error occurred: {response.status_code}")
        return

def gns3_reset_all_link_states(server, port, project_id):
    # Get links in the project
    links_url = f"http://{server}:{port}/v2/projects/{project_id}/links"
    response = requests.get(links_url)
    links = response.json()
    print(f"http://{server}:{port}/v2/projects/{project_id}/links")
    for link in links:
        payload = {"suspend": False}
        # Submit the PUT request
        url = f"http://{server}:{port}/v2/projects/{project_id}/links/{link['link_id']}"
        response = requests.put(url, json=payload)
    if response.status_code not in (200, 201):
        print(f"\nError: failed to update 'suspend' value for all links (status code {response.status_code})")
    else:
        print(f"\nAll links have been resumed")

def gns3_reset_lab_client_states(server, port, project_id):
    gns3_reset_all_link_states(server, port, project_id)
    gns3_reset_all_packet_filters(server, port, project_id)
    nodes = gns3_query_get_nodes(server, port, project_id)
    client_nodes = gns3_query_find_nodes_by_name(nodes, 'Network-Test-Client')
    for client_node in client_nodes:
        client_node_id = client_node[0]
        gns3_change_node_state(server, port, project_id, client_node_id, 'off')
    return True

def gns3_restart_node(server, port, project_id, node_id):
    url = f"http://{server}:{port}/v2/projects/{project_id}/nodes/{node_id}/stop"
    response = requests.post(url)
    if response.status_code != 200:
        print("Error stopping node:", response.text)
        return False
    url = f"http://{server}:{port}/v2/projects/{project_id}/nodes/{node_id}/start"
    response = requests.post(url)
    if response.status_code != 200:
        print("Error starting node:", response.text)
        return False
    return True

def gns3_change_node_state(server, port, project_id, node_id, state):
    if state == "on":
        url = f"http://{server}:{port}/v2/projects/{project_id}/nodes/{node_id}/start"
    elif state == "off":
        url = f"http://{server}:{port}/v2/projects/{project_id}/nodes/{node_id}/stop"
    else:
        print("Invalid state. Please use 'on' or 'off'.")
        return False
    response = requests.post(url)
    if response.status_code != 200:
        print(f"Error changing node state to {state}:", response.text)
        return False
    return True

def is_node_responsive(host, port):
    try:
        tn = telnetlib.Telnet()
        tn.open(host, port, timeout=2)
        tn.write(b'\x03')
        time.sleep(1)  # Add a delay before reading the response
        if tn.sock_avail():
            response = tn.read_until(b"\n", timeout=2)
            #tn.close()
            if response == b'':
                raise socket.timeout("Timeout waiting for response")
            return True
        else:
            raise socket.timeout("No response received")
    except (socket.timeout, socket.error) as e:
        #print(f"Error connecting to node: {e}")
        return False

def gns3_run_telnet_command(server, port, project_id, node_id, console, state, command=None):
    if not is_node_responsive(server, console):
        gns3_restart_node(server, port, project_id, node_id)
    tn = telnetlib.Telnet(server, console, timeout=1)
    if state == "on":
        tn.write(command.encode('utf-8') + b'\n')
        output = tn.read_until(b'\n', timeout=2).decode('utf-8').strip()
    elif state == "off":
        tn.write(b'\x03')
        output = tn.read_until(b'\n', timeout=2).decode('utf-8').strip()
    else:
        print("Invalid state value")
        return None
# endregion
