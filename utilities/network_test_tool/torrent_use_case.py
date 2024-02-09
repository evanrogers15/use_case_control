import argparse
import subprocess
import time
import random
import socket
import fcntl
import struct
import multiprocessing
import os
import signal
from datetime import datetime, timedelta

def get_ip_address(interface):
    # Get the IP address of the specified interface
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        ip_address = socket.inet_ntoa(fcntl.ioctl(
            sock.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', interface[:15].encode())
        )[20:24])
        return ip_address
    except IOError:
        return None

PORTS = [80, 443, 21, 23]

def start_iperf_server_session(client_ip, port):
    server_log_file = f'iperf3_server_port_{port}.log'
    delete_file(server_log_file)
    server_cmd = ['iperf3', '-s', '--logfile', server_log_file, '-p', str(port)]
    subprocess.Popen(server_cmd, stderr=subprocess.STDOUT, universal_newlines=True)

def start_iperf_server_sessions(other_clients):
    processes = []
    for idx, client in enumerate(other_clients):
        port = PORTS[idx % len(PORTS)]
        process = multiprocessing.Process(target=start_iperf_server_session, args=(client['ip'], port))
        process.start()
        processes.append(process)
    return processes

def start_iperf_client_sessions(other_clients, local_ip, duration):
    for client in other_clients:
        if client ['ip'] != local_ip:
            random_port = random.choice(PORTS)  # Choose a random port for each client
            bandwidth = random.randint(40000, 70000)  # kbps


            client_log_file = f'iperf3_client_{client ["ip"]}.log'
            delete_file(client_log_file)
            client_cmd = ['iperf3', '-c', client ['ip'], '-p', str(random_port), '--logfile', client_log_file, '-u', '-b', '100M', '-t',
                          str(duration) ,'-R']
            subprocess.Popen(client_cmd, stderr=subprocess.STDOUT, universal_newlines=True)

def terminate_iperf_server_sessions(server_processes):
    for process in server_processes:
        process.terminate()
        process.join()

def delete_and_recreate_file(file_path):
    # Delete the file if it exists and create a new empty file
    if os.path.exists(file_path):
        os.remove(file_path)
    open(file_path, 'a').close()

def delete_file(file_path):
    # Delete the file if it exists and create a new empty file
    if os.path.exists(file_path):
        os.remove(file_path)

def main(ports):
    # Use the ports list provided by the user
    global PORTS
    PORTS = ports
    # Get the IP address of the eth0 interface
    eth0_ip = get_ip_address('eth0')

    # Generate a list of client IP addresses
    clients = [{'ip': f'12.2.238.102'}]

    run_count = 0

    try:
        while run_count <= 50:
            duration = random.randint(60, 100)  # seconds

            interval_delay = duration + random.randint(10, 30)
            # Start iperf3 client sessions
            start_iperf_client_sessions(clients, eth0_ip, duration)

            time.sleep(interval_delay)
            run_count += 1

    except KeyboardInterrupt:
        # Clean up when interrupted
        print("Exiting..")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # parser.add_argument('sites', help='The type of test to be run, currently only "sites" is supported')
    # parser.add_argument('num_clients', type=int, help='Number of iperf3 clients to start')
    parser.add_argument('ports', type=lambda s: [int(item) for item in s.split(',')], help='Ports to use, separated by commas e.g. 21,22,23,80,443')
    args = parser.parse_args()

    main(args.ports)