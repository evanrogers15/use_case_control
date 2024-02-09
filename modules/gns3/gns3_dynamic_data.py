import ipaddress
import os
import logging.handlers
# from modules.gns3.gns3_variables import city_data, cedge_city_data, city_data

# region Generic
def generate_temp_hub_data(num_ports, template_name):
    ports_mapping = [{"name": f"Ethernet{i}", "port_number": i} for i in range(num_ports)]

    temp_hub_data = {
        "category": "switch",
        "compute_id": "local",
        "default_name_format": "Hub{0}",
        "name": template_name,
        "ports_mapping": ports_mapping,
        "symbol": ":/symbols/hub.svg",
        "template_type": "ethernet_hub"
    }
    return temp_hub_data

def generate_edge_network_objects(version, base_subnet, subnet_mask, site_index=1):
    network = ipaddress.IPv4Network(base_subnet)
    subnets_64 = list(network.subnets(new_prefix=subnet_mask))
    networks = []
    switch_limit = 1
    for subnet in subnets_64:
        if subnet.prefixlen == subnet_mask:
            if switch_limit == 45:
                break
            router_address = str(subnet.network_address + 1)
            edge_device_address = str(subnet.network_address + 2)
            subnet_address = str(
                ipaddress.IPv4Interface(str(subnet.network_address) + '/' + str(subnet_mask)).netmask)
            subnet_address_long = str(edge_device_address) + '/' + str(subnet_mask)
            if version == 'vedge':
                network_dict = {
                    'subnet': str(subnet.network_address),
                    'subnet_mask': str(subnet.prefixlen),
                    'subnet_address': subnet_address,
                    'router_address': router_address,
                    'vedge_address': subnet_address_long,
                    'isp_switch_address': edge_device_address,
                    'vedge': f'vEdge_{site_index:003}'
                }
            elif version == 'cedge':
                network_dict = {
                    'subnet': str(subnet.network_address),
                    'subnet_mask': str(subnet.prefixlen),
                    'subnet_address': subnet_address,
                    'router_address': router_address,
                    'cedge_address': subnet_address_long,
                    'isp_switch_address': edge_device_address,
                    'cedge': f'cEdge_{site_index:003}'
                }
            networks.append(network_dict)
            site_index += 1
            switch_limit += 1
    return networks

def generate_client_interfaces_file(filename_temp, ip=None):
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), '../configs/')
    filename = os.path.join(configs_path, filename_temp)

    with open(filename, 'w') as f:
        f.write('auto eth0\n')
        f.write('iface eth0 inet dhcp\n')
        # f.write('\tup echo nameserver 192.168.122.1 > /etc/resolv.conf\n')
        f.write('\thwaddress ether 4C:D7:17:00:00:00\n\n')
        if ip:
            f.write('auto eth1\n')
            f.write('iface eth1 inet static\n')
            f.write(f'\taddress {ip}\n')
            f.write('\tnetmask 255.255.255.0\n\n')

    logging.info(f"Deploy - Created file {filename_temp}")

def generate_interfaces_file(version, interface_data_2, interface_data_3, filename_temp, mgmt_component_1_gateway_ip=None, mgmt_component_2_gateway_ip=None, mgmt_component_3_gateway_ip=None):
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), '../configs/')
    filename = os.path.join(configs_path, filename_temp)
    with open(filename, 'w') as f:
        eth_1 = 0
        eth_2 = 0
        f.write(f'#{filename}\n')
        f.write('auto eth0\n')
        f.write('iface eth0 inet static\n')
        f.write(f'\taddress 192.168.122.250\n')
        f.write(f'\tnetmask 255.255.255.0\n')
        f.write(f'\tgateway 192.168.122.1\n')
        f.write('\tup echo nameserver 192.168.122.1 > /etc/resolv.conf\n\n')
        f.write('auto eth1\n')
        f.write('iface eth1 inet static\n')
        if version == "vedge" or version == "cedge":
            f.write(f'\taddress {mgmt_component_1_gateway_ip}\n')
            f.write(f'\tnetmask 255.255.255.252\n')
            f.write('auto eth2\n')
            f.write('iface eth2 inet static\n')
            f.write(f'\taddress {mgmt_component_2_gateway_ip}\n')
            f.write(f'\tnetmask 255.255.255.252\n')
            f.write('auto eth3\n')
            f.write('iface eth3 inet static\n')
            f.write(f'\taddress {mgmt_component_3_gateway_ip}\n')
            f.write(f'\tnetmask 255.255.255.252\n')
        elif version == "flexvnf":
            f.write(f'\taddress {mgmt_component_1_gateway_ip}\n')
            f.write(f'\tnetmask 255.255.255.252\n')
            f.write('auto eth2\n')
            f.write('iface eth2 inet static\n')
            f.write(f'\taddress {mgmt_component_2_gateway_ip}\n')
            f.write(f'\tnetmask 255.255.255.252\n')
            f.write('auto eth3\n')
            f.write('iface eth3 inet static\n')
        for i in range(5, 49):
            f.write(f'#{interface_data_2[eth_1][version]} interface ge0/0\n')
            f.write(f'auto eth{i}\n')
            f.write(f'iface eth{i} inet static\n')
            f.write(f'\taddress {interface_data_2[eth_1]["router_address"]}\n')
            f.write(f'\tnetmask {interface_data_2[eth_1]["subnet_address"]}\n')
            f.write('\n')
            eth_1 += 1
        for i in range(51, 95):
            f.write(f'#{interface_data_3[eth_2][version]} interface ge0/1\n')
            f.write(f'auto eth{i}\n')
            f.write(f'iface eth{i} inet static\n')
            f.write(f'\taddress {interface_data_3[eth_2]["router_address"]}\n')
            f.write(f'\tnetmask {interface_data_3[eth_2]["subnet_address"]}\n')
            f.write('\n')
            eth_2 += 1
    logging.info(f"Deploy - Created file {filename_temp}")

def generate_mgmt_switch_deploy_data(num_nodes):
    deploy_data = {}
    x = -279
    y_s = -313
    for i in range(1, num_nodes + 1):
        name = f"MGMT_switch_{i:03}"
        if i == 1:
            y = y_s
        else:
            y = y + 100
        deploy_data[f"mgmt_switch_{i:03}_deploy_data"] = {"x": x, "y": y, "name": name}


    return deploy_data
# endregion
# region Viptela Specific
def generate_vedge_objects(vedge_count, mgmt_base_subnet):
    subnet_mask = 24
    k = 101
    networks = []
    for i in range(1, vedge_count + 1):
        base_subnet = f'172.16.{k}.0/24'
        network = ipaddress.IPv4Network(base_subnet)
        subnets_64 = list(network.subnets(new_prefix=subnet_mask))
        for subnet in subnets_64:
            if subnet.prefixlen == subnet_mask:
                router_address = str(subnet.network_address + 1)
                vedge_address = str(subnet.network_address + 2)
                subnet_address_full = str(
                    ipaddress.IPv4Interface(str(subnet.network_address) + '/' + str(subnet_mask)).netmask)
                subnet_address_var = str(subnet.network_address) + '/' + str(subnet_mask)
                dhcp_exclude_var = str(subnet.network_address + 1) + '-' + str(subnet.network_address + 50)
                client_1_address_var = str(subnet.network_address + 51)
                network_dict = {
                    'lan_subnet_address': subnet_address_var,
                    'lan_gateway_address': router_address,
                    'lan_dhcp_pool': f'{router_address}/24',
                    'lan_dhcp_exclude': dhcp_exclude_var,
                    'client_1_address': client_1_address_var,
                    'vedge': f'vEdge_{i:003}',
                    'system_ip': f'{mgmt_base_subnet}.{i + 100}',
                    'mgmt_address': f'{mgmt_base_subnet}.{i + 100}/24',
                    'mgmt_gateway': f'{mgmt_base_subnet}.1',
                    'site_id': k,
                    'org_name': 'sdwan-lab'
                }
            networks.append(network_dict)
            k += 1
    # logging.info(networks)
    return networks

def generate_vedge_deploy_data(vedge_count, city_data):
    deploy_data = {}
    client_deploy_data = {}
    site_drawing_deploy_data = {}
    e = 1
    o = 1
    y_modifier = 0
    x_o = -557
    x_e = 267
    y = -554
    y_s = -554
    row_count = 20

    client_x = 0
    client_y = 0
    client_y_modifier = 115

    drawing_x = 0
    drawing_y = 0
    drawing_x_modifier = 200

    if vedge_count <= 10:
        row_count = 4
        y = -107
        y_s = -107
        for i in range(1, vedge_count + 1):
            temp_name = f"vEdge_{i:03}"
            name = f"vEdge_{i:03}_{city_data[temp_name]['city']}"
            client_name = f"Site_{i:03}_Client"
            if i == 1:
                x = x_o
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i == 2:
                x = x_e
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i <= row_count:
                if i % 2 == 0:
                    x = x_e + 200 * e
                    client_x = x
                    drawing_x = x - 57
                    drawing_y = y - 55
                    e += 1
                else:
                    x = x_o + -200 * o
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                    o += 1
            else:
                if (i - 1) % row_count == 0:
                    e = 1
                    o = 1
                    y_modifier += 1
                    x_o = -557
                    x_e = 267
                if i % 2 == 0:
                    x = x_e + 200 * (e - 1)
                    e += 1
                    y = y_s + 300 * y_modifier
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o - 200 * (o - 1)
                    y = y_s + 300 * y_modifier
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            deploy_data[f"vedge_{i:03}_deploy_data"] = {"x": x, "y": y, "name": name}
            client_deploy_data[f"network_test_client_{i:03}_deploy_data"] = {"x": client_x, "y": client_y,
                                                                             "name": client_name}
            site_drawing_deploy_data[f"site_drawing_{i:03}_deploy_data"] = {
                "svg": "<svg height=\"267\" width=\"169\"><rect fill=\"#aaffff\" fill-opacity=\"1.0\" height=\"267\" stroke=\"#000000\" stroke-width=\"2\" width=\"169\" /></svg>",
                "x": drawing_x, "y": drawing_y, "z": 0}
    elif vedge_count <= 25:
        row_count = 10
        y = -107
        y_s = -107
        for i in range(1, vedge_count + 1):
            temp_name = f"vEdge_{i:03}"
            name = f"vEdge_{i:03}_{city_data[temp_name]['city']}"
            client_name = f"Site_{i:03}_Client"
            if i == 1:
                x = x_o
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i == 2:
                x = x_e
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i <= row_count:
                if i % 2 == 0:
                    x = x_e + 200 * e
                    e += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o + -200 * (o)
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            else:
                if (i - 1) % row_count == 0:
                    e = 1
                    o = 1
                    y_modifier += 1
                    x_o = -557
                    x_e = 267
                if i % 2 == 0:
                    x = x_e + 200 * (e - 1)
                    e += 1
                    y = y_s + 300 * y_modifier
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o - 200 * (o - 1)
                    y = y_s + 300 * y_modifier
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            deploy_data[f"vedge_{i:03}_deploy_data"] = {"x": x, "y": y, "name": name}
            client_deploy_data[f"network_test_client_{i:03}_deploy_data"] = {"x": client_x, "y": client_y,
                                                                             "name": client_name}
            site_drawing_deploy_data[f"site_drawing_{i:03}_deploy_data"] = {
                "svg": "<svg height=\"267\" width=\"169\"><rect fill=\"#aaffff\" fill-opacity=\"1.0\" height=\"267\" stroke=\"#000000\" stroke-width=\"2\" width=\"169\" /></svg>",
                "x": drawing_x, "y": drawing_y, "z": 0}
    elif vedge_count <= 50:
        row_count = 10
        #y = -107
        #y_s = -107
        for i in range(1, vedge_count + 1):
            temp_name = f"vEdge_{i:03}"
            name = f"vEdge_{i:03}_{city_data[temp_name]['city']}"
            client_name = f"Site_{i:03}_Client"
            if i == 1:
                x = x_o
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i == 2:
                x = x_e
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i <= row_count:
                if i % 2 == 0:
                    x = x_e + 200 * e
                    e += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o + -200 * (o)
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            else:
                if (i - 1) % row_count == 0:
                    e = 1
                    o = 1
                    y_modifier += 1
                    x_o = -557
                    x_e = 267
                if i % 2 == 0:
                    x = x_e + 200 * (e - 1)
                    e += 1
                    y = y_s + 300 * y_modifier
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o - 200 * (o - 1)
                    y = y_s + 300 * y_modifier
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            deploy_data[f"vedge_{i:03}_deploy_data"] = {"x": x, "y": y, "name": name}
            client_deploy_data[f"network_test_client_{i:03}_deploy_data"] = {"x": client_x, "y": client_y,
                                                                             "name": client_name}
            site_drawing_deploy_data[f"site_drawing_{i:03}_deploy_data"] = {
                "svg": "<svg height=\"267\" width=\"169\"><rect fill=\"#aaffff\" fill-opacity=\"1.0\" height=\"267\" stroke=\"#000000\" stroke-width=\"2\" width=\"169\" /></svg>",
                "x": drawing_x, "y": drawing_y, "z": 0}

    else:
        for i in range(1, vedge_count + 1):
            temp_name = f"vEdge_{i:03}"
            name = f"vEdge_{i:03}_{city_data[temp_name]['city']}"
            client_name = f"Site_{i:03}_Client"
            if i == 1:
                x = x_o
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i == 2:
                x = x_e
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i <= row_count:
                if i % 2 == 0:
                    x = x_e + 200 * e
                    e += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o + -200 * o
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            else:
                if (i - 1) % row_count == 0:
                    e = 1
                    o = 1
                    y_modifier += 1
                    x_o = -557
                    x_e = 267
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                if i % 2 == 0:
                    x = x_e + 200 * (e - 1)
                    e += 1
                    y = y_s + 300 * y_modifier
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o - 200 * (o - 1)
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            deploy_data[f"vedge_{i:03}_deploy_data"] = {"x": x, "y": y, "name": name}
            client_deploy_data[f"network_test_client_{i:03}_deploy_data"] = {"x": client_x, "y": client_y,
                                                                             "name": client_name}
            site_drawing_deploy_data[f"site_drawing_{i:03}_deploy_data"] = {
                "svg": "<svg height=\"267\" width=\"169\"><rect fill=\"#aaffff\" fill-opacity=\"1.0\" height=\"267\" stroke=\"#000000\" stroke-width=\"2\" width=\"169\" /></svg>",
                "x": drawing_x, "y": drawing_y, "z": 0}
    return deploy_data, client_deploy_data, site_drawing_deploy_data

def generate_cedge_objects(edge_count, mgmt_base_subnet):
    subnet_mask = 24
    k = 101
    networks = []
    for i in range(1, edge_count + 1):
        base_subnet = f'172.16.{k}.0/24'
        network = ipaddress.IPv4Network(base_subnet)
        subnets_64 = list(network.subnets(new_prefix=subnet_mask))
        for subnet in subnets_64:
            if subnet.prefixlen == subnet_mask:
                router_address = str(subnet.network_address + 1)
                vedge_address = str(subnet.network_address + 2)
                lan_dhcp_exclude_start = str(subnet.network_address + 1)
                lan_dhcp_exclude_end = str(subnet.network_address + 50)
                subnet_address_full = str(subnet.netmask)  # Full subnet mask
                subnet_address_var = str(subnet.network_address) + '/' + str(subnet_mask)
                dhcp_exclude_var = str(subnet.network_address + 1) + '-' + str(subnet.network_address + 50)
                client_1_address_var = str(subnet.network_address + 51)
                network_dict = {
                    'lan_subnet_mask': subnet_address_full,
                    'lan_subnet_network': subnet.network_address,
                    'lan_subnet_address': subnet_address_var,
                    'lan_gateway_address': router_address,
                    'lan_dhcp_pool': f'{router_address}/24',
                    'lan_dhcp_exclude_start': lan_dhcp_exclude_start,
                    'lan_dhcp_exclude_end': lan_dhcp_exclude_end,
                    'lan_dhcp_exclude': dhcp_exclude_var,
                    'client_1_address': client_1_address_var,
                    'cedge': f'cEdge_{i:003}',
                    'system_ip': f'{mgmt_base_subnet}.{i + 100}',
                    'mgmt_address': f'{mgmt_base_subnet}.{i + 100}',
                    'mgmt_gateway': f'{mgmt_base_subnet}.1',
                    'site_id': k,
                    'org_name': 'sdwan-lab'
                }
            networks.append(network_dict)
            k += 1
    return networks

def generate_cedge_deploy_data(edge_count, city_data):
    deploy_data = {}
    client_deploy_data = {}
    site_drawing_deploy_data = {}
    e = 1
    o = 1
    y_modifier = 0
    x_o = -557
    x_e = 267
    y = -554
    y_s = -554
    row_count = 20

    client_x = 0
    client_y = 0
    client_y_modifier = 115

    drawing_x = 0
    drawing_y = 0
    drawing_x_modifier = 200

    if edge_count <= 10:
        row_count = 4
        y = -107
        y_s = -107
        for i in range(1, edge_count + 1):
            temp_name = f"cEdge_{i:03}"
            name = f"cEdge_{i:03}_{city_data[temp_name]['city']}"
            client_name = f"Site_{i:03}_Client"
            if i == 1:
                x = x_o
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i == 2:
                x = x_e
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i <= row_count:
                if i % 2 == 0:
                    x = x_e + 200 * e
                    client_x = x
                    drawing_x = x - 57
                    drawing_y = y - 55
                    e += 1
                else:
                    x = x_o + -200 * o
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                    o += 1
            else:
                if (i - 1) % row_count == 0:
                    e = 1
                    o = 1
                    y_modifier += 1
                    x_o = -557
                    x_e = 267
                if i % 2 == 0:
                    x = x_e + 200 * (e - 1)
                    e += 1
                    y = y_s + 300 * y_modifier
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o - 200 * (o - 1)
                    y = y_s + 300 * y_modifier
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            deploy_data[f"cedge_{i:03}_deploy_data"] = {"x": x, "y": y, "name": name}
            client_deploy_data[f"network_test_client_{i:03}_deploy_data"] = {"x": client_x, "y": client_y,
                                                                             "name": client_name}
            site_drawing_deploy_data[f"site_drawing_{i:03}_deploy_data"] = {
                "svg": "<svg height=\"267\" width=\"169\"><rect fill=\"#aaffff\" fill-opacity=\"1.0\" height=\"267\" stroke=\"#000000\" stroke-width=\"2\" width=\"169\" /></svg>",
                "x": drawing_x, "y": drawing_y, "z": 0}
    elif edge_count <= 25:
        row_count = 10
        y = -107
        y_s = -107
        for i in range(1, edge_count + 1):
            temp_name = f"cEdge_{i:03}"
            name = f"cEdge_{i:03}_{city_data[temp_name]['city']}"
            client_name = f"Site_{i:03}_Client"
            if i == 1:
                x = x_o
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i == 2:
                x = x_e
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i <= row_count:
                if i % 2 == 0:
                    x = x_e + 200 * e
                    e += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o + -200 * (o)
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            else:
                if (i - 1) % row_count == 0:
                    e = 1
                    o = 1
                    y_modifier += 1
                    x_o = -557
                    x_e = 267
                if i % 2 == 0:
                    x = x_e + 200 * (e - 1)
                    e += 1
                    y = y_s + 300 * y_modifier
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o - 200 * (o - 1)
                    y = y_s + 300 * y_modifier
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            deploy_data[f"cedge_{i:03}_deploy_data"] = {"x": x, "y": y, "name": name}
            client_deploy_data[f"network_test_client_{i:03}_deploy_data"] = {"x": client_x, "y": client_y,
                                                                             "name": client_name}
            site_drawing_deploy_data[f"site_drawing_{i:03}_deploy_data"] = {
                "svg": "<svg height=\"267\" width=\"169\"><rect fill=\"#aaffff\" fill-opacity=\"1.0\" height=\"267\" stroke=\"#000000\" stroke-width=\"2\" width=\"169\" /></svg>",
                "x": drawing_x, "y": drawing_y, "z": 0}
    elif edge_count <= 50:
        row_count = 10
        #y = -107
        #y_s = -107
        for i in range(1, edge_count + 1):
            temp_name = f"cEdge_{i:03}"
            name = f"cEdge_{i:03}_{city_data[temp_name]['city']}"
            client_name = f"Site_{i:03}_Client"
            if i == 1:
                x = x_o
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i == 2:
                x = x_e
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i <= row_count:
                if i % 2 == 0:
                    x = x_e + 200 * e
                    e += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o + -200 * (o)
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            else:
                if (i - 1) % row_count == 0:
                    e = 1
                    o = 1
                    y_modifier += 1
                    x_o = -557
                    x_e = 267
                if i % 2 == 0:
                    x = x_e + 200 * (e - 1)
                    e += 1
                    y = y_s + 300 * y_modifier
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o - 200 * (o - 1)
                    y = y_s + 300 * y_modifier
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            deploy_data[f"cedge_{i:03}_deploy_data"] = {"x": x, "y": y, "name": name}
            client_deploy_data[f"network_test_client_{i:03}_deploy_data"] = {"x": client_x, "y": client_y,
                                                                             "name": client_name}
            site_drawing_deploy_data[f"site_drawing_{i:03}_deploy_data"] = {
                "svg": "<svg height=\"267\" width=\"169\"><rect fill=\"#aaffff\" fill-opacity=\"1.0\" height=\"267\" stroke=\"#000000\" stroke-width=\"2\" width=\"169\" /></svg>",
                "x": drawing_x, "y": drawing_y, "z": 0}
    else:
        for i in range(1, edge_count + 1):
            temp_name = f"cEdge_{i:03}"
            name = f"cEdge_{i:03}_{city_data[temp_name]['city']}"
            client_name = f"Site_{i:03}_Client"
            if i == 1:
                x = x_o
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i == 2:
                x = x_e
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i <= row_count:
                if i % 2 == 0:
                    x = x_e + 200 * e
                    e += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o + -200 * o
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            else:
                if (i - 1) % row_count == 0:
                    e = 1
                    o = 1
                    y_modifier += 1
                    x_o = -557
                    x_e = 267
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                if i % 2 == 0:
                    x = x_e + 200 * (e - 1)
                    e += 1
                    y = y_s + 300 * y_modifier
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o - 200 * (o - 1)
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            deploy_data[f"cedge_{i:03}_deploy_data"] = {"x": x, "y": y, "name": name}
            client_deploy_data[f"network_test_client_{i:03}_deploy_data"] = {"x": client_x, "y": client_y,
                                                                             "name": client_name}
            site_drawing_deploy_data[f"site_drawing_{i:03}_deploy_data"] = {
                "svg": "<svg height=\"267\" width=\"169\"><rect fill=\"#aaffff\" fill-opacity=\"1.0\" height=\"267\" stroke=\"#000000\" stroke-width=\"2\" width=\"169\" /></svg>",
                "x": drawing_x, "y": drawing_y, "z": 0}
    return deploy_data, client_deploy_data, site_drawing_deploy_data
# endregion
# region Versa Specific
def generate_versa_network_objects(base_subnet, subnet_mask, site_index=1):
    network = ipaddress.IPv4Network(base_subnet)
    subnets_64 = list(network.subnets(new_prefix=subnet_mask))
    networks = []
    switch_limit = 1
    for subnet in subnets_64:
        if subnet.prefixlen == subnet_mask:
            if switch_limit == 45:
                break
            router_address = str(subnet.network_address + 1)
            vedge_address = str(subnet.network_address + 2)
            subnet_address = str(
                ipaddress.IPv4Interface(str(subnet.network_address) + '/' + str(subnet_mask)).netmask)
            subnet_address_long = str(vedge_address) + '/' + str(subnet_mask)
            network_dict = {
                'subnet': str(subnet.network_address),
                'subnet_mask': str(subnet.prefixlen),
                'subnet_address': subnet_address,
                'router_address': router_address,
                'flexvnf_address': subnet_address_long,
                'isp_switch_address': vedge_address,
                'flexvnf': f'FlexVNF-{site_index:003}'
            }
            networks.append(network_dict)
            site_index += 1
            switch_limit += 1
    return networks

def versa_generate_flexvnf_deploy_data(flexvnf_count, city_data):
    deploy_data = {}
    client_deploy_data = {}
    site_drawing_deploy_data = {}
    e = 1
    o = 1
    y_modifier = 0
    x_o = -557
    x_e = 267
    y = -554
    y_s = -554
    row_count = 20

    client_x = 0
    client_y = 0
    client_y_modifier = 115

    drawing_x = 0
    drawing_y = 0
    drawing_x_modifier = 200

    if flexvnf_count <= 10:
        row_count = 4
        y = -107
        y_s = -107
        for i in range(1, flexvnf_count + 1):
            temp_name = f"FlexVNF-{i:03}"
            name = f"FlexVNF-{i:03}-{city_data[temp_name]['city']}"
            client_name = f"Site_{i:03}_Client"
            if i == 1:
                x = x_o
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i == 2:
                x = x_e
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i <= row_count:
                if i % 2 == 0:
                    x = x_e + 200 * e
                    client_x = x
                    drawing_x = x - 57
                    drawing_y = y - 55
                    e += 1
                else:
                    x = x_o + -200 * o
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                    o += 1
            else:
                if (i - 1) % row_count == 0:
                    e = 1
                    o = 1
                    y_modifier += 1
                    x_o = -557
                    x_e = 267
                if i % 2 == 0:
                    x = x_e + 200 * (e - 1)
                    e += 1
                    y = y_s + 300 * y_modifier
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o - 200 * (o - 1)
                    y = y_s + 300 * y_modifier
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            deploy_data[f"flexvnf_{i:03}_deploy_data"] = {"x": x, "y": y, "name": name}
            client_deploy_data[f"network_test_client_{i:03}_deploy_data"] = {"x": client_x, "y": client_y,
                                                                             "name": client_name}
            site_drawing_deploy_data[f"site_drawing_{i:03}_deploy_data"] = {
                "svg": "<svg height=\"267\" width=\"169\"><rect fill=\"#aaffff\" fill-opacity=\"1.0\" height=\"267\" stroke=\"#000000\" stroke-width=\"2\" width=\"169\" /></svg>",
                "x": drawing_x, "y": drawing_y, "z": 0}
    elif flexvnf_count <= 20:
        row_count = 10
        y = -107
        y_s = -107
        for i in range(1, flexvnf_count + 1):
            temp_name = f"FlexVNF-{i:03}"
            name = f"FlexVNF-{i:03}-{city_data[temp_name]['city']}"
            client_name = f"Site_{i:03}_Client"
            if i == 1:
                x = x_o
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i == 2:
                x = x_e
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i <= row_count:
                if i % 2 == 0:
                    x = x_e + 200 * e
                    e += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o + -200 * (o)
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            else:
                if (i - 1) % row_count == 0:
                    e = 1
                    o = 1
                    y_modifier += 1
                    x_o = -557
                    x_e = 267
                if i % 2 == 0:
                    x = x_e + 200 * (e - 1)
                    e += 1
                    y = y_s + 300 * y_modifier
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o - 200 * (o - 1)
                    y = y_s + 300 * y_modifier
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            deploy_data[f"flexvnf_{i:03}_deploy_data"] = {"x": x, "y": y, "name": name}
            client_deploy_data[f"network_test_client_{i:03}_deploy_data"] = {"x": client_x, "y": client_y,
                                                                             "name": client_name}
            site_drawing_deploy_data[f"site_drawing_{i:03}_deploy_data"] = {
                "svg": "<svg height=\"267\" width=\"169\"><rect fill=\"#aaffff\" fill-opacity=\"1.0\" height=\"267\" stroke=\"#000000\" stroke-width=\"2\" width=\"169\" /></svg>",
                "x": drawing_x, "y": drawing_y, "z": 0}
    else:
        for i in range(1, flexvnf_count + 1):
            temp_name = f"FlexVNF-{i:03}"
            name = f"FlexVNF-{i:03}-{city_data[temp_name]['city']}"
            client_name = f"Site_{i:03}_Client"
            if i == 1:
                x = x_o
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i == 2:
                x = x_e
                client_x = x
                client_y = y + client_y_modifier
                drawing_x = x - 55
                drawing_y = y - 55
            elif i <= row_count:
                if i % 2 == 0:
                    x = x_e + 200 * e
                    e += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o + -200 * o
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            else:
                if (i - 1) % row_count == 0:
                    e = 1
                    o = 1
                    y_modifier += 1
                    x_o = -557
                    x_e = 267
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                if i % 2 == 0:
                    x = x_e + 200 * (e - 1)
                    e += 1
                    y = y_s + 300 * y_modifier
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
                else:
                    x = x_o - 200 * (o - 1)
                    o += 1
                    client_x = x
                    client_y = y + client_y_modifier
                    drawing_x = x - 55
                    drawing_y = y - 55
            deploy_data[f"flexvnf_{i:03}_deploy_data"] = {"x": x, "y": y, "name": name}
            client_deploy_data[f"network_test_client_{i:03}_deploy_data"] = {"x": client_x, "y": client_y,
                                                                             "name": client_name}
            site_drawing_deploy_data[f"site_drawing_{i:03}_deploy_data"] = {
                "svg": "<svg height=\"267\" width=\"169\"><rect fill=\"#aaffff\" fill-opacity=\"1.0\" height=\"267\" stroke=\"#000000\" stroke-width=\"2\" width=\"169\" /></svg>",
                "x": drawing_x, "y": drawing_y, "z": 0}
    return deploy_data, client_deploy_data, site_drawing_deploy_data

def generate_flexvnf_objects(vedge_count, mgmt_base_subnet):
    subnet_mask = 24
    k = 101
    networks = []
    for i in range(1, vedge_count + 1):
        base_subnet = f'172.16.{k}.0/24'
        network = ipaddress.IPv4Network(base_subnet)
        subnets_64 = list(network.subnets(new_prefix=subnet_mask))
        for subnet in subnets_64:
            if subnet.prefixlen == subnet_mask:
                router_address = str(subnet.network_address + 1)
                vedge_address = str(subnet.network_address + 2)
                subnet_address_full = str(
                    ipaddress.IPv4Interface(str(subnet.network_address) + '/' + str(subnet_mask)).netmask)
                subnet_address_var = str(subnet.network_address) + '/' + str(subnet_mask)
                subnet_base_var = str(subnet.network_address)
                dhcp_exclude_var = str(subnet.network_address + 1) + '-' + str(subnet.network_address + 50)
                client_1_address_var = str(subnet.network_address + 51)
                network_dict = {
                    'lan_subnet_base': subnet_base_var.rstrip(".0"),
                    'lan_subnet_address': subnet_address_var,
                    'lan_gateway_address': f'{router_address}/24',
                    'lan_dhcp_pool': f'{vedge_address}/24',
                    'lan_dhcp_exclude': dhcp_exclude_var,
                    'client_1_address': client_1_address_var,
                    'flexvnf': f'FlexVNF-{i:003}',
                    'system_ip': f'{mgmt_base_subnet}.{i + 100}',
                    'mgmt_address': f'{mgmt_base_subnet}.{i + 100}',
                    'mgmt_gateway': f'{mgmt_base_subnet}.1',
                    'site_id': k,
                    'org_name': 'sdwan-lab'
                }
            networks.append(network_dict)
            k += 1
    # logging.info(networks)
    return networks

def generate_versa_interfaces_file(interface_data_1, router_index, interface_data_2, interface_data_3, filename_temp):
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), '../configs/')
    filename = os.path.join(configs_path, filename_temp)
    with open(filename, 'w') as f:
        eth_1 = 0
        eth_2 = 0
        f.write(f'#{filename}\n')
        f.write('auto eth0\n')
        f.write('iface eth0 inet static\n')
        # f.write(f'\taddress {interface_data_1[router_index]["isp_switch_address"]}\n')
        # f.write(f'\tnetmask {interface_data_1[router_index]["subnet_address"]}\n')
        # f.write(f'\tgateway {interface_data_1[router_index]["router_address"]}\n')
        f.write(f'\taddress 192.168.122.251\n')
        f.write(f'\tnetmask 255.255.255.0\n')
        f.write(f'\tgateway 192.168.122.1\n')
        f.write('\tup echo nameserver 192.168.122.1 > /etc/resolv.conf\n\n')
        f.write('auto eth1\n')
        f.write('iface eth1 inet static\n')
        if filename_temp == "cloud_isp_switch_0_interfaces":
            f.write(f'\taddress 172.16.5.1\n')
            f.write(f'\tnetmask 255.255.255.252\n')
            f.write('auto eth2\n')
            f.write('iface eth2 inet static\n')
            f.write(f'\taddress 172.16.5.5\n')
            f.write(f'\tnetmask 255.255.255.252\n')
            f.write('auto eth3\n')
            f.write('iface eth3 inet static\n')
            f.write(f'\taddress 172.16.5.9\n')
            f.write(f'\tnetmask 255.255.255.252\n')
        for i in range(5, 49):
            f.write(f'#{interface_data_2[eth_1]["flexvnf"]} interface ge0/0\n')
            f.write(f'auto eth{i}\n')
            f.write(f'iface eth{i} inet static\n')
            f.write(f'\taddress {interface_data_2[eth_1]["router_address"]}\n')
            f.write(f'\tnetmask {interface_data_2[eth_1]["subnet_address"]}\n')
            f.write('\n')
            eth_1 += 1
        for i in range(51, 95):
            f.write(f'#{interface_data_3[eth_2]["flexvnf"]} interface ge0/1\n')
            f.write(f'auto eth{i}\n')
            f.write(f'iface eth{i} inet static\n')
            f.write(f'\taddress {interface_data_3[eth_2]["router_address"]}\n')
            f.write(f'\tnetmask {interface_data_3[eth_2]["subnet_address"]}\n')
            f.write('\n')
            eth_2 += 1
    logging.info(f"Deploy - Created file {filename_temp}")
# endregion
# region Arista Specific
def generate_arista_interfaces_file(filename_temp, mgmt_network_address, ip_var):
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), '../configs/')
    filename = os.path.join(configs_path, filename_temp)

    with open(filename, 'w') as f:
        f.write('auto eth0\n')
        f.write('iface eth0 inet static\n')
        f.write(f'\taddress {ip_var}\n')
        f.write('\tnetmask 255.255.255.0\n\n')
        f.write(f'\tgateway {mgmt_network_address}1\n')

    logging.info(f"Deploy - Created file {filename_temp}")

# endregion
# region Old
def generate_isp_deploy_data(num_nodes):
    deploy_data = {}
    x = -154
    y = 51

    for i in range(1, num_nodes + 1):
        name = f"Cloud_ISP_{i:03}"
        y += 75
        deploy_data[f"isp_{i:03}_deploy_data"] = {"x": x, "y": y, "name": name}

    return deploy_data
def generate_interfaces_file_old(interface_data_1, router_index, interface_data_2, interface_data_3, filename_temp):
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), '../configs/')
    filename = os.path.join(configs_path, filename_temp)
    with open(filename, 'w') as f:
        eth_1 = 0
        eth_2 = 0
        f.write(f'#{filename}\n')
        f.write('auto eth0\n')
        f.write('iface eth0 inet static\n')
        f.write(f'\taddress {interface_data_1[router_index]["isp_switch_address"]}\n')
        f.write(f'\tnetmask {interface_data_1[router_index]["subnet_address"]}\n')
        f.write(f'\tgateway {interface_data_1[router_index]["router_address"]}\n')
        f.write('\tup echo nameserver 192.168.122.1 > /etc/resolv.conf\n\n')
        f.write('auto eth1\n')
        f.write('iface eth1 inet static\n')
        if filename_temp == "cloud_isp_switch_0_interfaces":
            f.write(f'\taddress 172.16.4.1\n')
            f.write(f'\tnetmask 255.255.255.252\n')
            f.write('auto eth2\n')
            f.write('iface eth2 inet static\n')
            f.write(f'\taddress 172.16.4.5\n')
            f.write(f'\tnetmask 255.255.255.252\n')
            f.write('auto eth3\n')
            f.write('iface eth3 inet static\n')
            f.write(f'\taddress 172.16.4.9\n')
            f.write(f'\tnetmask 255.255.255.252\n')
        for i in range(5, 49):
            f.write(f'#{interface_data_2[eth_1]["vedge"]} interface ge0/0\n')
            f.write(f'auto eth{i}\n')
            f.write(f'iface eth{i} inet static\n')
            f.write(f'\taddress {interface_data_2[eth_1]["router_address"]}\n')
            f.write(f'\tnetmask {interface_data_2[eth_1]["subnet_address"]}\n')
            f.write('\n')
            eth_1 += 1
        for i in range(51, 95):
            f.write(f'#{interface_data_3[eth_2]["vedge"]} interface ge0/1\n')
            f.write(f'auto eth{i}\n')
            f.write(f'iface eth{i} inet static\n')
            f.write(f'\taddress {interface_data_3[eth_2]["router_address"]}\n')
            f.write(f'\tnetmask {interface_data_3[eth_2]["subnet_address"]}\n')
            f.write('\n')
            eth_2 += 1
    logging.info(f"Deploy - Created file {filename_temp}")

def generate_interfaces_file_old_1(vmanage_gateway_ip, vsmart_gateway_ip, vbond_gateway_ip, interface_data_2,
                                 interface_data_3, filename_temp):
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), '../configs/')
    filename = os.path.join(configs_path, filename_temp)
    with open(filename, 'w') as f:
        eth_1 = 0
        eth_2 = 0
        f.write(f'#{filename}\n')
        f.write('auto eth0\n')
        f.write('iface eth0 inet static\n')
        f.write(f'\taddress 192.168.122.250\n')
        f.write(f'\tnetmask 255.255.255.0\n')
        f.write(f'\tgateway 192.168.122.1\n')
        f.write('\tup echo nameserver 192.168.122.1 > /etc/resolv.conf\n\n')
        f.write('auto eth1\n')
        f.write('iface eth1 inet static\n')
        if filename_temp == "cloud_isp_switch_0_interfaces":
            f.write(f'\taddress {vmanage_gateway_ip}\n')
            f.write(f'\tnetmask 255.255.255.252\n')
            f.write('auto eth2\n')
            f.write('iface eth2 inet static\n')
            f.write(f'\taddress {vsmart_gateway_ip}\n')
            f.write(f'\tnetmask 255.255.255.252\n')
            f.write('auto eth3\n')
            f.write('iface eth3 inet static\n')
            f.write(f'\taddress {vbond_gateway_ip}\n')
            f.write(f'\tnetmask 255.255.255.252\n')
        for i in range(5, 49):
            f.write(f'#{interface_data_2[eth_1]["vedge"]} interface ge0/0\n')
            f.write(f'auto eth{i}\n')
            f.write(f'iface eth{i} inet static\n')
            f.write(f'\taddress {interface_data_2[eth_1]["router_address"]}\n')
            f.write(f'\tnetmask {interface_data_2[eth_1]["subnet_address"]}\n')
            f.write('\n')
            eth_1 += 1
        for i in range(51, 95):
            f.write(f'#{interface_data_3[eth_2]["vedge"]} interface ge0/1\n')
            f.write(f'auto eth{i}\n')
            f.write(f'iface eth{i} inet static\n')
            f.write(f'\taddress {interface_data_3[eth_2]["router_address"]}\n')
            f.write(f'\tnetmask {interface_data_3[eth_2]["subnet_address"]}\n')
            f.write('\n')
            eth_2 += 1
    logging.info(f"Deploy - Created file {filename_temp}")
# endregion
