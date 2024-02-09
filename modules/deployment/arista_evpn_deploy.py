import telnetlib
import time
import logging.handlers

from modules.gns3.gns3_actions import *
from modules.gns3.gns3_dynamic_data import *
from modules.gns3.gns3_query import *

def arista_deploy():
    # region Runtime
    main_mgmt_switch_deploy_data = {"x": 278, "y": -141, "name": "Main_MGMT-switch"}
    evpn_cloud_node_deploy_data = {"x": 431, "y": -236, "name": "MGMT-Cloud-TAP", "node_type": "cloud",
                              "compute_id": "local", "symbol": ":/symbols/cloud.svg"}
    deployment_type = 'arista'
    deployment_status = 'running'
    deployment_step = '- Action - '

    # endregion
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # region Runtime
    start_time = time.time()
    # region GNS3 Lab Setup
    c.execute("SELECT * FROM config")
    row = c.fetchone()
    conn.close()
    if row:
        server_name = row[1]
        server_ip = row[2]
        server_port = row[3]
        project_name = row[7]
        new_project_id = row[8]
        site_count = row[9]
        tap_name = row[10]
        mgmt_subnet_ip = row[11]

    gns3_server_data = [{"GNS3 Server": server_ip, "Server Name": server_name, "Server Port": server_port,
                         "Project Name": project_name, "Project ID": new_project_id,
                         "Tap Name": tap_name,
                         "Site Count": site_count, "Deployment Type": deployment_type,
                         "Deployment Status": deployment_status, "Deployment Step": deployment_step}]
    isp_switch_count = (site_count // 40) + 1
    mgmt_switch_count = (site_count // 30) + 1
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM deployments")
    c.execute("SELECT COUNT(*) FROM deployments")
    count = c.fetchone()[0]
    if count == 0:
        # Perform initial insertion to populate the table
        c.execute(
            "INSERT INTO deployments (server_name, server_ip, project_name) VALUES (?, ?, ?)",
            (server_ip, server_name, project_name))
        conn.commit()

    gns3_actions_remove_templates(gns3_server_data)
    gns3_set_project(gns3_server_data, new_project_id)
    # endregion
    # region Deploy Nodes
    deployment_step = 'Creating Templates'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, "Starting Template Creation")
    arista_count = 7
    arista_template_id = gns3_create_template(gns3_server_data, arista_ceos_template_data)
    temp_hub_data = generate_temp_hub_data(mgmt_main_switchport_count, mgmt_main_hub_template_name)
    regular_ethernet_hub_template_id = gns3_create_template(gns3_server_data, temp_hub_data)
    network_test_tool_template_id = gns3_create_template(gns3_server_data, network_test_tool_template_data)
    deployment_step = 'Deploy GNS3 Nodes'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                      f"Starting Node Deployment")
    cloud_node_id = gns3_create_cloud_node(gns3_server_data, new_project_id, evpn_cloud_node_deploy_data)
    mgmt_main_switch_node_id = gns3_create_node(gns3_server_data, new_project_id, regular_ethernet_hub_template_id,
                                                main_mgmt_switch_deploy_data)
    for i in range(1, arista_count + 1):
        node_id, node_name = gns3_create_node_multi_return(gns3_server_data, new_project_id, arista_template_id,
                                                           arista_deploy_data[f"arista_{i:02}_deploy_data"])
        arista_deploy_data[f"arista_{i:02}_deploy_data"]["node_id"] = node_id
        gns3_update_nodes(gns3_server_data, new_project_id, node_id, arista_deploy_data[f"arista_{i:02}_deploy_data"])
    gns3_start_all_nodes(gns3_server_data, new_project_id)
    # endregion
    # region Connect Nodes
    deployment_step = 'Connect'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                      "Connect Nodes")
    matching_nodes = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'name', 'ports', 'MGMT-Cloud-TAP')
    mgmt_tap_interface = 0
    for port in matching_nodes[0]:
        if port["short_name"] == tap_name:
            mgmt_tap_interface = port['port_number']
    gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 0, cloud_node_id, 0,
                       mgmt_tap_interface)
    for i in range(1, arista_count + 1):
        gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, i + 5,
                           arista_deploy_data[f"arista_{i:02}_deploy_data"]["node_id"], 19, 0)
    for i in range(1, arista_count + 1):
        name = arista_deploy_data[f"arista_{i:02}_deploy_data"]["name"]
        node_id = arista_deploy_data[f"arista_{i:02}_deploy_data"]["node_id"]
        if name == "arista-spine1":
            for k in range(1, 6):
                gns3_connect_nodes(gns3_server_data, new_project_id, node_id, k, 0,
                                   arista_deploy_data[f"arista_{k + 2:02}_deploy_data"]["node_id"], 11, 0)
        if name == "arista-spine2":
            for k in range(1, 6):
                gns3_connect_nodes(gns3_server_data, new_project_id, node_id, k, 0,
                                   arista_deploy_data[f"arista_{k + 2:02}_deploy_data"]["node_id"], 12, 0)
        if name == "arista-leaf1":
            gns3_connect_nodes(gns3_server_data, new_project_id, node_id, 10, 0,
                               arista_deploy_data[f"arista_04_deploy_data"]["node_id"],
                               10, 0)
        if name == "arista-leaf3":
            gns3_connect_nodes(gns3_server_data, new_project_id, node_id, 10, 0,
                               arista_deploy_data[f"arista_06_deploy_data"]["node_id"],
                               10, 0)
    # endregion
    # region Create GNS3 Drawings
    deployment_step = 'Drawings'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                      "Creating Drawings")
    drawing_index = 1
    for drawing_data in arista_drawing_deploy_data:
        gns3_create_drawing(gns3_server_data, new_project_id, arista_drawing_deploy_data[f'drawing_{drawing_index:02}'])
        drawing_index += 1
    # endregion
    # region Configure
    deployment_step = 'Configure'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                      "Configuring nodes..")
    time.sleep(60)
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    for server_ip in server_ips:
        arista_nodes = f'arista-'
        client_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, arista_nodes)
        abs_path = os.path.abspath(__file__)
        configs_path = os.path.join(os.path.dirname(abs_path), '../configs/arista/lab')
        if client_nodes:
            for client_node in client_nodes:
                client_node_id, client_console_port, client_aux = client_node
                temp_node_name = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'node_id', 'name',
                                                          client_node_id)
                temp_file = temp_node_name[0]
                file_name = os.path.join(configs_path, temp_file)
                tn = telnetlib.Telnet(server_ip, client_aux)
                logging.info(f"Deploy - Starting Configuration Deploy to {temp_node_name[0]}")
                tn.write(b"\r\n")
                tn.read_until(b"#")
                tn.write(b"Cli\n")
                tn.read_until(b">")
                tn.write(b"enable\n")
                tn.read_until(b"#")
                tn.write(b"conf t\n")
                tn.read_until(b"#")
                tn.write(b"service routing protocols model multi-agent\n")
                tn.read_until(b"#")
                with open(file_name, 'r') as f:
                    lines = f.readlines()
                    logging.info(f"Deploy - Sending configuration commands to {temp_node_name[0]}")
                    for line in lines:
                        formatted_line = line.format(
                        )
                        tn.write(formatted_line.encode('ascii') + b"\n")
                        tn.read_until(b"#")
                tn.write(b"wr mem\n")
                tn.read_until(b"Copy completed successfully.")
                time.sleep(2)
                gns3_stop_node(gns3_server_data, new_project_id, client_node_id)
                gns3_start_node(gns3_server_data, new_project_id, client_node_id)

    # endregion
    # region Deploy Site Clients in Lab
    deployment_step = 'Client Deploy'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                      "Deploying Clients")
    regular_ethernet_hub_template_id = gns3_query_get_template_id(server_ip, server_port, 'Main-MGMT-Switch')
    network_test_tool_template_id = gns3_query_get_template_id(server_ip, server_port, 'Network_Test_Tool')
    v = 1
    leaf_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, "leaf")
    for i in range(1, 4):
        local_switch_deploy_data[f"switch_{i:02}_deploy_data"]["node_id"] = gns3_create_node(gns3_server_data,
                                                                                             new_project_id,
                                                                                             regular_ethernet_hub_template_id,
                                                                                             local_switch_deploy_data[
                                                                                                 f"switch_{i:02}_deploy_data"])
    if leaf_nodes:
        for leaf_node in leaf_nodes:
            node_id = leaf_node[0]
            client_node_id = gns3_create_node(gns3_server_data, new_project_id, network_test_tool_template_id,
                                              client_deploy_data[f"client_{v:02}_deploy_data"])
            gns3_update_nodes(gns3_server_data, new_project_id, client_node_id,
                              client_deploy_data[f"client_{v:02}_deploy_data"])
            temp_ip = f"172.16.101.{v + 1}"
            generate_client_interfaces_file(client_filename, temp_ip)
            gns3_upload_file_to_node(gns3_server_data, new_project_id, client_node_id, client_node_file_path,
                                     client_filename)

            if v == 1:
                local_switch_node_id = local_switch_deploy_data["switch_01_deploy_data"]["node_id"]
                gns3_connect_nodes(gns3_server_data, new_project_id, local_switch_node_id, 0, v + 5, client_node_id, 1,
                                   0)
                gns3_connect_nodes(gns3_server_data, new_project_id, node_id, 1, 0, local_switch_node_id, 0, 0)
            elif v == 2:
                gns3_connect_nodes(gns3_server_data, new_project_id, local_switch_node_id, 0, v + 5, client_node_id, 1,
                                   0)
                gns3_connect_nodes(gns3_server_data, new_project_id, node_id, 1, 0, local_switch_node_id, 0, 1)
            elif v == 3:
                local_switch_node_id = local_switch_deploy_data["switch_02_deploy_data"]["node_id"]
                gns3_connect_nodes(gns3_server_data, new_project_id, local_switch_node_id, 0, v + 5, client_node_id, 1,
                                   0)
                gns3_connect_nodes(gns3_server_data, new_project_id, node_id, 1, 0, local_switch_node_id, 0, 3)
            elif v == 4:
                gns3_connect_nodes(gns3_server_data, new_project_id, local_switch_node_id, 0, v + 5, client_node_id, 1,
                                   0)
                gns3_connect_nodes(gns3_server_data, new_project_id, node_id, 1, 0, local_switch_node_id, 0, 4)
            elif v == 5:
                local_switch_node_id = local_switch_deploy_data["switch_03_deploy_data"]["node_id"]
                gns3_connect_nodes(gns3_server_data, new_project_id, local_switch_node_id, 0, v + 5, client_node_id, 1,
                                   0)
                gns3_connect_nodes(gns3_server_data, new_project_id, node_id, 1, 0, local_switch_node_id, 0, 4)
            gns3_start_node(gns3_server_data, new_project_id, client_node_id)
            v += 1
    # endregion
    end_time = time.time()
    total_time = (end_time - start_time) / 60
    deployment_step = 'Complete'
    deployment_status = 'Complete'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                      f"Total time for GNS3 Lab Deployment for project {project_name} deployment: {total_time:.2f} minutes")
    # endregion
