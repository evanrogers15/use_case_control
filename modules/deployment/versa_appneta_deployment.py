import sys
from modules.vendor_specific_actions.versa_actions import *
from modules.gns3.gns3_dynamic_data import *
from modules.gns3.gns3_query import *
from modules.gns3.gns3_variables import *
from modules.vendor_specific_actions.appneta_actions import *

import telnetlib
import time
from datetime import datetime

def versa_appneta_deploy():
    # region Variables
    lan_subnet_address = ''
    lan_gateway_address = ''
    lan_dhcp_exclude = ''
    lan_dhcp_pool = ''
    system_ip = ''
    site_id = 0
    mgmt_address = ''
    mgmt_gateway = ''
    flexvnf_info = []
    mgmt_switch_nodes = []
    isp_switch_nodes = []
    flexvnf_lan_objects = []
    flexvnf_lan_object = []
    isp_1_overall = []
    isp_2_overall = []
    flexvnf_nodes = []
    deployment_type = 'versa'
    deployment_status = 'running'
    deployment_step = '- Action - '
    cloud_node_deploy_data = {"x": 25, "y": -554, "name": "MGMT-Cloud-TAP", "node_type": "cloud",
                              "compute_id": "local", "symbol": ":/symbols/cloud.svg"}
    required_qemu_images = {"versa-director-c19c43c-21.2.3.qcow2", "versa-analytics-67ff6c7-21.2.3.qcow2", "versa-flexvnf-67ff6c7-21.2.3.qcow2"}

    local_city_data = {}
    for key, value in template_city_data.items():
        new_key = key.replace("replace", "FlexVNF")
        local_city_data[new_key] = value
    
    # endregion
    # region Runtime
    start_time = time.time()
    current_date = datetime.now().strftime("%m/%d/%Y")

    # region GNS3 Lab Setup
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
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
        appn_url = row[12]
        appn_site_key = row[13]

    if appn_url:
        deploy_appneta = 'y'
        appn_mp_image_name = gns3_check_for_image(server_ip, server_port, 'qemu', 'pathview')
        appneta_mp_template_name = appn_mp_image_name.rstrip(".qcow2")
        required_qemu_images.add(appn_mp_image_name)
        appneta_mp_template_data = {
            "compute_id": "local", "cpus": 2, "port_name_format": "eth{0}", "adapters": 3,
            "adapter_type": "virtio-net-pci", "hda_disk_interface": "virtio",
            "qemu_path": "/usr/bin/qemu-system-x86_64", "mac_address": "52:54:00:E0:00:00",
            "custom_adapters": [{"adapter_number": 1, "mac_address": "52:54:00:E1:00:00"},
                                {"adapter_number": 2, "mac_address": "52:54:00:E2:00:00"}],
            "hda_disk_image": appn_mp_image_name, "name": appneta_mp_template_name, "ram": 4096, "template_type": "qemu"
        }
    else:
        deploy_appneta = 'n'

    mgmt_subnet_gateway_ip = mgmt_subnet_ip + ".1"
    director_mgmt_ip = mgmt_subnet_ip + ".2"
    analytics_mgmt_ip = mgmt_subnet_ip + ".6"
    controller_mgmt_ip = mgmt_subnet_ip + ".10"

    southbound_subnet = '172.16.1'
    director_southbound_gateway_ip = southbound_subnet + ".1"
    director_southbound_ip = southbound_subnet + ".2"
    analytics_southbound_gateway_ip = southbound_subnet + ".5"
    analytics_southbound_ip = southbound_subnet + ".6"
    controller_southbound_gateway_ip = southbound_subnet + ".1"
    controller_southbound_ip = southbound_subnet + ".10"

    controller_isp_subnet = '172.16.5'
    controller_isp_1_ip_gateway = controller_isp_subnet + ".1"
    controller_isp_1_ip = controller_isp_subnet + ".2"
    controller_isp_2_ip_gateway = controller_isp_subnet + ".5"
    controller_isp_2_ip = controller_isp_subnet + ".6"

    snmp_trap_dst = "172.16.102.52"

    gns3_server_data = [{"GNS3 Server": server_ip, "Server Name": server_name, "Server Port": server_port,
                         "Project Name": project_name, "Project ID": new_project_id, "Tap Name": tap_name,
                         "Site Count": site_count, "Deployment Type": deployment_type,
                         "Deployment Status": deployment_status, "Deployment Step": deployment_step}]
    info_drawing_data = {
        "drawing_01": {
            "svg": "<svg width=\"297\" height=\"307\"><rect width=\"297\" height=\"307\" fill=\"#6080b3\" fill-opacity=\"0.6399938963912413\" stroke-width=\"2\" stroke=\"#000000\" /></svg>",
            "x": -215, "y": 286, "z": 0
        }, "drawing_02": {
            "svg": "<svg width=\"224\" height=\"25\"><text font-family=\"Arial\" font-size=\"14.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">Versa Management Components</text></svg>", "x": -173, "y": 566, "z": 2
        }, "drawing_03": {
            "svg": "<svg width=\"471\" height=\"50\"><text font-family=\"Arial\" font-size=\"36.0\" fill=\"#000000\" fill-opacity=\"1.0\">Versa SDWAN Environment</text></svg>",
            "x": -1172, "y": -591, "z": 2
        }, "drawing_04": {
            "svg": f"<svg width=\"318\" height=\"50\"><text font-family=\"Arial\" font-size=\"18.0\" fill=\"#000000\" fill-opacity=\"1.0\">Management IP Range: {mgmt_subnet_ip}.0/24\nVersa Director MGMT IP: {director_mgmt_ip}\nCreated On: {current_date}</text></svg>",
            "x": -1165, "y": -541, "z": 2
        },
    }

    isp_switch_count = (site_count // 40) + 1
    mgmt_switch_count = (site_count // 30) + 1
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM deployments")
    c.execute("SELECT COUNT(*) FROM deployments")
    count = c.fetchone()[0]
    if count == 0:
        c.execute(
            "INSERT INTO deployments (server_name, server_ip, project_name) VALUES (?, ?, ?)", (server_ip, server_name, project_name))
        conn.commit()

    gns3_actions_upload_images(gns3_server_data)
    for image in required_qemu_images:
        gns3_check_for_image(server_ip, server_port, 'qemu', image)
    gns3_delete_template(gns3_server_data, versa_director_template_name)
    gns3_delete_template(gns3_server_data, versa_analytics_template_name)
    gns3_delete_template(gns3_server_data, versa_flexvnf_template_name)
    gns3_delete_template(gns3_server_data, open_vswitch_isp_template_name)
    gns3_delete_template(gns3_server_data, network_test_tool_template_name)
    gns3_delete_template(gns3_server_data, mgmt_hub_template_name)
    gns3_delete_template(gns3_server_data, mgmt_main_hub_template_name)
    gns3_set_project(gns3_server_data, new_project_id)
    if deploy_appneta == 'y':
        gns3_delete_template(gns3_server_data, appneta_mp_template_name)
    # endregion
    # region Create GNS3 Templates
    deployment_step = 'Creating Templates'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, "Starting Template Creation")
    versa_director_template_id = gns3_create_template(gns3_server_data, versa_director_template_data)
    versa_analytics_template_id = gns3_create_template(gns3_server_data, versa_analytics_template_data)
    versa_flexvnf_template_id = gns3_create_template(gns3_server_data, versa_flexvnf_template_data)
    if deploy_appneta == 'y':
        appneta_template_id = gns3_create_template(gns3_server_data, appneta_mp_template_data)
    openvswitch_isp_template_id = gns3_create_template(gns3_server_data, openvswitch_isp_template_data)
    network_test_tool_template_id = gns3_create_template(gns3_server_data, network_test_tool_template_data)
    # openvswitch_template_id = gns3_create_template(gns3_server_data, openvswitch_cloud_template_data)
    temp_hub_data = generate_temp_hub_data(mgmt_main_switchport_count, mgmt_main_hub_template_name)
    regular_ethernet_hub_template_id = gns3_create_template(gns3_server_data, temp_hub_data)
    temp_hub_data = generate_temp_hub_data(mgmt_switchport_count, mgmt_hub_template_name)
    hub_template_id = gns3_create_template(gns3_server_data, temp_hub_data)
    # endregion
    #  region Setup Dynamic Networking
    flexvnf_deploy_data, client_deploy_data, site_drawing_deploy_data = versa_generate_flexvnf_deploy_data(site_count, local_city_data)
    mgmt_switch_deploy_data = generate_mgmt_switch_deploy_data(mgmt_switch_count)
    # endregion
    # region Deploy GNS3 Nodes
    deployment_step = 'Deploy GNS3 Nodes'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting Node Deployment")
    versa_director_node_id = gns3_create_node(gns3_server_data, new_project_id, versa_director_template_id, versa_director_deploy_data)
    versa_analytics_node_id = gns3_create_node(gns3_server_data, new_project_id, versa_analytics_template_id, versa_analytics_deploy_data)
    versa_controller_node_id = gns3_create_node(gns3_server_data, new_project_id, versa_flexvnf_template_id,
                                               versa_controller_deploy_data)
    isp_ovs_node_id = gns3_create_node(gns3_server_data, new_project_id, openvswitch_isp_template_id, openvswitch_isp_deploy_data)
    mgmt_main_switch_node_id = gns3_create_node(gns3_server_data, new_project_id, regular_ethernet_hub_template_id,
                                                main_mgmt_switch_deploy_data)
    versa_control_switch_node_id = gns3_create_node(gns3_server_data, new_project_id, regular_ethernet_hub_template_id,
                                                versa_control_switch_deploy_data)
    nat_node_id = gns3_create_cloud_node(gns3_server_data, new_project_id, nat_node_deploy_data)
    cloud_node_id = gns3_create_cloud_node(gns3_server_data, new_project_id, cloud_node_deploy_data)

    for i in range(1, mgmt_switch_count + 1):
        node_name = f"MGMT_switch_{i:03}"
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, node_name)
        if not matching_nodes:
            node_id, node_name = gns3_create_node_multi_return(gns3_server_data, new_project_id, hub_template_id,
                                                               mgmt_switch_deploy_data[
                                                                   f"mgmt_switch_{i:03}_deploy_data"])
            mgmt_switch_nodes.append({'node_name': node_name, 'node_id': node_id})
        else:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Node {node_name} already exists in project {project_name}")
    for i in range(1, site_count + 1):
        node_name = f"FlexVNF-{i:03}"
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, node_name)
        if not matching_nodes:
            node_id, node_name = gns3_create_node_multi_return(gns3_server_data, new_project_id, versa_flexvnf_template_id,
                                                               flexvnf_deploy_data[f"flexvnf_{i:03}_deploy_data"])
            flexvnf_info.append({'node_name': node_name, 'node_id': node_id})
        else:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Node {node_name} already exists in project {project_name}")
    gns3_update_nodes(gns3_server_data, new_project_id, versa_director_node_id, versa_director_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, versa_analytics_node_id, versa_analytics_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, versa_controller_node_id, versa_controller_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, isp_ovs_node_id, openvswitch_isp_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, main_mgmt_switch_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, deploy_data_z)

    for i in range(1, mgmt_switch_count + 1):
        matching_node = mgmt_switch_nodes[i - 1]
        if matching_node:
            node_id = matching_node['node_id']
            gns3_update_nodes(gns3_server_data, new_project_id, node_id,
                              mgmt_switch_deploy_data[f"mgmt_switch_{i:03}_deploy_data"])
            gns3_update_nodes(gns3_server_data, new_project_id, node_id, deploy_data_z)
        else:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"No nodes found in project {project_name} for MGMT_switch_{i}")

    for i in range(1, site_count + 1):
        matching_node = flexvnf_info[i - 1]
        if matching_node:
            node_id = matching_node['node_id']
            gns3_update_nodes(gns3_server_data, new_project_id, node_id, flexvnf_deploy_data[f"flexvnf_{i:03}_deploy_data"])
        else:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"No nodes found in project {project_name} for FlexVNF {i}")
    # endregion
    # region Connect GNS3 Lab Nodes
    deployment_step = 'Connect GNS3 Nodes'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting GNS3 Nodes Connect")
    matching_nodes = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'name', 'ports', 'MGMT-Cloud-TAP')
    mgmt_tap_interface = 0
    for port in matching_nodes[0]:
        if port["short_name"] == tap_name:
            mgmt_tap_interface = port['port_number']
    gns3_connect_nodes(gns3_server_data, new_project_id, nat_node_id, 0, 0, isp_ovs_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, isp_ovs_node_id, 1, 0, versa_controller_node_id, 3, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, isp_ovs_node_id, 2, 0, versa_controller_node_id, 4, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, cloud_node_id, 0, mgmt_tap_interface,
                           mgmt_main_switch_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 1, versa_director_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 2, versa_analytics_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 3, versa_controller_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, versa_control_switch_node_id, 0, 0, versa_director_node_id, 1, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, versa_control_switch_node_id, 0, 1, versa_analytics_node_id, 1, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, versa_control_switch_node_id, 0, 2, versa_controller_node_id, 2, 0)
    mgmt_switch_interface = 1
    switch_adapter_a = 5
    switch_adapter_b = (switchport_count // 2) + 4
    mgmt_switch_node_index = 0
    for i in range(mgmt_switch_count):
        first_flexvnf_index = i * 30
        last_flexvnf_index = min((i + 1) * 30, site_count)
        mgmt_switch_node_id = mgmt_switch_nodes[mgmt_switch_node_index]['node_id']
        mgmt_switch_index = i + 5
        gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_switch_node_id, 0, 0, mgmt_main_switch_node_id, 0,
                           mgmt_switch_index)
        for j in range(first_flexvnf_index, last_flexvnf_index):
            flexvnf_node_id = flexvnf_info[j]['node_id']
            gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_switch_node_id, 0, mgmt_switch_interface,
                               flexvnf_node_id, 0, 0)
            gns3_connect_nodes(gns3_server_data, new_project_id, isp_ovs_node_id, switch_adapter_a, 0, flexvnf_node_id,
                               1, 0)
            gns3_connect_nodes(gns3_server_data, new_project_id, isp_ovs_node_id, switch_adapter_b, 0, flexvnf_node_id,
                               2, 0)
            switch_adapter_a += 1
            switch_adapter_b += 1
            mgmt_switch_interface += 1
            if (j + 1) % 44 == 0:
                switch_adapter_a = 5
                switch_adapter_b = (switchport_count // 2) + 4
                mgmt_switch_interface = 1
        mgmt_switch_node_index += 1
    # endregion
    # region Create GNS3 Drawings
    gns3_create_drawing(gns3_server_data, new_project_id, big_block_deploy_data)
    for i in range(1, site_count + 1):
        gns3_create_drawing(gns3_server_data, new_project_id,
                            site_drawing_deploy_data[f"site_drawing_{i:03}_deploy_data"])
    drawing_index = 1
    for drawing_data in info_drawing_data:
        gns3_create_drawing(gns3_server_data, new_project_id, info_drawing_data[f'drawing_{drawing_index:02}'])
        drawing_index += 1
    # endregion
    # region Deploy GNS3 Node Config Files
    deployment_step = 'Node Configs'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting Node Config Creation")
    matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, "Cloud_ISP")
    starting_subnet = 6
    router_ip = 0
    switch_index = 0
    flexvnf_index = 1
    if matching_nodes:
        for matching_node in matching_nodes:
            node_id = matching_node[0]
            flexvnf_isp_1_base_subnet = f'172.16.{starting_subnet}.0/24'
            flexvnf_isp_2_base_subnet = f'172.16.{starting_subnet + 1}.0/24'
            temp_file_name = f'cloud_isp_switch_{switch_index}_interfaces'
            isp_switch_1_objects = generate_versa_network_objects(flexvnf_isp_1_base_subnet, 30, flexvnf_index)
            isp_switch_2_objects = generate_versa_network_objects(flexvnf_isp_2_base_subnet, 30, flexvnf_index)
            isp_1_overall.append(isp_switch_1_objects)
            isp_2_overall.append(isp_switch_2_objects)
            starting_subnet += 2
            switch_index += 1
            generate_interfaces_file('flexvnf', isp_switch_1_objects, isp_switch_2_objects, temp_file_name, controller_isp_1_ip_gateway, controller_isp_2_ip_gateway)
            router_ip += 1
            gns3_upload_file_to_node(gns3_server_data, new_project_id, node_id, "etc/network/interfaces", temp_file_name)
            flexvnf_index += 44
    # endregion
    # region Start All GNS3 Nodes
    deployment_step = 'Starting Nodes'
    gns3_start_all_nodes(gns3_server_data, new_project_id)
    # endregion
    # region Deploy Site Clients in Lab
    deployment_step = 'Deploy Site Clients'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                      f"Deploying clients into each site.")
    network_test_tool_template_id = gns3_query_get_template_id(server_ip, server_port, 'Network_Test_Tool')
    client_filename = 'client_interfaces'
    client_node_file_path = 'etc/network/interfaces'
    generate_client_interfaces_file(client_filename)
    flexvnf_deploy_data, client_deploy_data, site_drawing_deploy_data = versa_generate_flexvnf_deploy_data(site_count, local_city_data)
    v = 1
    flexvnf_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, "FlexVNF")
    if flexvnf_nodes:
        for flexvnf_node in flexvnf_nodes:
            temp_file_name = "client_interfaces"
            node_id = flexvnf_node[0]
            mgmt_network_adapter_index = v + 10
            appneta_temp_name = f"Site-{v:03}-AppNeta-vk35-"
            if v == 3 and deploy_appneta == 'y':
                network_test_node_id = gns3_create_node(gns3_server_data, new_project_id, appneta_template_id,
                                                        client_deploy_data[f"network_test_client_{v:03}_deploy_data"])
                appneta_node_name = appneta_temp_name + network_test_node_id[-4:]
                gns3_update_nodes(gns3_server_data, new_project_id, network_test_node_id,
                                  {"name": appneta_node_name})
                gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, mgmt_network_adapter_index, network_test_node_id, 2, 0)
                gns3_connect_nodes(gns3_server_data, new_project_id, node_id, 3, 0, network_test_node_id, 0, 0)
                gns3_start_node(gns3_server_data, new_project_id, network_test_node_id)
            elif v == 4 and deploy_appneta == 'y':
                network_test_node_id = gns3_create_node(gns3_server_data, new_project_id, appneta_template_id,
                                                        client_deploy_data[f"network_test_client_{v:03}_deploy_data"])
                appneta_node_name = appneta_temp_name + network_test_node_id[-4:]
                gns3_update_nodes(gns3_server_data, new_project_id, network_test_node_id,
                                  {"name": appneta_node_name})
                gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, mgmt_network_adapter_index,
                                   network_test_node_id, 2, 0)
                gns3_connect_nodes(gns3_server_data, new_project_id, node_id, 3, 0, network_test_node_id, 0, 0)
                gns3_start_node(gns3_server_data, new_project_id, network_test_node_id)
            else:
                network_test_node_id = gns3_create_node(gns3_server_data, new_project_id, network_test_tool_template_id,
                                                        client_deploy_data[f"network_test_client_{v:03}_deploy_data"])
                gns3_update_nodes(gns3_server_data, new_project_id, network_test_node_id,
                                  client_deploy_data[f"network_test_client_{v:03}_deploy_data"])
                gns3_upload_file_to_node(gns3_server_data, new_project_id, network_test_node_id, client_node_file_path,
                                         temp_file_name)
                gns3_connect_nodes(gns3_server_data, new_project_id, node_id, 3, 0, network_test_node_id, 0, 0)
            if v == 2:
                gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 10, network_test_node_id, 1, 0)
            v += 1
    # endregion
    # region Versa Director Setup Part 1
    deployment_step = 'Starting Nodes'
    wait_time = 2  # minutes
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Waiting {wait_time} mins for devices to come up, to resume at {util_resume_time(wait_time)}")
    time.sleep(wait_time * 60)
    deployment_step = 'Versa Director device Setup'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, "Starting Director device setup part 1")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    for server_ip in server_ips:
        temp_node_name = f'Director'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
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
    # region Versa Analytics Device Setup
    deployment_step = 'Versa Analytics Setup'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting Versa Analytics Device Setup")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    versa_interfaces = f"""auto eth0
    iface eth0 inet static
    address {analytics_mgmt_ip}
    netmask 255.255.255.0
    gateway {mgmt_subnet_gateway_ip}
    up echo nameserver 192.168.122.1 > /etc/resolv.conf
    auto eth1
    iface eth1 inet static
    address {analytics_southbound_ip}
    netmask 255.255.255.0
    """
    for server_ip in server_ips:
        temp_node_name = f'Analytics'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
        analytics_temp_route_command = f'route add -net 10.10.0.0/16 gw {controller_southbound_ip} dev eth1'
        analytics_persistent_route_command = f"sudo sed -i '/^exit 0/i route add -net 10.10.0.0/16 gw {controller_southbound_ip} dev eth1' /etc/rc.local\n"
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                node_name = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'node_id', 'name', node_id)
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Logging in to console for node {node_name[0]}")
                tn = telnetlib.Telnet(server_ip, console_port)
                while True:
                    tn.write(b"\r\n")
                    tn.read_until(b"login:", timeout=1)
                    tn.write(versa_analytics_username.encode("ascii") + b"\n")
                    tn.read_until(b"Password:", timeout=5)
                    tn.write(versa_old_password.encode("ascii") + b"\n")
                    output = tn.read_until(b"Password:", timeout=5).decode('ascii')
                    if 'admin@versa-analytics:~$' in output:
                        break
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                                      f"{temp_node_name} not available yet, trying again in 30 seconds")
                    time.sleep(30)
                tn.write(b"\r\n")
                tn.read_until(b"admin@versa-analytics:~$")
                tn.write(b'sudo su\r\n')
                tn.read_until(b"[sudo] password for admin:")
                tn.write(versa_old_password.encode("ascii") + b"\n")
                tn.read_until(b"[root@versa-analytics: admin]#")
                command = f"echo \"{versa_interfaces}\" > /etc/network/interfaces\n"
                tn.write(command.encode('utf-8'))
                tn.read_until(b"[root@versa-analytics: admin]#")
                tn.write(b"ifdown eth0 && ifup eth0 && ifup eth1\n")
                tn.read_until(b"[root@versa-analytics: admin]#")
                tn.write(analytics_temp_route_command.encode('ascii') + b"\n")
                tn.read_until(b"[root@versa-analytics: admin]#")
                tn.write(analytics_persistent_route_command.encode('ascii') + b"\n")
                tn.read_until(b"[root@versa-analytics: admin]#")
                tn.write(b"exit\n")
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed Versa AnalyticsDevice Setup")
    # endregion
    # region Versa Controller Setup
    deployment_step = 'Versa Controller Device Setup'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting Versa Controller Device Setup")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    versa_interfaces = f"""auto eth0
            iface eth0 inet static
            address {controller_mgmt_ip}
            netmask 255.255.255.0
            gateway {mgmt_subnet_gateway_ip}
            up echo nameserver 192.168.122.1 > /etc/resolv.conf
            """
    for server_ip in server_ips:
        temp_node_name = f'Controller'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                node_name = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'node_id', 'name',
                                                           node_id)
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                                  f"Logging in to console for node {node_name[0]}")
                tn = telnetlib.Telnet(server_ip, console_port)
                while True:
                    tn.write(b"\r\n")
                    tn.read_until(b"login:", timeout=1)
                    tn.write(versa_analytics_username.encode("ascii") + b"\n")
                    tn.read_until(b"Password:", timeout=5)
                    tn.write(versa_old_password.encode("ascii") + b"\n")
                    output = tn.read_until(b"Password:", timeout=5).decode('ascii')
                    if 'admin@versa-flexvnf: ~] $' in output:
                        break
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                                      f"{temp_node_name} not available yet, trying again in 30 seconds")
                    time.sleep(30)
                tn.write(b"\r\n")
                tn.read_until(b"admin@versa-flexvnf: ~] $")
                tn.write(b'sudo su\r\n')
                tn.read_until(b"[sudo] password for admin:")
                tn.write(versa_old_password.encode("ascii") + b"\n")
                tn.read_until(b"[root@versa-flexvnf: admin]#")
                command = f"echo \"{versa_interfaces}\" > /etc/network/interfaces\n"
                tn.write(command.encode('utf-8'))
                tn.read_until(b"[root@versa-flexvnf: admin]#")
                tn.write(b"ifdown eth0 && ifup eth0\n")
                tn.write(b"exit\n")
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed Versa Controller Device Setup")
    # endregion
    # region Versa Director Setup Part 2
    deployment_step = 'Director Setup Part 2'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting Director setup part 2")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), '../configs/versa')
    clustersetup_file = os.path.join(configs_path, 'clustersetup.conf')
    versa_configure_analytics_cluster(director_mgmt_ip, analytics_mgmt_ip, analytics_southbound_ip)
    for server_ip in server_ips:
        temp_node_name = f'Director'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
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
                    tn.write(versa_analytics_username.encode("ascii") + b"\n")
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
                tn.write(b'sudo su\r\n')
                tn.read_until(b"[sudo] password for Administrator:")
                tn.write(versa_old_password.encode("ascii") + b"\n")
                tn.read_until(b"root@director:/home/Administrator#")
                with open(clustersetup_file, 'r') as f:
                    file_contents = f.read()
                file_contents = file_contents.replace("versa_director_ip", director_mgmt_ip)
                file_contents = file_contents.replace("versa_analytics_ip", analytics_mgmt_ip)
                file_contents = file_contents.replace("analytics_southbound_ip", analytics_southbound_ip)
                remote_file_path = "/opt/versa/vnms/scripts/van-cluster-config/van_cluster_install/clustersetup.conf"
                command = f"echo \"{file_contents}\" > {remote_file_path}\n"
                tn.write(command.encode('utf-8'))
                tn.read_until(b"root@director:/home/Administrator#")
                tn.write(b"cd /opt/versa/vnms/scripts/van-cluster-config/van_cluster_install\r\n")
                tn.read_until(b"root@director:")
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                                  f"Starting VAN Cluster Install")
                tn.write(b"./van_cluster_installer.py --force\n")
                tn.read_until(b"VAN CLUSTER INSTALL COMPLETED")
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                                  f"Starting Post Install VAN Cluster Setup")
                tn.write(b"./van_cluster_installer.py --post-setup --gen-vd-cert\r\n")
                tn.read_until(b"VAN CLUSTER POST-SETUP PROCEDURES COMPLETED")
                time.sleep(30)
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                      f"Starting Director API Tasks")
    versa_create_provider_org(director_mgmt_ip)
    org_id = versa_get_org_uuid(director_mgmt_ip)
    versa_create_overlay_prefix(director_mgmt_ip)
    versa_create_overlay_route(director_mgmt_ip, controller_southbound_ip)
    versa_create_controller_workflow(director_mgmt_ip, controller_mgmt_ip, controller_southbound_ip, controller_isp_1_ip_gateway, controller_isp_1_ip, controller_isp_2_ip_gateway, controller_isp_2_ip)
    time.sleep(30)
    versa_create_dhcp_profile(director_mgmt_ip)
    versa_deploy_controller(director_mgmt_ip)
    time.sleep(30)
    versa_create_wan_network(director_mgmt_ip, org_id, "ISP-1")
    time.sleep(5)
    versa_create_wan_network(director_mgmt_ip, org_id, "ISP-2")
    time.sleep(5)
    versa_create_app_steering_template(director_mgmt_ip)
    time.sleep(5)
    versa_deploy_app_steering_template(director_mgmt_ip)
    time.sleep(5)
    versa_create_device_template(director_mgmt_ip)
    time.sleep(5)
    versa_deploy_device_template(director_mgmt_ip)
    time.sleep(5)
    versa_update_device_template_snmp(director_mgmt_ip, snmp_trap_dst)
    time.sleep(5)
    versa_update_device_template_oobm_interface(director_mgmt_ip)
    time.sleep(2)
    versa_update_device_template_netflow_1(director_mgmt_ip)
    time.sleep(2)
    versa_update_device_template_netflow_2(director_mgmt_ip)
    time.sleep(2)
    versa_update_device_template_netflow_3(director_mgmt_ip)
    time.sleep(2)
    versa_update_device_template_netflow_4(director_mgmt_ip)
    time.sleep(2)
    versa_update_device_template_netflow_5(director_mgmt_ip)
    time.sleep(5)
    versa_create_device_group(director_mgmt_ip)
    time.sleep(5)
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, "Completed vManage Device Setup Part 2")
    # endregion
    # region Versa FlexVNF Device Setup
    deployment_step = 'FlexVNF Device Onboarding'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting FlexVNF Device Onbaording for {site_count} FlexVNFs")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    flexvnf_lan_objects = generate_flexvnf_objects(site_count, mgmt_subnet_ip)
    isp_index = 0
    flexvnf_vr_index = 4
    for server_ip in server_ips:
        for i in range(1, site_count + 1):
            temp_node_name = f'FlexVNF-{i:003}'
            matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
            if matching_nodes:
                for matching_node in matching_nodes:
                    node_id, console_port, aux = matching_node
                    node_name = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'node_id', 'name', node_id)
                    for flexvnf_lan_object in flexvnf_lan_objects:
                        if flexvnf_lan_object['flexvnf'] == temp_node_name:
                            lan_dhcp_pool = flexvnf_lan_object['lan_dhcp_pool']
                            lan_subnet_base = flexvnf_lan_object['lan_subnet_base']
                            lan_dhcp_exclude = flexvnf_lan_object['lan_dhcp_exclude']
                            lan_gateway_address = flexvnf_lan_object['lan_gateway_address']
                            client_1_address = flexvnf_lan_object['client_1_address']
                            mgmt_address = flexvnf_lan_object['mgmt_address']
                            mgmt_gateway = flexvnf_lan_object['mgmt_gateway']
                            system_ip = flexvnf_lan_object['system_ip']
                            site_id = f"{flexvnf_lan_object['site_id']}"
                            device_serial_number = f"SN{site_id}"
                    for dictionary_0 in isp_1_overall[isp_index]:
                        if dictionary_0['flexvnf'] == temp_node_name:
                            vpn_0_ge0_0_ip_address = dictionary_0['flexvnf_address']
                            vpn_0_ge0_0_ip_gateway = dictionary_0['router_address']
                    for dictionary_1 in isp_2_overall[isp_index]:
                        if dictionary_1['flexvnf'] == temp_node_name:
                            vpn_0_ge0_1_ip_address = dictionary_1['flexvnf_address']
                            vpn_0_ge0_1_ip_gateway = dictionary_1['router_address']
                    flexvnf_hostname = f"{temp_node_name}-{local_city_data[temp_node_name]['city']}"
                    flexvnf_city = local_city_data[temp_node_name]['city']
                    site_country = local_city_data[temp_node_name]['country']
                    vr_1_route_ip = f'10.10.0.{flexvnf_vr_index}'
                    tvi_0_2_ip = f'10.10.0.{flexvnf_vr_index + 1}/32'
                    tvi_0_3_ip = f'10.10.0.{flexvnf_vr_index}/32'
                    latitude = local_city_data[temp_node_name]['latitude']
                    longitude = local_city_data[temp_node_name]['longitude']
                    onboard_command = f"sudo /opt/versa/scripts/staging.py -w 0 -n {device_serial_number} -c {controller_isp_1_ip} -s {vpn_0_ge0_0_ip_address} -g {vpn_0_ge0_0_ip_gateway} -l SDWAN-Branch@Versa-Root.com -r Controller-01-staging@Versa-Root.com"
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting FlexVNF Device Onboarding for {node_name[0]} - FlexVNF {i} of {site_count}")
                    versa_create_site_device_workflow(director_mgmt_ip, vr_1_route_ip, lan_gateway_address, lan_subnet_base, flexvnf_hostname, site_id, device_serial_number, site_country, flexvnf_city, vpn_0_ge0_0_ip_address, vpn_0_ge0_0_ip_gateway, vpn_0_ge0_1_ip_address, vpn_0_ge0_1_ip_gateway, tvi_0_2_ip, tvi_0_3_ip, latitude, longitude, mgmt_gateway, mgmt_address)
                    time.sleep(10)
                    versa_deploy_device_workflow(director_mgmt_ip, flexvnf_hostname)
                    time.sleep(10)
                    # versa_config_edge_mgmt_interface(director_mgmt_ip, flexvnf_hostname, mgmt_address, mgmt_subnet_gateway_ip)
                    time.sleep(10)
                    tn = telnetlib.Telnet(server_ip, console_port)
                    tn.write(b"\r\n")
                    while True:
                        tn.write(b"\r\n")
                        tn.read_until(b"versa-flexvnf login:", timeout=2)
                        tn.write(versa_analytics_username.encode("ascii") + b"\n")
                        tn.read_until(b"Password:", timeout=5)
                        tn.write(versa_old_password.encode("ascii") + b"\n")
                        output = tn.read_until(b"[admin@versa-flexvnf: ~] $", timeout=5).decode('ascii')
                        if '[admin@versa-flexvnf: ~] $' in output:
                            break
                        log_and_update_db(server_name, project_name, deployment_type, deployment_status,
                                          deployment_step,
                                          f"{node_name} not available yet, trying again in 30 seconds")
                        time.sleep(30)
                    tn.write(b"\r\n")
                    tn.read_until(b"[admin@versa-flexvnf: ~] $")
                    while True:
                        tn.write(b"\r\n")
                        tn.write(b'sudo su\r\n')
                        tn.read_until(b"[sudo] password for admin:", timeout=2)
                        tn.write(versa_old_password.encode("ascii") + b"\n")
                        output = tn.read_until(b"[root@versa-flexvnf: admin]#", timeout=5).decode('ascii')
                        if '[root@versa-flexvnf: admin]#' in output:
                            break
                    tn.write(onboard_command.encode('ascii') + b"\r")
                    tn.read_until(b"[root@versa-flexvnf: admin]#")
                    tn.close()
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed FlexVNF Device Onboarding for {temp_node_name}, Remaining - {site_count - i}")
                    if i % 44 == 0 and i != 0:
                        isp_index += 1
                    flexvnf_vr_index += 2
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed FlexVNF Device Onboarding for {site_count} FlexVNF devices")
    # endregion
    # region AppNeta MP Setup
    if deploy_appneta == 'y':
        deployment_step = 'AppNeta Monitoring Point Setup'
        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                          f"Starting AppNeta Monitoring Point Configuration")
        server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
        v = 1
        mp_lan_index = 3
        for server_ip in server_ips:
            temp_node_name = f'AppNeta'
            matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
            if matching_nodes:
                for matching_node in matching_nodes:
                    mp_ip_address = f"{mgmt_subnet_ip}.{v+50}"
                    mp_lan_address = f"172.16.10{mp_lan_index}.51"
                    mp_lan_gateway = f"172.16.10{mp_lan_index}.1"
                    node_id, console_port, aux = matching_node
                    node_name = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'node_id', 'name',
                                                               node_id)
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                                      f"Logging in to console for node {node_name[0]}")
                    appneta_cli_curl_commands(server_ip, server_port, server_name, new_project_id, project_name, deployment_type, node_id, console_port, node_name[0], appneta_mp_mac, mp_ip_address, appn_site_key, appn_url)
                    v += 1
                    mp_lan_index += 1

        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                          f"Completed AppNeta MP Configuration")
    # endregion

    end_time = time.time()
    total_time = (end_time - start_time) / 60
    deployment_step = 'Complete'
    deployment_status = 'Complete'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Total time for GNS3 Lab Deployment with {site_count} FlexVNF Devices: {total_time:.2f} minutes")
    # endregion

