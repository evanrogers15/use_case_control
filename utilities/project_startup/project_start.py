import subprocess

def run_command(cmd):
    """
    Runs the given command in a subprocess.
    """
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        print(f"Error executing command: {cmd}")
        print(stderr.decode())
    else:
        print(stdout.decode())

def main():
    commands = [
        "python3 start_nodes_utility.py 192.168.122.1 80 multivendor-sdwan start bgp,isp,Versa,FlexVNF,sw-core,sw-dist,sw-acc,Client,Server,Tix",
        "python3 latency_utility.py 192.168.122.1 80 multivendor-sdwan add bgp",
        "python3 latency_utility.py 192.168.122.1 80 multivendor-sdwan add isp-houston",
        "python3 bandwidth_utility.py 192.168.122.1 80 multivendor-sdwan add isp-newyork eth2 50",
        "python3 bandwidth_utility.py 192.168.122.1 80 multivendor-sdwan add isp-newyork eth3 50",
        "python3 bandwidth_utility.py 192.168.122.1 80 multivendor-sdwan add isp-seattle eth2 50",
        "python3 bandwidth_utility.py 192.168.122.1 80 multivendor-sdwan add isp-seattle eth3 50",
        "python3 bandwidth_utility.py 192.168.122.1 80 multivendor-sdwan add isp-sanfran eth2 50",
        "python3 bandwidth_utility.py 192.168.122.1 80 multivendor-sdwan add isp-sanfran eth3 50",
        "python3 bandwidth_utility.py 192.168.122.1 80 multivendor-sdwan add isp-atlanta eth2 50",
        "python3 bandwidth_utility.py 192.168.122.1 80 multivendor-sdwan add isp-atlanta eth3 50",
        "python3 bandwidth_utility.py 192.168.122.1 80 multivendor-sdwan add isp-miami eth2 50",
        "python3 bandwidth_utility.py 192.168.122.1 80 multivendor-sdwan add isp-miami eth3 50",
        "python3 bandwidth_utility.py 192.168.122.1 80 multivendor-sdwan add isp-chicago eth2 50",
        "python3 bandwidth_utility.py 192.168.122.1 80 multivendor-sdwan add isp-chicago eth3 50",
        "python3 bandwidth_utility.py 192.168.122.1 80 multivendor-sdwan add isp-houston eth0 50",
        "python3 start_nodes_utility.py 192.168.122.1 80 multivendor-sdwan start ISP_Router",
        "python3 isp_route_utility.py 192.168.122.1 80 multivendor-sdwan ISP_Router",
        "python3 start_nodes_utility.py 192.168.122.1 80 multivendor-sdwan start vk35,vManage,vBond,vSmart,vEdge",
    ]

    for cmd in commands:
        print(f'Running command {cmd}..')
        run_command(cmd)

if __name__ == "__main__":
    main()
