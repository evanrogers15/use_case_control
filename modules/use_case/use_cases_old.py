import time

from modules.gns3.gns3_query import *
from modules.gns3.gns3_actions import *
import logging.handlers

def use_case_12(server, port, project_id, state):
    matching_nodes = gns3_query_find_nodes_by_field(server, port, project_id, 'name', 'name', 'Client')
    site_001_matching_nodes = gns3_query_find_nodes_by_field(server, port, project_id, 'name', 'name', '001')
    for node_name in site_001_matching_nodes:
        if 'Edge' in node_name or 'FlexVNF' in node_name:
            router_node_name = node_name
    else:
        logging.info("No site routers found..")

    remote_node_name_1 = 'Cloud_ISP_01'
    # router_node_name = 'vEdge_001_NewYork'
    filter_type = 'packet_loss'
    filter_value = '5'
    nodes = gns3_query_get_nodes(server, port, project_id)
    router_node_id, router_console, router_aux = gns3_query_find_node_by_name(nodes, router_node_name)
    links = gns3_query_get_links(server, port, project_id, router_node_id)
    remote_node_id_1, remote_node_console_1, remote_node_aux_1 = gns3_query_find_node_by_name(nodes, remote_node_name_1)
    link_id = gns3_query_get_node_links(nodes, links, server, port, project_id, router_node_id, remote_node_id_1, '1/0')
    client_count = len(matching_nodes)
    #client_command_2 = f'nohup python3 /home/scripts/iperf3_server.py {client_count} &'
    client_command_2 = f'nohup python3 /home/scripts/iperf3_server.py {client_count} | tail -n 60 > output.log 2>&1 &'
    if state == 'on':
        for index, client in enumerate(matching_nodes):
            server_ip = f"172.16.102.51"
            client_command_1 = f'nohup sh -c "while true; do rand=\$(shuf -i 5-80 -n 1)m; echo \$rand; iperf3 -c {server_ip} -p 520{index+1} -u -b \$rand -t 30; done" > /dev/null 2>&1 &'
            client_node_id, client_console, client_aux = gns3_query_find_node_by_name(nodes, client)
            gns3_change_node_state(server, port, project_id, client_node_id, 'on')
            if index == 1: #len(matching_nodes) - 1:
                gns3_run_telnet_command(server, port, project_id, client_node_id, client_console, state, client_command_2)
            else:
                gns3_run_telnet_command(server, port, project_id, client_node_id, client_console, state, client_command_1)
        gns3_set_single_packet_filter(server, port, project_id, link_id, filter_type, filter_value)
        return {'message': 'Scenario started successfully.'}, 200
    else:
        for index, client in enumerate(matching_nodes):
            client_node_id, client_node_console, client_node_aux = gns3_query_find_node_by_name(nodes, client)
            gns3_change_node_state(server, port, project_id, client_node_id, 'off')
        gns3_remove_single_packet_filter(server, port, project_id, link_id)
        return {'message': 'Scenario started successfully.'}, 200

def use_case_2_old(server, port, project_id, state):
    client_nodes = gns3_query_find_nodes_by_field(server, port, project_id, 'name', 'name', 'Client')
    site_001_matching_nodes = gns3_query_find_nodes_by_field(server, port, project_id, 'name', 'name', '001')
    for node_name in site_001_matching_nodes:
        if 'Edge' in node_name:
            matching_nodes = gns3_query_find_nodes_by_field(server, port, project_id, 'name', 'name', 'vEdge')
            break
        elif 'FlexVNF' in node_name:
            matching_nodes = gns3_query_find_nodes_by_field(server, port, project_id, 'name', 'name', 'FlexVNF')
            break
    else:
        logging.info("No site routers found..")
    client_count = len(client_nodes)
    client_command_2 = f'nohup python3 /home/scripts/iperf3_server.py {client_count} | tail -n 60 > output.log 2>&1 &'
    nodes = gns3_query_get_nodes(server, port, project_id)
    if state == 'on':
        for site in matching_nodes:
            remote_node_name_1 = 'Cloud_ISP_001'
            router_node_name = site
            filter_type = 'packet_loss'
            filter_value = '5'
            router_node_id, router_console, router_aux = gns3_query_find_node_by_name(nodes, router_node_name)
            remote_node_id_1, remote_node_console_1, remote_node_aux_1 = gns3_query_find_node_by_name(nodes, remote_node_name_1)
            links = gns3_query_get_links(server, port, project_id, router_node_id)
            link_id = gns3_query_get_node_links(nodes, links, server, port, project_id, router_node_id, remote_node_id_1, '1/0')
            gns3_set_single_packet_filter(server, port, project_id, link_id, filter_type, filter_value)
        for index, client in enumerate(client_nodes):
            server_ip = f"172.16.102.51"
            client_command_1 = f'nohup sh -c "while true; do rand=\$(shuf -i 5-80 -n 1)m; echo \$rand; iperf3 -c {server_ip} -p 520{index + 1} -u -b \$rand -t 30; done" > /dev/null 2>&1 &'
            client_node_id, client_console, client_aux = gns3_query_find_node_by_name(nodes, client)
            gns3_change_node_state(server, port, project_id, client_node_id, 'on')
            if index == 1:
                gns3_run_telnet_command(server, port, project_id, client_node_id, client_console, state, client_command_2)
            else:
                gns3_run_telnet_command(server, port, project_id, client_node_id, client_console, state, client_command_1)
        return {'message': 'Scenario started successfully.'}, 200
    else:
        for site in matching_nodes:
            remote_node_name_1 = 'Cloud_ISP_001'
            router_node_name = site
            router_node_id, router_console, router_aux = gns3_query_find_node_by_name(nodes, router_node_name)
            remote_node_id_1, remote_node_console_1, remote_node_aux_1 = gns3_query_find_node_by_name(nodes, remote_node_name_1)
            links = gns3_query_get_links(server, port, project_id, router_node_id)
            link_id = gns3_query_get_node_links(nodes, links, server, port, project_id, router_node_id, remote_node_id_1, '1/0')
            gns3_remove_single_packet_filter(server, port, project_id, link_id)
        for index, client in enumerate(client_nodes):
            client_node_id, client_node_console, client_node_aux = gns3_query_find_node_by_name(nodes, client)
            gns3_change_node_state(server, port, project_id, client_node_id, 'off')
        return {'message': 'Scenario started successfully.'}, 200
def use_case_1_temp(server, port, project_id, state):
    matching_nodes = gns3_query_find_nodes_by_field(server, port, project_id, 'name', 'name', 'Client')
    site_001_matching_nodes = gns3_query_find_nodes_by_field(server, port, project_id, 'name', 'name', '001')
    for node_name in site_001_matching_nodes:
        if 'Edge' in node_name or 'FlexVNF' in node_name:
            router_node_name = node_name
    else:
        logging.info("No site routers found..")
    remote_node_name_1 = 'Cloud_ISP_01'
    filter_type = 'packet_loss'
    filter_value = '5'
    nodes = gns3_query_get_nodes(server, port, project_id)
    router_node_id, router_console, router_aux = gns3_query_find_node_by_name(nodes, router_node_name)
    links = gns3_query_get_links(server, port, project_id, router_node_id)
    remote_node_id_1, remote_node_console_1, remote_node_aux_1 = gns3_query_find_node_by_name(nodes, remote_node_name_1)
    link_id = gns3_query_get_node_links(nodes, links, server, port, project_id, router_node_id, remote_node_id_1, '1/0')
    client_count = len(matching_nodes)
    if state == 'on':
        for index, client in enumerate(matching_nodes):
            client_command = f'python3 /home/scripts/traffic/client_traffic_generator.py {client_count} &'
            client_node_id, client_console, client_aux = gns3_query_find_node_by_name(nodes, client)
            gns3_change_node_state(server, port, project_id, client_node_id, 'on')
            gns3_run_telnet_command(server, port, project_id, client_node_id, client_console, state,
                                    client_command)
        gns3_set_single_packet_filter(server, port, project_id, link_id, filter_type, filter_value)
        return {'message': 'Scenario started successfully.'}, 200
    else:
        for index, client in enumerate(matching_nodes):
            client_node_id, client_node_console, client_node_aux = gns3_query_find_node_by_name(nodes, client)
            gns3_change_node_state(server, port, project_id, client_node_id, 'off')
        gns3_remove_single_packet_filter(server, port, project_id, link_id)
        return {'message': 'Scenario started successfully.'}, 200

def use_case_1(server, port, project_id, state):
    filter_type = 'packet_loss'
    filter_value = '10'
    link_id = "0f296ad9-2992-4d32-afda-3deeafe908b1"
    if state == 'on':
        gns3_set_single_packet_filter_simple(server, port, project_id, link_id, filter_type, filter_value)
        return {'message': 'Scenario started successfully.'}, 200
    else:
        gns3_remove_single_packet_filter(server, port, project_id, link_id)
        return {'message': 'Scenario started successfully.'}, 200

def use_case_2(server, port, project_id, state):
    link_id_test = "c3cef7b6-77b3-4b27-b419-23900542c6a3"
    link_id = "8606cf9c-da87-4bf6-b620-5e6d344adeb7"
    gns3_set_suspend(server, port, project_id, link_id)
    return {'message': 'Scenario started successfully.'}, 200

def use_case_3(server, port, project_id, state):
    remote_node_name = 'SanFran-Client-2'
    nodes = gns3_query_get_nodes(server, port, project_id)
    remote_node_id, remote_node_console, remote_node_aux = gns3_query_find_node_by_name(nodes, remote_node_name)
    client_command = f'python3 /home/torrent_use_case.py 6681'
    gns3_run_telnet_command(server, port, project_id, remote_node_id, remote_node_aux, state, client_command)

    return {'message': 'Scenario started successfully.'}, 200

def use_case_4(server, port, project_id, state):
    remote_node_name = 'vEdge_001_Houston'
    nodes = gns3_query_get_nodes(server, port, project_id)
    remote_node_id, remote_node_console, remote_node_aux = gns3_query_find_node_by_name(nodes, remote_node_name)

    config_commands_start = ["conf t", "vpn 0", "int ge0/1", "nat", "respond-to-ping", "no block-icmp-error",
                            "int ge0/0", "no nat", "commit and-quit"]

    config_commands_stop = ["conf t", "vpn 0", "int ge0/0", "nat", "respond-to-ping", "no block-icmp-error", "int ge0/1",
        "no nat", "commit and-quit"]

    tn = telnetlib.Telnet(server, remote_node_console, timeout=1)

    tn.write(b"\r\n")
    output = tn.read_until(b"login:", timeout=1)
    if b"login" in output:
        tn.write(viptela_username.encode("ascii") + b"\n")
        output = tn.read_until(b"Password:", timeout=3)
        if b"Password:" in output:
            tn.write(viptela_password.encode("ascii") + b"\n")

    time.sleep(5)
    if state == "on":
        for command in config_commands_start:
            client_command = command
            tn.write(b"\r\n")
            tn.write(client_command.encode("ascii") + b"\n")
            time.sleep(.5)
            # gns3_run_telnet_command(server, port, project_id, remote_node_id, remote_node_console, state, client_command)
    elif state == "off":
        for command in config_commands_stop:
            client_command = command
            tn.write(b"\r\n")
            tn.write(client_command.encode("ascii") + b"\n")
            time.sleep(.5)
            # gns3_run_telnet_command(server, port, project_id, remote_node_id, remote_node_console, state, client_command)

    return {'message': 'Scenario started successfully.'}, 200