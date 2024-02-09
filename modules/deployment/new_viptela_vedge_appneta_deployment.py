import telnetlib
import time
import re

from modules.vendor_specific_actions.viptela_actions import *
from modules.gns3.gns3_dynamic_data import *
from modules.gns3.gns3_query import *
from modules.vendor_specific_actions.appneta_actions import *

def viptela_vedge_appneta_deploy():
    # region Variables
    vmanage_headers = {}
    lan_subnet_address = ''
    lan_gateway_address = ''
    lan_dhcp_exclude = ''
    lan_dhcp_pool = ''
    system_ip = ''
    site_id = 0
    mgmt_address = ''
    mgmt_gateway = ''
    vedge_info = []
    mgmt_switch_nodes = []
    isp_switch_nodes = []
    vedge_lan_objects = []
    vedge_lan_object = []
    isp_1_overall = []
    isp_2_overall = []
    vedge_nodes = []
    vmanage_root_cert = ""
    deployment_type = 'viptela'
    deployment_status = 'running'
    deployment_step = '- Action - '
    cloud_node_deploy_data = {"x": 25, "y": -554, "name": "MGMT-Cloud-TAP", "node_type": "cloud",
                              "compute_id": "local", "symbol": ":/symbols/cloud.svg"}
    required_qemu_images = {"viptela-vmanage-li-20.10.1-genericx86-64.qcow2", "empty30G.qcow2", "viptela-smart-li-20.10.1-genericx86-64.qcow2", "viptela-edge-20.10.1-genericx86-64.qcow2"}
    deploy_appneta = 'n'

    local_city_data = {}
    for key, value in template_city_data_multivendor.items():
        new_key = key.replace("replace-", "vEdge_")
        local_city_data[new_key] = value
    # endregion
    # region Runtime
    start_time = time.time()
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
    vmanage_mgmt_ip = mgmt_subnet_ip + ".2"
    vsmart_mgmt_ip = mgmt_subnet_ip + ".6"
    vbond_mgmt_ip = mgmt_subnet_ip + ".10"

    vpn_0_subnet = '172.16.4'
    vmanage_vpn_0_gateway_ip = vpn_0_subnet + ".1"
    vmanage_vpn_0_ip = vpn_0_subnet + ".2"
    vsmart_vpn_0_gateway_ip = vpn_0_subnet + ".5"
    vsmart_vpn_0_ip = vpn_0_subnet + ".6"
    vbond_vpn_0_gateway_ip = vpn_0_subnet + ".9"
    vbond_vpn_0_ip = vpn_0_subnet + ".10"

    gns3_server_data = [{"GNS3 Server": server_ip, "Server Name": server_name, "Server Port": server_port,
                    "vManage API IP": vmanage_mgmt_ip, "Project Name": project_name, "Project ID": new_project_id,
                    "Tap Name": tap_name,
                    "Site Count": site_count, "Deployment Type": deployment_type, "Deployment Status": deployment_status, "Deployment Step": deployment_step}]
    info_drawing_data = {
        "drawing_01": {
            "svg": "<svg width=\"297\" height=\"246\"><rect width=\"297\" height=\"246\" fill=\"#6080b3\" fill-opacity=\"0.6399938963912413\" stroke-width=\"2\" stroke=\"#000000\" /></svg>",
            "x": -228, "y": 457, "z": 0},
        "drawing_02": {
            "svg": "<svg width=\"232\" height=\"25\"><text font-family=\"Arial\" font-size=\"14.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">Viptela Management Components</text></svg>",
            "x": -195, "y": 675, "z": 2},
        "drawing_03": {
            "svg": "<svg width=\"471\" height=\"50\"><text font-family=\"Arial\" font-size=\"36.0\" fill=\"#000000\" fill-opacity=\"1.0\">Viptela SDWAN Environment</text></svg>",
            "x": -1172, "y": -591, "z": 2},
        "drawing_04": {
            "svg": f"<svg width=\"318\" height=\"50\"><text font-family=\"Arial\" font-size=\"18.0\" fill=\"#000000\" fill-opacity=\"1.0\">Management IP Range: {mgmt_subnet_ip}.0/24\nViptela vManage MGMT IP: {vmanage_mgmt_ip}</text></svg>",
            "x": -1165, "y": -541, "z": 2},
    }

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
            "INSERT INTO deployments (server_name, server_ip, project_name) VALUES (?, ?, ?)", (server_ip, server_name, project_name))
        conn.commit()

    gns3_actions_upload_images(gns3_server_data)
    for image in required_qemu_images:
        gns3_check_for_image(server_ip, server_port, 'qemu', image)
    gns3_delete_template(gns3_server_data, vmanage_template_name)
    gns3_delete_template(gns3_server_data, vbond_template_name)
    gns3_delete_template(gns3_server_data, vsmart_template_name)
    gns3_delete_template(gns3_server_data, vedge_template_name)
    gns3_delete_template(gns3_server_data, network_test_tool_template_name)
    gns3_delete_template(gns3_server_data, open_vswitch_isp_template_name)
    gns3_delete_template(gns3_server_data, mgmt_hub_template_name)
    gns3_delete_template(gns3_server_data, mgmt_main_hub_template_name)
    if deploy_appneta == 'y':
        gns3_delete_template(gns3_server_data, appneta_mp_template_name)
    # gns3_set_project(gns3_server_data, new_project_id)
    # endregion
    # region Create GNS3 Templates
    deployment_step = 'Creating Templates'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, "Starting Template Creation")
    vmanage_template_id = gns3_create_template(gns3_server_data, viptela_vmanage_template_data)
    vbond_template_id = gns3_create_template(gns3_server_data, viptela_vbond_template_data)
    vsmart_template_id = gns3_create_template(gns3_server_data, viptela_vsmart_template_data)
    vedge_template_id = gns3_create_template(gns3_server_data, viptela_vedge_template_data)
    if deploy_appneta == 'y':
        appneta_template_id = gns3_create_template(gns3_server_data, appneta_mp_template_data)
    network_test_tool_template_id = gns3_create_template(gns3_server_data, network_test_tool_template_data)
    openvswitch_isp_template_id = gns3_create_template(gns3_server_data, openvswitch_isp_template_data)
    temp_hub_data = generate_temp_hub_data(mgmt_main_switchport_count, mgmt_main_hub_template_name)
    regular_ethernet_hub_template_id = gns3_create_template(gns3_server_data, temp_hub_data)
    temp_hub_data = generate_temp_hub_data(mgmt_switchport_count, mgmt_hub_template_name)
    hub_template_id = gns3_create_template(gns3_server_data, temp_hub_data)
    # endregion
    #  region Setup Dynamic Networking
    vedge_deploy_data, client_deploy_data, site_drawing_deploy_data = generate_vedge_deploy_data(site_count, local_city_data)
    mgmt_switch_deploy_data = generate_mgmt_switch_deploy_data(mgmt_switch_count)
    # endregion
    # region Deploy GNS3 Nodes
    deployment_step = 'Deploy GNS3 Nodes'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting Node Deployment")
    vmanage_node_id = gns3_create_node(gns3_server_data, new_project_id, vmanage_template_id, vmanage_deploy_data)
    vsmart_node_id = gns3_create_node(gns3_server_data, new_project_id, vsmart_template_id, vsmart_deploy_data)
    vbond_node_id = gns3_create_node(gns3_server_data, new_project_id, vbond_template_id, vbond_deploy_data)
    isp_ovs_node_id = gns3_create_node(gns3_server_data, new_project_id, openvswitch_isp_template_id, openvswitch_isp_deploy_data)
    mgmt_main_switch_node_id = gns3_create_node(gns3_server_data, new_project_id, regular_ethernet_hub_template_id,
                                                main_mgmt_switch_deploy_data)
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
        node_name = f"vEdge_{i:03}"
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, node_name)
        if not matching_nodes:
            node_id, node_name = gns3_create_node_multi_return(gns3_server_data, new_project_id, vedge_template_id,
                                                               vedge_deploy_data[f"vedge_{i:03}_deploy_data"])
            vedge_info.append({'node_name': node_name, 'node_id': node_id})
        else:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Node {node_name} already exists in project {project_name}")
    gns3_update_nodes(gns3_server_data, new_project_id, vmanage_node_id, vmanage_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, vsmart_node_id, vsmart_deploy_data)
    gns3_update_nodes(gns3_server_data, new_project_id, vbond_node_id, vbond_deploy_data)
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
        matching_node = vedge_info[i - 1]
        if matching_node:
            node_id = matching_node['node_id']
            gns3_update_nodes(gns3_server_data, new_project_id, node_id, vedge_deploy_data[f"vedge_{i:03}_deploy_data"])
        else:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"No nodes found in project {project_name} for vEdge {i}")
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
    gns3_connect_nodes(gns3_server_data, new_project_id, isp_ovs_node_id, 1, 0, vmanage_node_id, 1, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, isp_ovs_node_id, 2, 0, vsmart_node_id, 1, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, isp_ovs_node_id, 3, 0, vbond_node_id, 1, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, cloud_node_id, 0, mgmt_tap_interface,
                       mgmt_main_switch_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 1, vmanage_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 2, vsmart_node_id, 0, 0)
    gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_main_switch_node_id, 0, 3, vbond_node_id, 0, 0)
    mgmt_switch_interface = 1
    switch_adapter_a = 5
    switch_adapter_b = (switchport_count // 2) + 4
    cloud_isp_node_index = 0
    mgmt_switch_node_index = 0
    for i in range(mgmt_switch_count):
        first_vedge_index = i * 30
        last_vedge_index = min((i + 1) * 30, site_count)
        mgmt_switch_node_id = mgmt_switch_nodes[mgmt_switch_node_index]['node_id']
        mgmt_switch_index = i + 5
        gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_switch_node_id, 0, 0, mgmt_main_switch_node_id, 0,
                           mgmt_switch_index)
        for j in range(first_vedge_index, last_vedge_index):
            vedge_node_id = vedge_info[j]['node_id']
            gns3_connect_nodes(gns3_server_data, new_project_id, mgmt_switch_node_id, 0, mgmt_switch_interface,
                               vedge_node_id, 0, 0)
            gns3_connect_nodes(gns3_server_data, new_project_id, isp_ovs_node_id, switch_adapter_a, 0, vedge_node_id,
                               1, 0)
            gns3_connect_nodes(gns3_server_data, new_project_id, isp_ovs_node_id, switch_adapter_b, 0, vedge_node_id,
                               2, 0)
            switch_adapter_a += 1
            switch_adapter_b += 1
            mgmt_switch_interface += 1
            if (j + 1) % 44 == 0:
                cloud_isp_node_index += 1
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
    starting_subnet = 8
    router_ip = 0
    switch_index = 0
    vedge_index = 1
    if matching_nodes:
        for matching_node in matching_nodes:
            node_id = matching_node[0]
            # isp_router_base_subnet = '172.16.5.0/24'
            vedge_isp_1_base_subnet = f'172.16.{starting_subnet}.0/24'
            vedge_isp_2_base_subnet = f'172.16.{starting_subnet + 1}.0/24'
            temp_file_name = f'cloud_isp_switch_{switch_index}_interfaces'
            # isp_router_objects = generate_network_objects(isp_router_base_subnet, 30)
            isp_switch_1_objects = generate_edge_network_objects('vedge', vedge_isp_1_base_subnet, 30, vedge_index)
            isp_switch_2_objects = generate_edge_network_objects('vedge', vedge_isp_2_base_subnet, 30, vedge_index)
            isp_1_overall.append(isp_switch_1_objects)
            isp_2_overall.append(isp_switch_2_objects)
            starting_subnet += 2
            switch_index += 1
            generate_interfaces_file('vedge', isp_switch_1_objects, isp_switch_2_objects, temp_file_name, vmanage_vpn_0_gateway_ip, vsmart_vpn_0_gateway_ip, vbond_vpn_0_gateway_ip)
            router_ip += 1
            gns3_upload_file_to_node(gns3_server_data, new_project_id, node_id, "etc/network/interfaces",
                                     temp_file_name)
            vedge_index += 44
    # matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, "ISP-Router")
    # if matching_nodes:
    #    for matching_node in matching_nodes:
    #        temp_file_name = "ISP-Router"
    #        node_id = matching_node[0]
    #        gns3_upload_file_to_node(gns3_server_data, new_project_id, node_id, "startup-config.cfg", temp_file_name)
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
    vedge_deploy_data, client_deploy_data, site_drawing_deploy_data = generate_vedge_deploy_data(site_count, local_city_data)
    v = 1
    vedge_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, "vEdge")
    if vedge_nodes:
        for vedge_node in vedge_nodes:
            temp_file_name = "client_interfaces"
            node_id = vedge_node[0]
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
            v += 1
    # endregion
    # region Viptela vManage Setup Part 1
    deployment_step = 'vManage Setup Part 1'
    wait_time = 5  # minutes
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Waiting {wait_time} mins for devices to come up, to resume at {util_resume_time(wait_time)}")
    time.sleep(wait_time * 60)
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, "Starting vManage device setup part 1")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    for server_ip in server_ips:
        temp_node_name = f'vManage'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Logging in to console for node {temp_node_name}")
                tn = telnetlib.Telnet(server_ip, console_port)
                while True:
                    tn.write(b"\r\n")
                    tn.read_until(b"login:", timeout=1)
                    tn.write(viptela_username.encode("ascii") + b"\n")
                    tn.read_until(b"Password:", timeout=5)
                    tn.write(viptela_old_password.encode("ascii") + b"\n")
                    output = tn.read_until(b"Password:", timeout=5).decode('ascii')
                    if 'Welcome' in output:
                        break
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"{temp_node_name} not available yet, trying again in 30 seconds")
                    time.sleep(30)
                tn.write(viptela_password.encode("ascii") + b"\n")
                tn.read_until(b"password:")
                tn.write(viptela_password.encode("ascii") + b"\n")
                tn.read_until(b":")
                tn.write(b'1\n')
                tn.read_until(b"[y/n]")
                tn.write(b'y\n')
                tn.read_until(b":")
                tn.write(b'1\n')
                tn.read_until(b"):")
                tn.write(b'y\n')
                tn.read_until(b"umount")
                tn.close()
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed vManage Device Setup Part 1")
    # endregion
    # region Viptela vSmart Setup
    deployment_step = 'vSmart Setup'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting vSmart Device Setup")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), '../configs/viptela')
    file_name = os.path.join(configs_path, 'vsmart_template')
    for server_ip in server_ips:
        temp_node_name = f'vSmart'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                node_name = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'node_id', 'name', node_id)
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Logging in to console for node {node_name[0]}")
                tn = telnetlib.Telnet(server_ip, console_port)
                while True:
                    tn.write(b"\r\n")
                    output = tn.read_until(b"login:", timeout=2).decode('ascii')
                    if 'vsmart#' in output:
                        tn.write(b"\r\n")
                        break
                    tn.write(viptela_username.encode("ascii") + b"\n")
                    tn.read_until(b"Password:", timeout=2)
                    tn.write(viptela_old_password.encode("ascii") + b"\n")
                    output = tn.read_until(b"Password:", timeout=10).decode('ascii')
                    if 'Login incorrect' in output:
                        tn.read_until(b"login:", timeout=1)
                        tn.write(viptela_username.encode("ascii") + b"\n")
                        tn.read_until(b"Password:", timeout=1)
                        tn.write(viptela_password.encode("ascii") + b"\n")
                        tn.write(b"\r\n")
                        break
                    elif 'Welcome' in output:
                        tn.write(viptela_password.encode("ascii") + b"\n")
                        tn.read_until(b"password:", timeout=2)
                        tn.write(viptela_password.encode("ascii") + b"\n")
                        tn.write(b"\r\n")
                        break
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"{temp_node_name} not available yet, trying again in 30 seconds")
                    time.sleep(30)
                tn.write(b"\r\n")
                tn.read_until(b"#")
                with open(file_name, 'r') as f:
                    lines = f.readlines()
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Sending configuration commands to {node_name[0]}")
                    for line in lines:
                        formatted_line = line.format(
                            hostname=temp_node_name,
                            latitude='40.758701',
                            longitude='-111.876183',
                            system_ip=vsmart_mgmt_ip,
                            org_name=org_name,
                            vbond_address=vbond_vpn_0_ip,
                            vpn_0_eth1_ip_address=f'{vsmart_vpn_0_ip}/30',
                            vpn_0_eth1_ip_gateway=vsmart_vpn_0_gateway_ip,
                            vpn_512_eth0_ip_address=f'{vsmart_mgmt_ip}/24',
                            vpn_512_eth0_ip_gateway=mgmt_subnet_gateway_ip
                        )
                        tn.write(formatted_line.encode('ascii') + b"\n")
                        tn.read_until(b"#")
                tn.write(b"\r\n")
                tn.read_until(b"Commit complete.")
                tn.write(b"exit\r")
                tn.read_until(b"exit")
                tn.close()
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed vSmart Device Setup")
    # endregion
    # region Viptela vBond Setup
    deployment_step = 'vBond Setup'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting vBond Device Setup")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), '../configs/viptela')
    file_name = os.path.join(configs_path, 'vbond_template')
    for server_ip in server_ips:
        temp_node_name = f'vBond'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                node_name = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'node_id', 'name', node_id)
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Logging in to console for node {temp_node_name}")
                tn = telnetlib.Telnet(server_ip, console_port)
                while True:
                    tn.write(b"\r\n")
                    output = tn.read_until(b"login:", timeout=1).decode('ascii')
                    if 'vbond#' in output:
                        tn.write(b"\r\n")
                        break
                    tn.write(viptela_username.encode("ascii") + b"\n")
                    tn.read_until(b"Password:")
                    tn.write(viptela_old_password.encode("ascii") + b"\n")
                    output = tn.read_until(b"Password:", timeout=5).decode('ascii')
                    if 'Login incorrect' in output:
                        tn.read_until(b"login:", timeout=1)
                        tn.write(viptela_username.encode("ascii") + b"\n")
                        tn.read_until(b"Password:", timeout=1)
                        tn.write(viptela_password.encode("ascii") + b"\n")
                        tn.write(b"\r\n")
                        break
                    elif 'Welcome' in output:
                        tn.write(viptela_password.encode("ascii") + b"\n")
                        tn.read_until(b"password:", timeout=2)
                        tn.write(viptela_password.encode("ascii") + b"\n")
                        tn.write(b"\r\n")
                        break
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"{temp_node_name} not available yet, trying again in 30 seconds")
                    time.sleep(30)
                tn.write(b"\r\n")
                tn.read_until(b"#")
                with open(file_name, 'r') as f:
                    lines = f.readlines()
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Sending configuration commands to {temp_node_name}")
                    for line in lines:
                        formatted_line = line.format(
                            hostname=temp_node_name,
                            latitude='40.758701',
                            longitude='-111.876183',
                            system_ip=vbond_mgmt_ip,
                            org_name=org_name,
                            vbond_address=vbond_vpn_0_ip,
                            vpn_0_eth1_ip_address=f'{vbond_vpn_0_ip}/30',
                            vpn_0_eth1_ip_gateway=vbond_vpn_0_gateway_ip,
                            vpn_512_eth0_ip_address=f'{vbond_mgmt_ip}/24',
                            vpn_512_eth0_ip_gateway=mgmt_subnet_gateway_ip
                        )
                        tn.write(formatted_line.encode('ascii') + b"\n")
                        tn.read_until(b"#")
                tn.write(b"\r\n")
                tn.read_until(b"Commit complete.")
                tn.write(b"exit\r")
                tn.read_until(b"exit")
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed vBond Device Setup")
    # endregion
    # region Viptela vManage Setup Part 2
    deployment_step = 'vManage Setup Part 2'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting vManage setup part 2")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), '../configs/viptela')
    file_name = os.path.join(configs_path, 'vmanage_template')
    vdevices = [6, 10]
    for server_ip in server_ips:
        temp_node_name = f'vManage'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Logging in to console for node {temp_node_name}")
                tn = telnetlib.Telnet(server_ip, console_port)
                while True:
                    tn.write(b"\r\n")
                    output = tn.read_until(b"login:", timeout=2).decode('ascii')
                    if 'vManage#' in output:
                        break
                    elif 'vManage:~$' in output:
                        tn.write(b"exit\r\n")
                        tn.read_until(b"#")
                        break
                    tn.write(viptela_username.encode("ascii") + b"\n")
                    tn.read_until(b"Password:", timeout=1)
                    tn.write(viptela_password.encode("ascii") + b"\n")
                    output = tn.read_until(b"#", timeout=1).decode('ascii')
                    if 'vmanage#' in output:
                        break
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"{temp_node_name} not available yet, trying again in 30 seconds")
                    time.sleep(30)
                tn.write(b"\r\n")
                tn.read_until(b"#")
                with open(file_name, 'r') as f:
                    lines = f.readlines()
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Sending configuration commands to {temp_node_name}")
                    for line in lines:
                        formatted_line = line.format(
                            hostname=temp_node_name,
                            latitude='40.758701',
                            longitude='-111.876183',
                            system_ip=vmanage_mgmt_ip,
                            org_name=org_name,
                            vbond_address=vbond_vpn_0_ip,
                            vpn_0_eth1_ip_address=f'{vmanage_vpn_0_ip}/30',
                            vpn_0_eth1_ip_gateway=vmanage_vpn_0_gateway_ip,
                            vpn_512_eth0_ip_address=f'{vmanage_mgmt_ip}/24',
                            vpn_512_eth0_ip_gateway=mgmt_subnet_gateway_ip
                        )
                        tn.write(formatted_line.encode('ascii') + b"\n")
                        tn.read_until(b"#")
                tn.write(b"\r\n")
                # exit_var = tn.read_until(b"vSmart#").decode('ascii')
                # if temp_node_name not in exit_var:
                #        sys.exit()
                tn.write(b'vshell\r\n')
                tn.read_until(b'vManage:~$')
                tn.write(b'openssl genrsa -out SDWAN.key 2048\r\n')
                tn.read_until(b'vManage:~$')
                tn.write(
                    b'openssl req -x509 -new -nodes -key SDWAN.key -sha256 -days 2000 -subj "/C=US/ST=MS/O=sdwan-lab/CN=sdwan-lab" -out SDWAN.pem\r')
                tn.read_until(b'vManage:~$')
                tn.write(b'exit\r\n')
                tn.read_until(b'#')
                for vdevice in vdevices:
                    scp_command = f"request execute vpn 512 scp /home/admin/SDWAN.pem admin@{mgmt_subnet_ip}.{vdevice}:/home/admin"
                    tn.write(scp_command.encode('ascii') + b"\r")
                    test_o = tn.read_until(b"?", timeout=2).decode('ascii')
                    if "fingerprint" in test_o:
                        tn.write(b'yes\r\n')
                    else:
                        tn.write(b"\n")
                    tn.read_until(b"Password:")
                    tn.write(viptela_password.encode("ascii") + b"\n")
                    tn.read_until(b'#')
                tn.write(b'exit\r\n')
                tn.read_until(b'exit')
                tn.close()
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, "Completed vManage Device Setup Part 2")
    # endregion
    # region Viptela vEdge Device Setup
    deployment_step = 'vEdge Device Setup'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting vEdge Device Setup for {site_count} vEdges")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), '../configs/viptela')
    file_name = os.path.join(configs_path, 'vedge_cloud_site_template_no_restrict')
    vedge_lan_objects = generate_vedge_objects(site_count, f'{mgmt_subnet_ip}')
    isp_index = 0
    for server_ip in server_ips:
        for i in range(1, site_count + 1):
            temp_node_name = f'vEdge_{i:003}'
            matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
            if matching_nodes:
                for matching_node in matching_nodes:
                    node_id, console_port, aux = matching_node
                    node_name = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'node_id', 'name', node_id)
                    for vedge_lan_object in vedge_lan_objects:
                        if vedge_lan_object['vedge'] == temp_node_name:
                            lan_dhcp_pool = vedge_lan_object['lan_dhcp_pool']
                            lan_subnet_address = vedge_lan_object['lan_subnet_address']
                            lan_dhcp_exclude = vedge_lan_object['lan_dhcp_exclude']
                            lan_gateway_address = vedge_lan_object['lan_gateway_address']
                            client_1_address = vedge_lan_object['client_1_address']
                            mgmt_address = vedge_lan_object['mgmt_address']
                            mgmt_gateway = vedge_lan_object['mgmt_gateway']
                            system_ip = vedge_lan_object['system_ip']
                            site_id = vedge_lan_object['site_id']
                    for dictionary_0 in isp_1_overall[isp_index]:
                        if dictionary_0['vedge'] == temp_node_name:
                            vpn_0_ge0_0_ip_address = dictionary_0['vedge_address']
                            vpn_0_ge0_0_ip_gateway = dictionary_0['router_address']
                    for dictionary_1 in isp_2_overall[isp_index]:
                        if dictionary_1['vedge'] == temp_node_name:
                            vpn_0_ge0_1_ip_address = dictionary_1['vedge_address']
                            vpn_0_ge0_1_ip_gateway = dictionary_1['router_address']
                    vedge_hostname = f"{temp_node_name}_{local_city_data[temp_node_name]['city']}"
                    if i == 3:
                        client_1_mac_address = "52:54:00:E0:00:00"
                    elif i == 4:
                        client_1_mac_address = "52:54:00:E0:00:00"
                    else:
                        client_1_mac_address = "4C:D7:17:00:00:00"
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting vEdge Device Setup for {node_name[0]} - vEdge {i} of {site_count}")
                    tn = telnetlib.Telnet(server_ip, console_port)
                    while True:
                        tn.write(b"\r\n")
                        output = tn.read_until(b"login:", timeout=1).decode('ascii')
                        if 'vedge#' in output:
                            tn.write(b"\r\n")
                            break
                        tn.write(viptela_username.encode("ascii") + b"\n")
                        tn.read_until(b"Password:")
                        tn.write(viptela_old_password.encode("ascii") + b"\n")
                        output = tn.read_until(b"Password:", timeout=5).decode('ascii')
                        if 'Login incorrect' in output:
                            tn.read_until(b"login:", timeout=1)
                            tn.write(viptela_username.encode("ascii") + b"\n")
                            tn.read_until(b"Password:", timeout=1)
                            tn.write(viptela_password.encode("ascii") + b"\n")
                            tn.write(b"\r\n")
                            break
                        elif 'Welcome' in output:
                            tn.write(viptela_password.encode("ascii") + b"\n")
                            tn.read_until(b"password:", timeout=2)
                            tn.write(viptela_password.encode("ascii") + b"\n")
                            tn.write(b"\r\n")
                            break
                        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"{temp_node_name} not available yet, trying again in 30 seconds")
                        time.sleep(30)
                    tn.write(b"\r\n")
                    tn.read_until(b"#")
                    with open(file_name, 'r') as f:
                        lines = f.readlines()
                        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Sending configuration commands to {node_name[0]}")
                        for line in lines:
                            formatted_line = line.format(
                                vedge_hostname=vedge_hostname,
                                latitude=local_city_data[temp_node_name]['latitude'],
                                longitude=local_city_data[temp_node_name]['longitude'],
                                system_ip=system_ip,
                                site_id=site_id,
                                org_name=org_name,
                                vbond_address=vbond_vpn_0_ip,
                                vpn_0_ge0_0_ip_address=vpn_0_ge0_0_ip_address,
                                vpn_0_ge0_0_ip_gateway=vpn_0_ge0_0_ip_gateway,
                                vpn_0_ge0_1_ip_address=vpn_0_ge0_1_ip_address,
                                vpn_0_ge0_1_ip_gateway=vpn_0_ge0_1_ip_gateway,
                                vpn_1_ge0_2_ip_address=lan_dhcp_pool,
                                dhcp_pool=lan_subnet_address,
                                dhcp_exclude=lan_dhcp_exclude,
                                dhcp_gateway=lan_gateway_address,
                                client_1_address=client_1_address,
                                client_1_mac=client_1_mac_address,
                                vpn_512_eth0_ip_address=mgmt_address,
                                vpn_512_eth0_ip_gateway=mgmt_gateway
                            )
                            tn.write(formatted_line.encode('ascii') + b"\n")
                            tn.read_until(b"#")
                    tn.write(b"\r\n")
                    output = tn.read_until(b"Commit complete.").decode('ascii')
                    tn.write(b"exit\r")
                    tn.read_until(b"exit")
                    tn.close()
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed vEdge Device Setup for {temp_node_name}, Remaining - {site_count - i}")
                    if i % 44 == 0 and i != 0:
                        isp_index += 1
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed vEdge Device Setup for {site_count} vEdge devices")
    # endregion
    # region Viptela vManage API Setup
    deployment_step = ' vManage API Setup'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting vManage API Setup")
    auth = Authentication()
    while True:
        try:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Checking if vManage API is available..")
            response = auth.get_jsessionid(vmanage_mgmt_ip)
            break
        except:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f'vManage API is yet not available, checking again in 1 minute at {util_resume_time(1)}')
            time.sleep(60)
    vmanage_headers = vmanage_create_auth(vmanage_mgmt_ip)
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    for server_ip in server_ips:
        temp_node_name = f'vManage'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                tn = telnetlib.Telnet(server_ip, console_port)
                while True:
                    tn.write(b"\r\n")
                    output = tn.read_until(b"login:", timeout=2).decode('ascii')
                    if '#' in output:
                        tn.write(b"\r\n")
                        tn.read_until(b"#")
                        tn.write(b'vshell\r\n')
                        break
                    elif ':~$' in output:
                        tn.write(b"\r\n")
                        break
                    tn.write(viptela_username.encode("ascii") + b"\n")
                    tn.read_until(b"Password:", timeout=1)
                    tn.write(viptela_password.encode("ascii") + b"\n")
                    output = tn.read_until(b"#", timeout=1).decode('ascii')
                    if '#' in output:
                        tn.write(b"\r\n")
                        tn.read_until(b"#")
                        tn.write(b'vshell\r\n')
                        break
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"{temp_node_name} not available yet, trying again in 30 seconds")
                    time.sleep(30)
                tn.write(b"\r\n")
                tn.read_until(b'$')
                tn.write(b"cat SDWAN.pem\r")
                tn.read_until(b"cat SDWAN.pem")
                vmanage_root_cert = tn.read_until(b"-----END CERTIFICATE-----")
                vmanage_root_cert = vmanage_root_cert.decode('ascii').split('\r\n', 1)[1]
                vmanage_root_cert = vmanage_root_cert.replace('\r\n', '\n')
                vmanage_set_org(vmanage_mgmt_ip, vmanage_headers)
                vmanage_set_cert_type(vmanage_mgmt_ip, vmanage_headers)
                vmanage_set_cert(vmanage_mgmt_ip, vmanage_headers, vmanage_root_cert)
                vmanage_sync_rootcertchain(vmanage_mgmt_ip, vmanage_headers)
                vmanage_set_vbond(vmanage_mgmt_ip, vmanage_headers, vbond_vpn_0_ip)
                vmanage_csr = vmanage_generate_csr(vmanage_mgmt_ip, vmanage_headers, vmanage_mgmt_ip, 'vmanage')
                tn.write(b'exit\r\n')
                tn.read_until(b'#')
                tn.write(b'vshell\r\n')
                tn.read_until(b'$')
                tn.write(b'echo -n "' + vmanage_csr.encode('ascii') + b'\n" > vdevice.csr\r\n')
                tn.read_until(b'$')
                tn.write(b"sed '/^$/d' vdevice.csr\n")
                tn.read_until(b'$')
                tn.write(
                    b'openssl x509 -req -in vdevice.csr -CA SDWAN.pem -CAkey SDWAN.key -CAcreateserial -out vdevice.crt -days 2000 -sha256\r\n')
                tn.read_until(b'$')
                tn.write(b"cat vdevice.crt\r")
                tn.read_until(b"cat vdevice.crt\r")
                vdevice_cert = tn.read_until(b"-----END CERTIFICATE-----")
                vdevice_cert = vdevice_cert.decode('ascii').split('\r\n', 1)[1]
                vdevice_cert = vdevice_cert.replace('\r\n', '\n')
                vmanage_install_cert(vmanage_mgmt_ip, vmanage_headers, vdevice_cert)
                vmanage_set_device(vmanage_mgmt_ip, vmanage_headers, vsmart_vpn_0_ip, "vsmart")
                vmanage_set_device(vmanage_mgmt_ip, vmanage_headers, vbond_vpn_0_ip, "vbond")
                vbond_csr = vmanage_generate_csr(vmanage_mgmt_ip, vmanage_headers, vbond_vpn_0_ip, 'vbond')
                vsmart_csr = vmanage_generate_csr(vmanage_mgmt_ip, vmanage_headers, vsmart_vpn_0_ip, 'vsmart')
                tn.write(b'exit\r\n')
                tn.read_until(b'#')
                tn.write(b'vshell\r\n')
                tn.read_until(b'$')
                tn.write(b'echo -n "' + vsmart_csr.encode('ascii') + b'\n" > vdevice.csr\r\n')
                tn.read_until(b'$')
                tn.write(b"sed '/^$/d' vdevice.csr\n")
                tn.read_until(b'$')
                tn.write(
                    b'openssl x509 -req -in vdevice.csr -CA SDWAN.pem -CAkey SDWAN.key -CAcreateserial -out vdevice.crt -days 2000 -sha256\r\n')
                tn.read_until(b'$')
                tn.write(b"cat vdevice.crt\r")
                tn.read_until(b"cat vdevice.crt\r")
                vdevice_cert = tn.read_until(b"-----END CERTIFICATE-----")
                vdevice_cert = vdevice_cert.decode('ascii').split('\r\n', 1)[1]
                vdevice_cert = vdevice_cert.replace('\r\n', '\n')
                vmanage_install_cert(vmanage_mgmt_ip, vmanage_headers, vdevice_cert)
                tn.write(b'exit\r\n')
                tn.read_until(b'#')
                tn.write(b'vshell\r\n')
                tn.read_until(b'$')
                tn.write(b'echo -n "' + vbond_csr.encode('ascii') + b'\n" > vdevice.csr\r\n')
                tn.read_until(b'$')
                tn.write(b"sed '/^$/d' vdevice.csr\n")
                tn.read_until(b'$')
                tn.write(
                    b'openssl x509 -req -in vdevice.csr -CA SDWAN.pem -CAkey SDWAN.key -CAcreateserial -out vdevice.crt -days 2000 -sha256\r\n')
                tn.read_until(b'$')
                tn.write(b"cat vdevice.crt\r")
                tn.read_until(b"cat vdevice.crt\r")
                vdevice_cert = tn.read_until(b"-----END CERTIFICATE-----")
                vdevice_cert = vdevice_cert.decode('ascii').split('\r\n', 1)[1]
                vdevice_cert = vdevice_cert.replace('\r\n', '\n')
                vmanage_install_cert(vmanage_mgmt_ip, vmanage_headers, vdevice_cert)
                tn.write(b'exit\r\n')
                tn.read_until(b'#')
                tn.close()
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed vManage API Setup")
    # endregion
    # region Viptela vEdge Final Setup
    deployment_step = 'vEdge Final Setup'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting vEdge Certificate setup and deployment into Viptela Environment")
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    ve = 101
    v = 1
    for server_ip in server_ips:
        temp_node_name = f'vManage'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
        vedge_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, "vEdge")
        if matching_nodes:
            for matching_node in matching_nodes:
                node_id, console_port, aux = matching_node
                log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Logging in to console for node {temp_node_name}")
                for vedge_node in vedge_nodes:
                    vedge_id, vedge_console, vedge_aux = vedge_node
                    node_name = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'node_id', 'name', vedge_id)
                    scp_command = f"request execute vpn 512 scp /home/admin/SDWAN.pem admin@{mgmt_subnet_ip}.{ve}:/home/admin"
                    scp_2_command = f"request execute vpn 512 scp /home/admin/vedge.crt admin@{mgmt_subnet_ip}.{ve}:/home/admin"
                    scp_3_command = f"request execute vpn 512 scp /home/admin/vedge.csr admin@{mgmt_subnet_ip}.2:/home/admin"
                    ssh_command = f"request execute vpn 512 ssh admin@{mgmt_subnet_ip}.{ve}"
                    ssh_2_command = f"request execute vpn 512 ssh admin@{vbond_mgmt_ip}"
                    # tn = telnetlib.Telnet(server_ip, console_port)
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting vEdge Certificate Setup for {node_name[0]} - vEdge {v} of {site_count}")
                    while True:
                        tn = telnetlib.Telnet(server_ip, console_port)
                        tn.write(b"\r\n")
                        output = tn.read_until(b"login:", timeout=2).decode('ascii')
                        if '#' in output:
                            tn.write(b"\r\n")
                            tn.read_until(b"#")
                            tn.write(b'vshell\r\n')
                            break
                        elif ':~$' in output:
                            tn.write(b"\r\n")
                            break
                        tn.write(viptela_username.encode("ascii") + b"\n")
                        tn.read_until(b"Password:", timeout=1)
                        tn.write(viptela_password.encode("ascii") + b"\n")
                        output = tn.read_until(b"#", timeout=1).decode('ascii')
                        if '#' in output:
                            tn.write(b"\r\n")
                            tn.read_until(b"#")
                            tn.write(b'vshell\r\n')
                            break
                        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"{temp_node_name} not available yet, trying again in 30 seconds")
                        tn.close()
                        time.sleep(30)
                    tn.write(b"\r\n")
                    tn.read_until(b'$')
                    tn.write(b'rm -rf vedge*\r\n')
                    tn.read_until(b'$')
                    tn.write(b'exit\r\n')
                    # SCP SDWAN.pem to vEdge
                    tn.read_until(b'#')
                    tn.write(scp_command.encode('ascii') + b"\n")
                    test_o = tn.read_until(b"?", timeout=2).decode('ascii')
                    if "fingerprint" in test_o:
                        tn.write(b'yes\r\n')
                    else:
                        tn.write(b"\n")
                    tn.read_until(b"Password:")
                    tn.write(viptela_password.encode("ascii") + b"\n")
                    tn.read_until(b'#')
                    # SSH to vEdge
                    tn.write(ssh_command.encode('ascii') + b"\n")
                    tn.read_until(b"Password:")
                    tn.write(viptela_password.encode("ascii") + b"\n")
                    tn.read_until(b'#')
                    tn.write(b'request root-cert-chain install /home/admin/SDWAN.pem\n')
                    tn.read_until(b'#')
                    tn.write(b'request csr upload home/admin/vedge.csr\n')
                    tn.read_until(b":")
                    tn.write(b'sdwan-lab\n')
                    tn.read_until(b":")
                    tn.write(b'sdwan-lab\n')
                    tn.read_until(b'#')
                    # SCP the vEdge.csr to the vManage
                    tn.write(scp_3_command.encode('ascii') + b"\n")
                    test_o = tn.read_until(b"?", timeout=2).decode('ascii')
                    if "fingerprint" in test_o:
                        tn.write(b'yes\r\n')
                    else:
                        tn.write(b"\n")
                    tn.read_until(b"Password:")
                    tn.write(viptela_password.encode("ascii") + b"\n")
                    tn.read_until(b'#')
                    # Drop back to the vManage
                    tn.write(b'exit\r\n')
                    tn.read_until(b'vManage#')
                    tn.write(b'vshell\r\n')
                    tn.read_until(b'$')
                    tn.write(
                        b'openssl x509 -req -in vedge.csr -CA SDWAN.pem -CAkey SDWAN.key -CAcreateserial -out vedge.crt -days 2000 -sha256\n')
                    tn.read_until(b'$')
                    tn.write(b'exit\r\n')
                    tn.read_until(b'#')
                    # SCP the vEdge.crt to the vEdge
                    tn.write(scp_2_command.encode('ascii') + b"\n")
                    tn.read_until(b"Password:")
                    tn.write(viptela_password.encode("ascii") + b"\n")
                    tn.read_until(b'#')
                    # SSH to the vEdge to install the new cert
                    tn.write(ssh_command.encode('ascii') + b"\n")
                    tn.read_until(b"Password:")
                    tn.write(viptela_password.encode("ascii") + b"\n")
                    tn.read_until(b'#')
                    while True:
                        tn.write(b'request certificate install /home/admin/vedge.crt\r\n')
                        tn.read_until(b'#')
                        tn.write(b'show certificate serial\r\n')
                        cert_output = tn.read_until(b"#").decode("ascii")
                        chassis_regex = r"Chassis number: (.+?)\s+serial number:"
                        serial_regex = r"serial number: ([A-F0-9]+)"
                        chassis_number = re.search(chassis_regex, cert_output).group(1)
                        serial_number = re.search(serial_regex, cert_output).group(1)
                        if chassis_number and serial_number:
                            break
                        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"{node_name[0]} tried to install certificate too quickly, trying again in 10 seconds ")
                        time.sleep(10)
                    tn.write(b'exit\r\n')
                    tn.read_until(b'#')
                    vedge_install_command = f"request vedge add chassis-num {chassis_number} serial-num {serial_number}"
                    tn.write(ssh_2_command.encode('ascii') + b"\n")
                    tn.read_until(b"Password:")
                    tn.write(viptela_password.encode("ascii") + b"\n")
                    tn.read_until(b'#')
                    tn.write(vedge_install_command.encode('ascii') + b"\n")
                    tn.read_until(b'#')
                    tn.write(b'exit\r\n')
                    tn.read_until(b'#')
                    tn.write(vedge_install_command.encode('ascii') + b"\n")
                    tn.read_until(b'#')
                    ve += 1
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed vEdge Certificate Setup for {node_name[0]}, Remaining - {site_count - v}")
                    tn.close()
                    v += 1
    while True:
        try:
            auth = Authentication()
            response = auth.get_jsessionid(vmanage_mgmt_ip)
            break
        except:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f'vManage API is yet not available')
            time.sleep(60)
    vmanage_headers = vmanage_create_auth(vmanage_mgmt_ip)
    vmanage_push_certs(vmanage_mgmt_ip, vmanage_headers)
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed vEdge Certificate setup and deployment into Viptela Environment")
    # endregion
    # region Push vEdge Certs to Control Devices
    deployment_step = 'Push vEdge Certs'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Waiting 5 mins to send final API call to vManage to push vEdge certificates to control devices, to resume at {util_resume_time(5)}")
    time.sleep(300)
    while True:
        try:
            auth = Authentication()
            response = auth.get_jsessionid(vmanage_mgmt_ip)
            break
        except:
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f'vManage API is yet not available')
            time.sleep(60)
    vmanage_headers = vmanage_create_auth(vmanage_mgmt_ip)
    vmanage_push_certs(vmanage_mgmt_ip, vmanage_headers)
    # endregion
    # region AppNeta MP Setup
    if deploy_appneta == 'y':
        deployment_step = 'AppNeta Monitoring Point Setup'
        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                          f"Starting AppNeta Monitoring Point Configuration")
        server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
        v = 1
        for server_ip in server_ips:
            temp_node_name = f'AppNeta'
            matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
            if matching_nodes:
                for matching_node in matching_nodes:
                    mp_ip_address = f"{mgmt_subnet_ip}.{v+50}"
                    node_id, console_port, aux = matching_node
                    node_name = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'node_id', 'name',
                                                               node_id)
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                                      f"Logging in to console for node {node_name[0]}")
                    appneta_cli_curl_commands(server_ip, server_port, server_name, new_project_id, project_name, deployment_type, node_id, console_port, node_name[0], appneta_mp_mac, mp_ip_address, appn_site_key, appn_url)
                    v += 1

        log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,
                          f"Completed AppNeta MP Configuration")
    # endregion
    # region Validation
    client_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, "Site_")
    if client_nodes:
        for client_node in client_nodes:
            node_id, console_port, aux = client_node
            gns3_start_node(gns3_server_data, new_project_id, node_id)
    wait_time = 10  # minutes
    deployment_step = 'Validation'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Waiting {wait_time} minutes to validate deployment, to resume at {util_resume_time(wait_time)}")
    time.sleep(wait_time * 60)
    server_ips = set(d['GNS3 Server'] for d in gns3_server_data)
    for server_ip in server_ips:
        temp_node_name = f'001_Client'
        vedge_nodes = f'vEdge_'
        matching_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, temp_node_name)
        client_nodes = gns3_query_find_nodes_by_name(server_ip, server_port, new_project_id, vedge_nodes)
        client_ip = 101
        successful_site = 0
        i = 1
        if matching_nodes:
            node_id, console_port, aux = matching_nodes[0]
            node_name = gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'node_id', 'name', node_id)
            log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Starting deployment validation on node {node_name[0]}")
            tn = telnetlib.Telnet(server_ip, console_port)
            tn.write(b"\r\n")
            tn.read_until(b"#")
            for client_node in client_nodes:
                ping_command = f"ping -c 2 -W 1 172.16.{client_ip}.1"
                tn.write(ping_command.encode('ascii') + b"\r")
                output = tn.read_until(b"loss", timeout=5).decode('ascii')
                if "100% packet" in output:
                    client_node_name = \
                    gns3_query_find_nodes_by_field(server_ip, server_port, new_project_id, 'node_id', 'name', client_nodes[i][0])[0]
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Packet Loss to Site {client_ip}")
                else:
                    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step,f"Successfully connected to Site {client_ip}")
                    successful_site += 1
                client_ip += 1
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Successful connection to {successful_site} of {len(client_nodes)} Sites")
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Completed deployment validation for project {project_name}")
    # endregion

    end_time = time.time()
    total_time = (end_time - start_time) / 60
    deployment_step = 'Complete'
    deployment_status = 'Complete'
    log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, f"Total time for GNS3 Lab Deployment with {site_count} vEdge Devices: {total_time:.2f} minutes")
    # endregion

