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
        "python3 /app/utilities/project_startup/start_nodes_utility.py 192.168.122.1 80 velocloud-lab start bgp,isp,Versa,FlexVNF,sw-core,sw-dist,sw-acc,Client,Server,Tix",
        "python3 /app/utilities/project_startup/latency_utility.py 192.168.122.1 80 velocloud-lab add bgp",
        "python3 /app/utilities/project_startup/latency_utility.py 192.168.122.1 80 velocloud-lab add isp-houston",
        "python3 /app/utilities/project_startup/bandwidth_utility.py 192.168.122.1 80 velocloud-lab add isp-newyork",
        "python3 /app/utilities/project_startup/bandwidth_utility.py 192.168.122.1 80 velocloud-lab add isp-seattle",
        "python3 /app/utilities/project_startup/bandwidth_utility.py 192.168.122.1 80 velocloud-lab add isp-sanfran",
        "python3 /app/utilities/project_startup/bandwidth_utility.py 192.168.122.1 80 velocloud-lab add isp-atlanta",
        "python3 /app/utilities/project_startup/bandwidth_utility.py 192.168.122.1 80 velocloud-lab add isp-miami",
        "python3 /app/utilities/project_startup/bandwidth_utility.py 192.168.122.1 80 velocloud-lab add isp-chicago",
        "python3 /app/utilities/project_startup/start_nodes_utility.py 192.168.122.1 80 velocloud-lab start ISP_Router",
        "python3 /app/utilities/project_startup/isp_route_utility.py 192.168.122.1 80 velocloud-lab ISP_Router",
    ]

    for cmd in commands:
        print(f'Running command {cmd}..')
        run_command(cmd)

if __name__ == "__main__":
    main()
