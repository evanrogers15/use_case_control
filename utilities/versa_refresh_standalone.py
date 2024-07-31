import telnetlib
import time
from datetime import datetime
import requests
import json
import re
import logging

def query_find_nodes_by_field(server_ip, server_port, project_id, search_field, return_field, search_string):
    nodes = gns3_query_get_nodes(server_ip, server_port, project_id)
    if search_string:
        matching_nodes = [node for node in nodes if search_string in node[search_field]]
        if not matching_nodes:
            return []
        else:
            if return_field == "node_id":
                return matching_nodes[0][return_field]
            else:
                return [node[return_field] for node in matching_nodes]
    else:
        return []

def get_node_coordinates(gns3_server_ip, port, project_id, node_id):
    # Build the URL for the GNS3 API endpoint
    url = f"http://{gns3_server_ip}:{port}/v2/projects/{project_id}/nodes/{node_id}"

    # Make the request to the GNS3 server
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code != 200:
        raise Exception(f"Error querying GNS3 server: {response.text}")

    # Parse the JSON response
    data = response.json()

    # Extract and return the coordinates
    x = data.get('x', None)
    y = data.get('y', None)
    return x, y

def update_node_coordinates(gns3_server_ip, port, project_id, node_id, x, y):
    # Build the URL for the GNS3 API endpoint
    url = f"http://{gns3_server_ip}:{port}/v2/projects/{project_id}/nodes/{node_id}"

    # Prepare the data to update
    payload = {
        "x": x,
        "y": y
    }

    # Make the request to the GNS3 server to update the node coordinates
    response = requests.put(url, json=payload)

    # Check if the request was successful
    if response.status_code not in (200, 204):  # 200 for OK, 204 for No Content (both indicate success)
        raise Exception(f"Error updating coordinates on GNS3 server: {response.text}")

    return response.json()

def delete_node(gns3_server_data, project_id, node_id):
    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, deployment_type, deployment_status, deployment_step = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Server Name'], server_record['Project Name'], server_record['Deployment Type'], server_record['Deployment Status'], server_record['Deployment Step']
        delete_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}"
        response = make_request("DELETE", delete_url)

# region Imported functions

def log_and_update_db(server_name=None, project_name=None, deployment_type=None, deployment_status=None, deployment_step=None, log_message=None):
    # Log the message using logging.info
    logging.info(log_message)

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

def gns3_query_get_project_id(server_ip, server_port, project_name):
    url = f"http://{server_ip}:{server_port}/v2/projects"
    response = requests.get(url)
    projects = json.loads(response.text)
    for project in projects:
        if project['name'] == project_name:
            return project['project_id']
    return None

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

def gns3_query_get_template_id(server_ip, server_port, template_name):
    url = f"http://{server_ip}:{server_port}/v2/templates"
    response = requests.get(url)
    templates = json.loads(response.text)
    for template in templates:
        if template['name'] == template_name:
            return template['template_id']
    return None

def gns3_start_node(gns3_server_data, project_id, node_id):
    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, deployment_type, deployment_status, deployment_step = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Server Name'], server_record['Project Name'], server_record['Deployment Type'], server_record['Deployment Status'], server_record['Deployment Step']
        template_data = {}
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}/start"
        node_response = make_request("POST", node_url, data=template_data)

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

def gns3_update_nodes(gns3_server_data, project_id, node_id, request_data):
    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, deployment_type, deployment_status, deployment_step = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Server Name'], server_record['Project Name'], server_record['Deployment Type'], server_record['Deployment Status'], server_record['Deployment Step']
        request_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}"
        node_name = gns3_query_find_nodes_by_field(server_ip, server_port, project_id, 'node_id', 'name', node_id)
        request_response = make_request("PUT", request_url, data=request_data)
        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Updated deploy data for node {node_name[0]}")

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

# endregion

# region Variables

versa_director_template_name = 'Versa Director 21.2.3'
versa_director_template_data = {"compute_id": "local", "cpus": 16, "adapters": 6,
                                 "symbol": ":/symbols/affinity/circle/blue/server_cluster.svg",
                                 "adapter_type": "virtio-net-pci", "qemu_path": "/usr/bin/qemu-system-x86_64",
                                 "hda_disk_image": "versa-director-c19c43c-21.2.3.qcow2",
                                 "name": versa_director_template_name, "ram": 16384,
                                 "template_type": "qemu", "hda_disk_interface": "virtio",
                                 "options": "-cpu host -smp 2,maxcpus=2"}
versa_director_deploy_data = {"x": 5, "y": 495, "name": "Versa_Director"}
versa_director_username = 'Administrator'
versa_old_password = "versa123"
versa_analytics_username = "admin"

# endregion

def versa_refresh(server_ip, server_port, project_name, site_count, mgmt_subnet_ip):
    # region Variables
    deployment_type = 'versa'
    deployment_status = 'running'
    deployment_step = '- Action - '

    required_qemu_images = {"versa-director-c19c43c-21.2.3.qcow2"}

    start_time = time.time()
    current_date = datetime.now().strftime("%m/%d/%Y")

    mgmt_subnet_gateway_ip = mgmt_subnet_ip + ".1"
    director_mgmt_ip = mgmt_subnet_ip + ".2"
    analytics_mgmt_ip = mgmt_subnet_ip + ".6"

    southbound_subnet = '172.16.1'
    director_southbound_ip = southbound_subnet + ".2"
    analytics_southbound_ip = southbound_subnet + ".6"

    server_name = gns3_query_get_computes_name(server_ip, server_port)
    project_id = gns3_query_get_project_id(server_ip, server_port, project_name)
    
    gns3_server_data = [{
        "GNS3 Server": server_ip, "Server Name": server_name, "Server Port": server_port, "Project Name": project_name,
        "Project ID": project_id, "Site Count": site_count,
        "Deployment Type": deployment_type, "Deployment Status": deployment_status, "Deployment Step": deployment_step
    }]

    # endregion
    # region Runtime
    # region Create GNS3 Templates
    deployment_step = 'Creating Templates'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, "Starting Template Creation")
    versa_director_template_id = gns3_query_get_template_id(server_ip, server_port, versa_director_template_name)
    if versa_director_template_id is None:
        versa_director_template_id = gns3_create_template(gns3_server_data, versa_director_template_data)
    # endregion
    # region Versa Director Backup
    deployment_step = 'Director Backup'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting Director Backup")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    for server_ip in server_ips:
        temp_node_name = f'Director'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, project_id, temp_node_name)
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Logging in to console for node {temp_node_name}")
                tn = telnetlib.Telnet(server_ip, console_port)
                while True:
                    tn.write(b"\r\n")
                    output = tn.read_until(b"login:", timeout=2).decode('ascii')
                    if '[Administrator@director: ~] $' in output:
                        break
                    tn.write(versa_director_username.encode("ascii") + b"\n")
                    tn.read_until(b"Password:", timeout=5)
                    tn.write(versa_old_password.encode("ascii") + b"\n")
                    output = tn.read_until(b"Password:", timeout=5).decode('ascii')
                    if '[Administrator@director: ~] $' in output:
                        break
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                                      f"{temp_node_name} not available yet, trying again in 30 seconds")
                    time.sleep(30)
                tn.write(b"\r\n")
                tn.read_until(b"[Administrator@director: ~] $")
                tn.write(b'cli\r\n')
                tn.read_until(b"director>")
                tn.write(b'request system recovery backup\r\n')
                output = tn.read_until(b"Backup operation took").decode('ascii')
                match = re.search(r"Backup filename: (\S+)", output)
                backup_filename = match.group(1)
                tn.write(b"\r\n")
                tn.read_until(b"director>")
                tn.write(b"exit\r\n")
                tn.read_until(b"[Administrator@director: ~] $")
                scp_backup_command = f"scp /var/versa/backups/{backup_filename} admin@{analytics_mgmt_ip}:/home/admin"
                tn.write(scp_backup_command.encode('ascii') + b"\n")
                output = tn.read_until(b"?").decode('ascii')
                if "fingerprint" in output:
                    tn.write(b'yes\r\n')
                else:
                    tn.write(b"\n")
                tn.read_until(b"password:")
                tn.write(versa_old_password.encode("ascii") + b"\n")
                tn.read_until(b"[Administrator@director: ~] $")
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, "Completed Versa Director Backup")
    # endregion
    # region Deploy GNS3 Nodes
    deployment_step = 'Deploy GNS3 Nodes'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                      f"Starting Node Deployment")
    versa_director_node_id = query_find_nodes_by_field(server_ip, server_port, project_id, 'name', 'node_id', 'Versa_Director')
    versa_director_x, versa_director_y = get_node_coordinates(server_ip, server_port, project_id, versa_director_node_id)
    delete_node(gns3_server_data, project_id, versa_director_node_id)
    versa_director_node_id = gns3_create_node(gns3_server_data, project_id, versa_director_template_id, versa_director_deploy_data)
    gns3_update_nodes(gns3_server_data, project_id, versa_director_node_id, versa_director_deploy_data)
    update_node_coordinates(server_ip, server_port, project_id, versa_director_node_id, versa_director_x, versa_director_y)
    # endregion
    # region Connect GNS3 Lab Nodes
    deployment_step = 'Connect GNS3 Nodes'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting GNS3 Nodes Connect")
    mgmt_main_switch_node_id = query_find_nodes_by_field(server_ip, server_port, project_id, 'name', 'node_id', 'Versa_MGMT_Switch')
    versa_director_node_id = query_find_nodes_by_field(server_ip, server_port, project_id, 'name', 'node_id', 'Versa_Director')
    versa_control_switch_node_id = query_find_nodes_by_field(server_ip, server_port, project_id, 'name', 'node_id', 'Control_Network')

    gns3_connect_nodes(gns3_server_data, project_id, mgmt_main_switch_node_id, 0, 1, versa_director_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, project_id, versa_control_switch_node_id, 0, 5, versa_director_node_id, 1, 0)
    # endregion
    # region Start All GNS3 Nodes
    deployment_step = 'Starting Nodes'
    gns3_start_node(gns3_server_data, project_id, versa_director_node_id)
    # endregion
    # region Versa Director Setup Part 1
    deployment_step = 'Starting Nodes'
    wait_time = 2  # minutes
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Waiting {wait_time} mins for devices to come up")
    # time.sleep(wait_time * 60)
    deployment_step = 'Versa Director device Setup'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, "Starting Director device setup part 1")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    for server_ip in server_ips:
        temp_node_name = f'Director'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, project_id, temp_node_name)
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Logging in to console for node {temp_node_name}")
                tn = telnetlib.Telnet(server_ip, console_port)
                while True:
                    tn.write(b"\r\n")
                    tn.read_until(b"login:", timeout=1)
                    tn.write(versa_director_username.encode("ascii") + b"\n")
                    tn.read_until(b"Password:", timeout=5)
                    tn.write(versa_old_password.encode("ascii") + b"\n")
                    output = tn.read_until(b"Password:", timeout=5).decode('ascii')
                    if 'enter setup' in output:
                        break
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"{temp_node_name} not available yet, trying again in 30 seconds")
                    time.sleep(30)
                tn.write(b"\r\n")
                tn.read_until(b"Do you want to enter setup? (y/n)?")
                tn.write(b'y\n')
                tn.read_until(b"[sudo] password for Administrator: ")
                tn.write(versa_old_password.encode("ascii") + b"\n")
                tn.read_until(b"Do you want to setup hostname for system? (y/n)?")
                tn.write(b'y\n')
                tn.read_until(b"Enter hostname:")
                tn.write(b'director.local\n')
                tn.read_until(b"Do you want to setup network interface configuration? (y/n)?")
                tn.write(b'y\n')
                tn.read_until(b"Enter interface name [eg. eth0]:")
                tn.write(b'eth0\n')
                tn.read_until(b"Enter IP Address:")
                tn.write(director_mgmt_ip.encode('ascii') + b"\n")
                tn.read_until(b"Enter Netmask Address:")
                tn.write(b'255.255.255.0\n')
                tn.read_until(b"Configure Gateway Address? (y/n)?")
                tn.write(b'y\n')
                tn.read_until(b"Enter Gateway Address:")
                tn.write(mgmt_subnet_gateway_ip.encode('ascii') + b"\n")
                tn.read_until(b"Configure another interface? (y/n)?")
                tn.write(b'y\n')
                tn.read_until(b"Enter interface name [eg. eth0]:")
                tn.write(b'eth1\n')
                tn.read_until(b"Enter IP Address:")
                tn.write(director_southbound_ip.encode('ascii') + b"\n")
                tn.read_until(b"Enter Netmask Address:")
                tn.write(b'255.255.255.0\n')
                tn.read_until(b"Configure another interface? (y/n)?")
                tn.write(b'n\n')
                tn.read_until(b"Configure North-Bound interface (If not configured, default 0.0.0.0 will be accepted) (y/n)?")
                tn.write(b'y\n')
                tn.read_until(b"Enter interface name [eg. eth0]:")
                tn.write(b'eth0\n')
                tn.read_until(b"Enter interface name [eg. eth0]:")
                tn.write(b'eth1\n')
                tn.read_until(b"Configure another South-Bound interface? (y/n)?")
                tn.write(b'n\n')
                tn.read_until(b"Enable secure mode for Director HA ports? (y/n)?")
                tn.write(b'n\n')
                tn.read_until(b"Secure Director HA communication? (y/n)?")
                tn.write(b'n\n')
                tn.read_until(b"Prompt to set new password at first time UI login? (y/n)?")
                tn.write(b'n\n')
                tn.read_until(b"Edit list of hosts allowed to access Versa GUI? (y/n)?")
                tn.write(b'n\n')
                tn.read_until(b"Press ENTER to continue")
                tn.write(b"\r\n")
                tn.read_until(b"director login:")
                tn.write(versa_director_username.encode("ascii") + b"\n")
                tn.read_until(b"Password:")
                tn.write(versa_old_password.encode("ascii") + b"\n")
                tn.read_until(b"[Administrator@director: ~] $")
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed Director Device Setup Part 1")
    # endregion
    # region Versa Director Restore
    deployment_step = 'Director Restore'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                      f"Starting {deployment_step}")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    for server_ip in server_ips:
        temp_node_name = f'Director'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, project_id, temp_node_name)
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                                  f"Logging in to console for node {temp_node_name}")
                tn = telnetlib.Telnet(server_ip, console_port)
                while True:
                    tn.write(b"\r\n")
                    output = tn.read_until(b"login:", timeout=2).decode('ascii')
                    if '[Administrator@director: ~] $' in output:
                        break
                    tn.write(versa_director_username.encode("ascii") + b"\n")
                    tn.read_until(b"Password:", timeout=5)
                    tn.write(versa_old_password.encode("ascii") + b"\n")
                    output = tn.read_until(b"Password:", timeout=5).decode('ascii')
                    if '[Administrator@director: ~] $' in output:
                        break
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                                      f"{temp_node_name} not available yet, trying again in 30 seconds")
                    time.sleep(30)
                tn.write(b"\r\n")
                while True:
                    tn.write(b'sudo su\r')
                    tn.read_until(b"[sudo] password for Administrator:", timeout=5)
                    tn.write(versa_old_password.encode("ascii") + b"\n")
                    output = tn.read_until(b"root@director:/home/Administrator#", timeout=5).decode('ascii')
                    if 'root@director:/home/Administrator#' in output:
                        break
                    time.sleep(5)
                scp_restore_command = f"scp admin@{analytics_mgmt_ip}:/home/admin/{backup_filename} /var/versa/backups"
                tn.write(scp_restore_command.encode("ascii") + b"\n")
                output = tn.read_until(b"?").decode('ascii')
                if "fingerprint" in output:
                    tn.write(b'yes\r\n')
                tn.read_until(b"password:")
                tn.write(versa_old_password.encode("ascii") + b"\n")
                tn.read_until(b"root@director:/home/Administrator#")
                tn.write(b'exit\r\n')
                tn.read_until(b"[Administrator@director: ~] $")
                tn.write(b'cli\r\n')
                tn.read_until(b"director>")
                restore_backup_command = f"request system recovery restore file {backup_filename}"
                tn.write(restore_backup_command.encode("ascii") + b"\n")
                tn.read_until(b"Restore operation took")
                tn.write(b"\n")
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                      f"Completed {deployment_step}")
    # endregion

    end_time = time.time()
    total_time = (end_time - start_time) / 60
    deployment_step = 'Complete'
    deployment_status = 'Complete'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Total time for Versa Refresh {total_time:.2f} minutes")
    # endregion

server_ip = "192.168.122.1"
server_port = "80"
project_name = "multivendor-sdwan"
site_count = 5
mgmt_subnet_ip = "172.16.253"


versa_refresh(server_ip, server_port, project_name, site_count, mgmt_subnet_ip)

