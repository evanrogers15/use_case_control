import requests
import json
import telnetlib
import time
import socket

from modules.gns3.gns3_actions import *

def appneta_cli_curl_commands(server_ip, server_port, server_name, project_id, project_name, deployment_type, node_id, console_port, node_name, appn_password, mp_ip_address, appn_site_key, appn_url, mp_lan_address=None, mp_lan_gateway=None):
    tn = telnetlib.Telnet(server_ip, console_port)
    deployment_step = 'AppNeta Monitoring Point Setup'
    user = "admin"
    set_eth2_command = f'curl -k -u admin:525400E00000 -X POST -H "Content-Type: application/json" -d \'{{"name": "eth2", "family": "inet", "method": "static", "address": "{mp_ip_address}", "netmask": "255.255.255.0"}}\' \'https://127.0.0.1/api/v1/interface/\''
    set_hostname_command = f'curl -k -u admin:525400E00000 -X PUT -H "Content-Type: application/json" -H "Accept: application/json" -d \'{{"hostname": "{node_name}"}}\' "https://127.0.0.1/api/v1/hostname/"'
    set_nis_command = f'curl -k -u admin:525400E00000 -X POST -H "Content-Type: application/json" -d \'{{"address": "{appn_url}", "site_key": "{appn_site_key}", "ports": "80,8080", "relay_addresses": "{appn_url}:443", "ssl": "true", "protocol": "TCP"}}\' "https://127.0.0.1/api/v1/nis/?restart_services=true"'
    set_password_command = f'curl -k -u admin:525400E00000 -X PUT -H "Content-Type: application/json" -H "Accept: application/json" -d \'{{"password": "PW4netops!"}}\' "https://127.0.0.1/api/v1/appliance/password/"'
    log_and_update_db(server_name, project_name, deployment_type, 'running', deployment_step, f"Starting configuration on {node_name}")
    loop_index = 0
    tn.write(b"\r\n")
    while True:
        tn.write(b"\r\n")
        tn.read_until(b"login:", timeout=1)
        tn.write(user.encode("ascii") + b"\n")
        output = tn.read_until(b"Password:", timeout=3)
        if b"Password:" in output:
            tn.write(appn_password.encode("ascii") + b"\n")
            break
        log_and_update_db(server_name, 'project_name', "deployment_type", 'running',
                              deployment_step,
                              f"{node_name} not available yet, trying again in 30 seconds..")
        time.sleep(30)
    tn.read_until(b"admin@vk25")
    tn.write(b'echo "vk35-r01" > /var/lib/pathview/ma-platform.force\n')
    tn.read_until(b"$ ")
    if deployment_type == 'test':
        set_eth0_command = f'curl -k -u admin:525400E00000 -X POST -H "Content-Type: application/json" -d \'{{"name": "eth0", "family": "inet", "method": "static", "address": "{mp_lan_address}", "netmask": "255.255.255.0", "gateway": "{mp_lan_gateway}"}}\' \'https://127.0.0.1/api/v1/interface/\''
        tn.write(set_eth0_command.encode('ascii') + b"\n")
        tn.read_until(b'status":')
    tn.write(set_eth2_command.encode('ascii') + b"\n")
    tn.read_until(b'status":')
    tn.write(set_hostname_command.encode('ascii') + b"\n")
    tn.read_until(b'status":')
    # tn.write(set_eth2_command.encode('ascii') + b"\n")
    # tn.read_until(b'status":')
    tn.write(b'sudo reboot\n')
    tn.write(appn_password.encode("ascii") + b"\n")
    log_and_update_db(server_name, project_name, deployment_type, 'running', deployment_step,
                      f"Rebooting {node_name}...")
    # gns3_restart_node(server_ip, server_port, project_id, node_id)
    tn.read_until(b"$ ")
    # tn.close()
    time.sleep(120)
    while True:
        if loop_index == 5:
            gns3_restart_node(server_ip, server_port, project_id, node_id)
            log_and_update_db(server_name, 'project_name', "deployment_type", 'running', deployment_step,
                              f"{node_name} being rebooted again due to prompt issue.. Trying again in 2 mins..")
            time.sleep(120)
            loop_index = 0
        tn = telnetlib.Telnet(server_ip, console_port)
        tn.write(b"\r\n")
        tn.read_until(b"login:", timeout=1)
        tn.write(user.encode("ascii") + b"\n")
        output = tn.read_until(b"Password:", timeout=3)
        if b"Password:" in output:
            tn.write(appn_password.encode("ascii") + b"\n")
            break
        log_and_update_db(server_name, 'project_name', "deployment_type", 'running',
                              deployment_step,
                              f"{node_name} not available yet, trying again in 30 seconds..")
        tn.close()
        time.sleep(30)
        loop_index += 1
    log_and_update_db(server_name, project_name, deployment_type, 'running', deployment_step,
                      f"Setting AppNeta NIS on {node_name}")
    tn.write(set_nis_command.encode('ascii') + b"\n")
    tn.read_until(b'status":')
    tn.write(set_password_command.encode('ascii') + b"\n")
    tn.read_until(b'status":')
    log_and_update_db(server_name, project_name, deployment_type, 'running', deployment_step,
                      f"Completed configuration on {node_name}")
    tn.close()
