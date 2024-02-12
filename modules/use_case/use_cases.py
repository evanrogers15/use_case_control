import time

from modules.gns3.gns3_query import *
from modules.gns3.gns3_actions import *
import logging.handlers

def use_case_15(server, port, project_id, state):
    filter_type = 'packet_loss'
    filter_value = '10'
    link_id_dev = "0f296ad9-2992-4d32-afda-3deeafe908b1"
    link_id = "7a7bd227-4f15-4d21-8152-0b2fc5427c3e"
    if state == 'on':
        gns3_set_single_packet_filter_simple(server, port, project_id, link_id, filter_type, filter_value)
        return {'message': 'Scenario started successfully.'}, 200
    else:
        gns3_remove_single_packet_filter(server, port, project_id, link_id)
        return {'message': 'Scenario started successfully.'}, 200
def use_case_1(server, port, project_id, state):
    filter_type = 'packet_loss'
    filter_value = '10'
    remote_node_name = 'FlexVNF-002-Seattle'
    router_node_name = 'isp-seattle'
    nodes = gns3_query_get_nodes(server, port, project_id)

    router_node_id, router_console, router_aux = gns3_query_find_node_by_name(nodes, router_node_name)
    remote_node_id_1, remote_node_console_1, remote_node_aux_1 = gns3_query_find_node_by_name(nodes, remote_node_name)

    links = gns3_query_get_links(server, port, project_id, router_node_id)
    link_id = gns3_query_get_node_links(nodes, links, server, port, project_id, router_node_id, remote_node_id_1, 'e1')
    if state == 'on':
        gns3_set_single_packet_filter_simple(server, port, project_id, link_id, filter_type, filter_value)
        return {'message': 'Scenario started successfully.'}, 200
    else:
        gns3_remove_single_packet_filter(server, port, project_id, link_id)
        return {'message': 'Scenario stopped successfully.'}, 200

def use_case_25(server, port, project_id, state):
    link_id_dev = "8606cf9c-da87-4bf6-b620-5e6d344adeb7"
    link_id = "24196a68-abd6-4927-a615-926bd8ab08b9"
    gns3_set_suspend(server, port, project_id, link_id)
    return {'message': 'Scenario started successfully.'}, 200

def use_case_2(server, port, project_id, state):
    remote_node_name = 'atlanta-sw-dist-02'
    router_node_name = 'atlanta-sw-core-01'
    nodes = gns3_query_get_nodes(server, port, project_id)

    router_node_id, router_console, router_aux = gns3_query_find_node_by_name(nodes, router_node_name)
    remote_node_id_1, remote_node_console_1, remote_node_aux_1 = gns3_query_find_node_by_name(nodes, remote_node_name)

    links = gns3_query_get_links(server, port, project_id, router_node_id)
    link_id = gns3_query_get_node_links(nodes, links, server, port, project_id, router_node_id, remote_node_id_1, 'eth0')
    if state == 'on':
        gns3_set_suspend(server, port, project_id, link_id)
        return {'message': 'Scenario started successfully.'}, 200
    else:
        gns3_reset_single_suspend(server, port, project_id, link_id)
        return {'message': 'Scenario stopped successfully.'}, 200

def use_case_3(server, port, project_id, state):
    remote_node_name = 'Miami-Client-2'
    nodes = gns3_query_get_nodes(server, port, project_id)
    remote_node_id, remote_node_console, remote_node_aux = gns3_query_find_node_by_name(nodes, remote_node_name)
    client_command = f'python3 /home/torrent_use_case.py 6881'
    gns3_run_telnet_command(server, port, project_id, remote_node_id, remote_node_aux, state, client_command)
    remote_node_name = 'Miami-Client'
    nodes = gns3_query_get_nodes(server, port, project_id)
    remote_node_id, remote_node_console, remote_node_aux = gns3_query_find_node_by_name(nodes, remote_node_name)
    client_command = f'python3 /home/torrent_use_case.py 6681'
    gns3_run_telnet_command(server, port, project_id, remote_node_id, remote_node_aux, state, client_command)

    return {'message': 'Scenario started successfully.'}, 200

def use_case_4(server, port, project_id, state):
    viptela_new_password = "CAdemo@123"
    viptela_username = "admin"
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
            tn.write(viptela_new_password.encode("ascii") + b"\n")

    time.sleep(5)
    if state == "on":
        for command in config_commands_start:
            client_command = command
            tn.write(b"\r\n")
            tn.write(client_command.encode("ascii") + b"\n")
            time.sleep(.5)
    elif state == "off":
        for command in config_commands_stop:
            client_command = command
            tn.write(b"\r\n")
            tn.write(client_command.encode("ascii") + b"\n")
            time.sleep(.5)

    return {'message': 'Scenario started successfully.'}, 200

def use_case_5(server, port, project_id, state):
    remote_node_name = 'isp-chicago'
    nodes = gns3_query_get_nodes(server, port, project_id)
    remote_node_id, remote_node_console, remote_node_aux = gns3_query_find_node_by_name(nodes, remote_node_name)

    config_commands_start = ["bash", "cd /etc/frr", "python3 bandwidth_adjuster.py add eth0 30", "exit"]

    config_commands_stop = ["bash", "cd /etc/frr", "python3 bandwidth_adjuster.py remove eth0", "exit"]

    tn = telnetlib.Telnet(server, remote_node_aux, timeout=1)

    tn.write(b"\n")

    time.sleep(2)
    if state == "on":
        for command in config_commands_start:
            client_command = command
            tn.write(b"\r\n")
            tn.write(client_command.encode("ascii") + b"\n")
            time.sleep(.5)

    elif state == "off":
        for command in config_commands_stop:
            client_command = command
            tn.write(b"\r\n")
            tn.write(client_command.encode("ascii") + b"\n")
            time.sleep(.5)

    return {'message': 'Scenario started successfully.'}, 200