import logging
logging.basicConfig(filename='app.log', level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

processes = {}

db_path = 'gns3.db'

deployment_type = ''
deployment_status = ''
deployment_step = ''

# region Viptela Variables
viptela_username = 'admin'
viptela_old_password = "admin"
viptela_password = 'PW4netops'
org_name = 'sdwan-lab'
switchport_count = 95

versa_director_username = 'Administrator'
versa_old_password = "versa123"
versa_analytics_username = "admin"
versa_flexvnf_username = "admin"

mgmt_switchport_count = 45
mgmt_main_switchport_count = 30

appneta_mp_mac = "525400E00000"
# endregion

# region Variables: GNS3 Template Data
headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}

client_filename = 'client_interfaces'
client_node_file_path = 'etc/network/interfaces'

vmanage_template_name = 'vManage'
vbond_template_name = 'vBond'
vsmart_template_name = 'vSmart'
vedge_template_name = 'vEdge'
cedge_template_name = 'c8000v'
open_vswitch_cloud_template_name = 'Open_vSwitch_Cloud'
open_vswitch_isp_template_name = 'Open_vSwitch_ISP'
network_test_tool_template_name = 'Network_Test_Tool'
cisco_l3_router_template_name = 'Cisco IOU L3 155-2T'
mgmt_hub_template_name = 'MGMT_Hub'
mgmt_main_hub_template_name = 'Main-MGMT-Switch'
arista_veos_template_name = 'arista_switch'
arista_ceos_template_name = 'arista_ceos'
fortinet_fortigate_template_name = 'Fortigate 7.0.5'
versa_director_template_name = 'Versa Director 21.2.3'
versa_analytics_template_name = 'Versa Analytics 21.2.3'
versa_flexvnf_template_name = 'Versa FlexVNF 21.2.3'

# region Viptela Template Data
viptela_vmanage_template_data = {"compute_id": "local", "cpus": 16, "adapters": 6,
                                 "symbol": ":/symbols/affinity/circle/blue/server_cluster.svg",
                                 "adapter_type": "vmxnet3", "qemu_path": "/usr/bin/qemu-system-x86_64",
                                 "hda_disk_image": "viptela-vmanage-li-20.10.1-genericx86-64.qcow2",
                                 "hdb_disk_image": "empty30G.qcow2", "name": vmanage_template_name, "ram": 32768,
                                 "template_type": "qemu", "hda_disk_interface": "virtio",
                                 "hdb_disk_interface": "virtio", "options": "-cpu host -smp 2,maxcpus=2"}
viptela_vsmart_template_data = {"compute_id": "local", "cpus": 2, "adapters": 3,
                                "symbol": ":/symbols/affinity/circle/blue/interconnect.svg",
                                "adapter_type": "vmxnet3", "qemu_path": "/usr/bin/qemu-system-x86_64",
                                "hda_disk_image": "viptela-smart-li-20.10.1-genericx86-64.qcow2",
                                "name": vsmart_template_name, "ram": 4096, "template_type": "qemu",
                                "hda_disk_interface": "virtio", "options": "-cpu host"}
viptela_vbond_template_data = {"compute_id": "local", "cpus": 2, "adapters": 3,
                               "symbol": ":/symbols/affinity/circle/blue/isdn.svg", "adapter_type": "vmxnet3",
                               "qemu_path": "/usr/bin/qemu-system-x86_64",
                               "hda_disk_image": "viptela-edge-20.10.1-genericx86-64.qcow2",
                               "name": vbond_template_name, "ram": 2048, "template_type": "qemu",
                               "hda_disk_interface": "virtio", "options": "-cpu host"}
viptela_vedge_template_data = {"compute_id": "local", "cpus": 1, "adapters": 6,
                               "symbol": ":/symbols/affinity/square/blue/communications.svg",
                               "adapter_type": "vmxnet3", "qemu_path": "/usr/bin/qemu-system-x86_64",
                               "hda_disk_image": "viptela-edge-20.10.1-genericx86-64.qcow2",
                               "name": vedge_template_name, "ram": 2048, "template_type": "qemu",
                               "hda_disk_interface": "virtio", "options": "-cpu host -smp 2,maxcpus=2"}
viptela_cedge_template_data = {"compute_id": "local", "cpus": 2, "adapters": 6,
                               "symbol": ":/symbols/affinity/square/blue/communications.svg",
                               "adapter_type": "vmxnet3", "qemu_path": "/usr/bin/qemu-system-x86_64",
                               "hda_disk_image": "c8000v-universalk9_8G_serial.17.09.01a.qcow2",
                               "name": cedge_template_name, "ram": 4096, "template_type": "qemu",
                               "hda_disk_interface": "ide", "options": "-cpu host -smp 2,maxcpus=2"}

openvswitch_template_data = {"compute_id": "local", "adapters": 16, "category": "switch",
                             "image": "gns3/ovs-snmp:latest", "name": "Open vSwitch",
                             "symbol": ":/symbols/classic/multilayer_switch.svg", "template_type": "docker",
                             "usage": "By default all interfaces are connected to the br0"}
openvswitch_cloud_template_data = {"compute_id": "local", "adapters": switchport_count, "category": "switch",
                                   "image": "gns3/ovs-snmp:latest", "name": open_vswitch_cloud_template_name,
                                   "symbol": ":/symbols/cloud.svg", "template_type": "docker",
                                   "usage": "By default all interfaces are connected to the br0"}
openvswitch_isp_template_data = {"compute_id": "local", "adapters": switchport_count, "category": "switch",
                                   "image": "evanrogers719/ovs-snmp-nat:latest", "name": open_vswitch_isp_template_name,
                                   "symbol": ":/symbols/cloud.svg", "template_type": "docker",
                                   "usage": "By default all interfaces are connected to the br0", "start_command": "./bin/boot.sh", "extra_volumes": ["/etc/openvswitch/"]}
network_test_tool_template_data = {"compute_id": "local", "adapters": 2, "category": "guest",
                                   "image": "evanrogers719/network_test_tool:latest",
                                   "name": network_test_tool_template_name, "symbol": ":/symbols/docker_guest.svg",
                                   "template_type": "docker"}
cisco_l3_router_template_data = {"compute_id": "local", "path": "L3-ADVENTERPRISEK9-M-15.5-2T.bin", "nvram": 256,
                                 "ram": 512, "symbol": ":/symbols/classic/router.svg", "template_type": "iou",
                                 "use_default_iou_values": True, "ethernet_adapters": 2, "serial_adapters": 0,
                                 "name": cisco_l3_router_template_name,
                                 "startup_config": "iou_l3_base_startup-config.txt"}
fortinet_fortigate_template_data = {"compute_id": "local", "cpus": 4, "adapters": 10, "adapter_type": "e1000",
                                    "qemu_path": "/usr/bin/qemu-system-x86_64",
                                    "hda_disk_image": "FGT_VM64_KVM-v7.0.5.F-FORTINET.out.kvm.qcow2",
                                    "hdb_disk_image": "empty30G.qcow2", "name": fortinet_fortigate_template_name,
                                    "ram": 2048, "template_type": "qemu", "hda_disk_interface": "virtio",
                                    "hdb_disk_interface": "virtio"}
arista_veos_template_data = {"compute_id": "local", "cpus": 2, "adapters": 20, "adapter_type": "e1000",
                             "qemu_path": "/usr/bin/qemu-system-x86_64", "hda_disk_image": "cdrom.iso",
                             "hdb_disk_image": "vEOS-lab-4.28.0F.qcow2",
                             "name": arista_veos_template_name,
                             "ram": 2048, "template_type": "qemu", "hda_disk_interface": "ide",
                             "hdb_disk_interface": "ide", "options": "-cpu host"}
arista_ceos_old_template_data = {"compute_id": "local", "adapters": 20, "category": "router",
                                 "image": "ceosimage:4.26.0.1F", "name": arista_ceos_template_name,
                                 "symbol": ":/symbols/classic/multilayer_switch.svg", "template_type": "docker",
                                 "usage": "By default all interfaces are connected to the br0",
                                 "start_command": "/sbin/init systemd.setenv=INTFTYPE=eth systemd.setenv=ETBA=1 systemd.setenv=SKIP_ZEROTOUCH_BARRIER_IN_SYSDBINIT=1 systemd.setenv=CEOS=1 systemd.setenv=EOS_PLATFORM=ceoslab systemd.setenv=container=docker",
                                 "environment": "INTFTYPE=eth\nETBA=1 \nSKIP_ZEROTOUCH_BARRIER_IN_SYSDBINIT=1 \nCEOS=1 \nEOS_PLATFORM=ceoslab \ncontainer=docker\nMAPETH0=1\nMGMTINF=eth0", }

arista_ceos_template_data = {"compute_id": "local", "adapters": 20, "category": "router",
                             "image": "ceosimage:4.28.6.1M", "name": arista_ceos_template_name,
                             "symbol": ":/symbols/classic/multilayer_switch.svg", "template_type": "docker",
                             "usage": "By default all interfaces are connected to the br0",
                             "start_command": "/sbin/init systemd.setenv=INTFTYPE=eth systemd.setenv=ETBA=1 systemd.setenv=SKIP_ZEROTOUCH_BARRIER_IN_SYSDBINIT=1 systemd.setenv=CEOS=1 systemd.setenv=EOS_PLATFORM=ceoslab systemd.setenv=container=docker",
                             "environment": "INTFTYPE=eth\nETBA=1 \nSKIP_ZEROTOUCH_BARRIER_IN_SYSDBINIT=1 \nCEOS=1 \nEOS_PLATFORM=ceoslab \ncontainer=docker\nMAPETH0=1\nMGMTINF=eth0", }
# endregion
versa_director_template_data = {"compute_id": "local", "cpus": 16, "adapters": 6,
                                 "symbol": ":/symbols/affinity/circle/blue/server_cluster.svg",
                                 "adapter_type": "virtio-net-pci", "qemu_path": "/usr/bin/qemu-system-x86_64",
                                 "hda_disk_image": "versa-director-c19c43c-21.2.3.qcow2",
                                 "name": versa_director_template_name, "ram": 16384,
                                 "template_type": "qemu", "hda_disk_interface": "virtio",
                                 "options": "-cpu host -smp 2,maxcpus=2"}
versa_analytics_template_data = {"compute_id": "local", "cpus": 6, "adapters": 6,
                                "symbol": ":/symbols/affinity/circle/blue/interconnect.svg",
                                "adapter_type": "virtio-net-pci", "qemu_path": "/usr/bin/qemu-system-x86_64",
                                "hda_disk_image": "versa-analytics-67ff6c7-21.2.3.qcow2",
                                "name": versa_analytics_template_name, "ram": 16384, "template_type": "qemu",
                                "hda_disk_interface": "virtio", "options": "-cpu host"}
versa_flexvnf_template_data = {"compute_id": "local", "cpus": 1, "adapters": 6,
                               "symbol": ":/symbols/affinity/circle/blue/isdn.svg", "adapter_type": "virtio-net-pci",
                               "qemu_path": "/usr/bin/qemu-system-x86_64",
                               "hda_disk_image": "versa-flexvnf-67ff6c7-21.2.3.qcow2",
                               "name": versa_flexvnf_template_name, "ram": 4096, "template_type": "qemu",
                               "hda_disk_interface": "virtio", "options": "-cpu host -smp 2,maxcpus=2"}


vmanage_deploy_data = {"x": -107, "y": 570, "name": "vManage"}
vsmart_deploy_data = {"x": -182, "y": 495, "name": "vSmart"}
vbond_deploy_data = {"x": -32, "y": 495, "name": "vBond"}
isp_router_deploy_data = {"x": -108, "y": -247, "name": "ISP-Router"}
cloud_node_deploy_data = {"x": -154, "y": -247, "name": "MGMT-Cloud-TAP", "node_type": "cloud",
                          "compute_id": "local", "symbol": ":/symbols/cloud.svg"}
openvswitch_isp_deploy_data = {"x": -154, "y": -51, "name": "Cloud_ISP_01"}
main_mgmt_switch_deploy_data = {"x": 60, "y": -313, "name": "Main_MGMT-switch"}
nat_node_deploy_data = {"x": -154, "y": -554, "name": "Internet", "node_type": "nat", "compute_id": "local",
                        "symbol": ":/symbols/cloud.svg"}

versa_director_deploy_data = {"x": 5, "y": 495, "name": "Versa_Director"}
versa_analytics_deploy_data = {"x": -190, "y": 495, "name": "Versa_Analytics"}
versa_controller_deploy_data = {"x": -100, "y": 317, "name": "Versa_Controller"}
versa_control_switch_deploy_data = {"x": -103, "y": 422, "name": "Control_Network"}

big_block_deploy_data = {
    "svg": "<svg height=\"1500\" width=\"3681\"><rect fill=\"#ffffff\" fill-opacity=\"1.0\" height=\"1500\" stroke=\"#000000\" stroke-width=\"2\" width=\"3681\" /></svg>",
    "x": -1950, "y": -630, "z": -1}

arista_deploy_data = {
    "arista_01_deploy_data": {"x": -323, "y": -219, "name": "arista-spine1"},
    "arista_02_deploy_data": {"x": -23, "y": -219, "name": "arista-spine2"},
    "arista_03_deploy_data": {"x": -558, "y": 79, "name": "arista-leaf1"},
    "arista_04_deploy_data": {"x": -323, "y": 79, "name": "arista-leaf2"},
    "arista_05_deploy_data": {"x": -23, "y": 79, "name": "arista-leaf3"},
    "arista_06_deploy_data": {"x": 200, "y": 79, "name": "arista-leaf4"},
    "arista_07_deploy_data": {"x": 500, "y": 79, "name": "arista-leaf5"}
}
arista_2 = {
    "arista_07_deploy_data": {"x": -25, "y": -23, "name": "arista-leaf5"},
    "arista_08_deploy_data": {"x": -550, "y": 276, "name": "arista-leaf6"},
    "arista_09_deploy_data": {"x": -325, "y": 276, "name": "arista-leaf7"},
    "arista_10_deploy_data": {"x": -25, "y": 276, "name": "arista-leaf8"},
}
client_deploy_data = {
    "client_01_deploy_data": {"x": -555, "y": 373, "name": "Client-1"},
    "client_02_deploy_data": {"x": -330, "y": 373, "name": "Client-2"},
    "client_03_deploy_data": {"x": -30, "y": 373, "name": "Client-3"},
    "client_04_deploy_data": {"x": 200, "y": 373, "name": "Client-4"},
    "client_05_deploy_data": {"x": 494, "y": 373, "name": "Client-5"},
}
local_switch_deploy_data = {
    "switch_01_deploy_data": {"x": -445, "y": 237, "name": "switch-1"},
    "switch_02_deploy_data": {"x": 83, "y": 237, "name": "switch-2"},
    "switch_03_deploy_data": {"x": 491, "y": 237, "name": "switch-3"},
    "switch_04_deploy_data": {"x": 199, "y": 237, "name": "switch-4"},
    "switch_05_deploy_data": {"x": 499, "y": 237, "name": "switch-5"},
}
arista_drawing_deploy_data = {
    "drawing_01": {
        "svg": "<svg width=\"374.71428571428567\" height=\"146.57142857142856\"><ellipse cx=\"187\" rx=\"188\" cy=\"73\" ry=\"74\" fill=\"#00fdff\" fill-opacity=\"0.20602731364919508\" stroke-width=\"2\" stroke=\"#000000\" /></svg>",
        "x": -600, "y": 26, "z": 0},
    "drawing_02": {
        "svg": "<svg width=\"374.71428571428567\" height=\"146.57142857142856\"><ellipse cx=\"187\" rx=\"188\" cy=\"73\" ry=\"74\" fill=\"#00fdff\" fill-opacity=\"0.20602731364919508\" stroke-width=\"2\" stroke=\"#000000\" /></svg>",
        "x": -77, "y": 24, "z": 0},
    "drawing_03": {
        "svg": "<svg width=\"495.7142857142858\" height=\"146.57142857142856\"><ellipse cx=\"247\" rx=\"248\" cy=\"73\" ry=\"74\" fill=\"#00fdff\" fill-opacity=\"0.20602731364919508\" stroke-width=\"2\" stroke=\"#000000\" /></svg>",
        "x": -390, "y": -274, "z": 0},
    "drawing_04": {
        "svg": "<svg width=\"80\" height=\"28\"><text font-family=\"Arial Black\" font-size=\"14.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">AS 65001</text></svg>",
        "x": -453, "y": 75, "z": 2},
    "drawing_05": {
        "svg": "<svg width=\"80\" height=\"28\"><text font-family=\"Arial Black\" font-size=\"14.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">AS 65002</text></svg>",
        "x": 69, "y": 74, "z": 2},
    "drawing_06": {
        "svg": "<svg width=\"80\" height=\"28\"><text font-family=\"Arial Black\" font-size=\"14.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">AS 65000</text></svg>",
        "x": -189, "y": -268, "z": 2},
    "drawing_07": {
        "svg": "<svg width=\"95\" height=\"23\"><text font-family=\"Arial Black\" font-size=\"10.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">MLAG Peer Link</text></svg>",
        "x": -457, "y": 99, "z": 2},
    "drawing_08": {
        "svg": "<svg width=\"95\" height=\"23\"><text font-family=\"Arial Black\" font-size=\"10.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">MLAG Peer Link</text></svg>",
        "x": 66, "y": 101, "z": 2},
    "drawing_09": {
        "svg": "<svg width=\"356\" height=\"36\"><text font-family=\"Arial\" font-size=\"24.0\" fill=\"#000000\" fill-opacity=\"1.0\">Arista EVPN / BGP / VXLAN Lab</text></svg>",
        "x": -238, "y": -407, "z": 2},
    "drawing_10": {
        "svg": "<svg width=\"194\" height=\"212\"><text font-family=\"TypeWriter\" font-size=\"10.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">Managment Network: 172.16.3.0/24\narista-spine1 - 172.16.3.2\narista-spine1 - 172.16.3.3\narista-leaf1 - 172.16.3.4\narista-leaf2 - 172.16.3.5\narista-leaf3 - 172.16.3.6\narista-leaf4 - 172.16.3.7\narista-leaf5 - 172.16.3.8\n\nClient Network: 172.16.101.0/24\nVLAN 40\nVXLAN1\nClient-1: 172.16.101.2\nClient-2: 172.16.101.3\nClient-3: 172.16.101.4\nClient-4: 172.16.101.5\nClient-5: 172.16.101.6</text></svg>",
        "x": -603, "y": -293, "z": 2},
    "drawing_11": {
        "svg": "<svg width=\"1326\" height=\"163\"><rect width=\"1326\" height=\"163\" fill=\"#00f900\" fill-opacity=\"0.19299610894941635\" stroke-width=\"2\" stroke=\"#000000\" /></svg>",
        "x": -640, "y": 318, "z": 0},
    "drawing_12": {
        "svg": "<svg width=\"74\" height=\"28\"><text font-family=\"Arial Black\" font-size=\"14.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">VLAN 40</text></svg>",
        "x": -182, "y": 320, "z": 2},
    "drawing_13": {
        "svg": "<svg width=\"207.5\" height=\"146.57142857142856\"><ellipse cx=\"103\" rx=\"104\" cy=\"73\" ry=\"74\" fill=\"#00fdff\" fill-opacity=\"0.20602731364919508\" stroke-width=\"2\" stroke=\"#000000\" /></svg>",
        "x": 422, "y": 21, "z": 0},
    "drawing_14": {
        "svg": "<svg width=\"80\" height=\"28\"><text font-family=\"Arial Black\" font-size=\"14.0\" font-weight=\"bold\" fill=\"#000000\" fill-opacity=\"1.0\">AS 65003</text></svg>",
        "x": 481, "y": 29, "z": 2},
}

template_city_data_bgp = {
    "replace-001": {"city": "NewYorkCity", "country": "US", "latitude": 40.712776, "longitude": -74.005974},
    "replace-002": {"city": "Detroit", "country": "US", "latitude": 42.331427, "longitude": -83.045754},
    "replace-003": {"city": "Atlanta", "country": "US", "latitude": 33.749, "longitude": -84.387984},
    "replace-004": {"city": "Nashville", "country": "US", "latitude": 36.162664, "longitude": -86.781602},
    "replace-005": {"city": "Houston", "country": "US", "latitude": 29.760427, "longitude": -95.369803},
    "replace-006": {"city": "Miami", "country": "US", "latitude": 25.76168, "longitude": -80.19179},
    "replace-007": {"city": "Chicago", "country": "US", "latitude": 41.878114, "longitude": -87.629798},
    "replace-008": {"city": "Kansas City", "country": "US", "latitude": 39.099727, "longitude": -94.578567},
    "replace-009": {"city": "Minneapolis", "country": "US", "latitude": 44.977753, "longitude": -93.265011},
    "replace-010": {"city": "Denver", "country": "US", "latitude": 39.739235, "longitude": -104.99025},
    "replace-011": {"city": "Billings", "country": "US", "latitude": 45.783286, "longitude": -108.50069},
    "replace-012": {"city": "Phoenix", "country": "US", "latitude": 33.448376, "longitude": -112.074036},
    "replace-013": {"city": "SaltLakeCity", "country": "US", "latitude": 40.76078, "longitude": -111.891045},
    "replace-014": {"city": "SanFrancisco", "country": "US", "latitude": 37.773972, "longitude": -122.431297},
    "replace-015": {"city": "LosAngeles", "country": "US", "latitude": 34.052235, "longitude": -118.243683},
    "replace-016": {"city": "Seattle", "country": "US", "latitude": 47.608013, "longitude": -122.335167},
}

template_city_data = {
    "replace-001": {"city": "NewYorkCity", "country": "US", "latitude": 40.712776, "longitude": -74.005974},
    "replace-002": {"city": "Seattle", "country": "US", "latitude": 47.608013, "longitude": -122.335167},
    "replace-003": {"city": "SanFrancisco", "country": "US", "latitude": 37.773972, "longitude": -122.431297},
    "replace-004": {"city": "Atlanta", "country": "US", "latitude": 33.749, "longitude": -84.387984},
    "replace-005": {"city": "Miami", "country": "US", "latitude": 25.76168, "longitude": -80.19179},
    "replace-006": {"city": "Chicago", "country": "US", "latitude": 41.878114, "longitude": -87.629798},
    "replace-007": {"city": "Nashville", "country": "US", "latitude": 36.162664, "longitude": -86.781602},
    "replace-008": {"city": "Kansas City", "country": "US", "latitude": 39.099727, "longitude": -94.578567},
    "replace-009": {"city": "Minneapolis", "country": "US", "latitude": 44.977753, "longitude": -93.265011},
    "replace-010": {"city": "Denver", "country": "US", "latitude": 39.739235, "longitude": -104.99025},
    "replace-011": {"city": "Billings", "country": "US", "latitude": 45.783286, "longitude": -108.50069},
    "replace-012": {"city": "Phoenix", "country": "US", "latitude": 33.448376, "longitude": -112.074036},
    "replace-013": {"city": "SaltLakeCity", "country": "US", "latitude": 40.76078, "longitude": -111.891045},
    "replace-014": {"city": "Detroit", "country": "US", "latitude": 42.331427, "longitude": -83.045754},
    "replace-015": {"city": "LosAngeles", "country": "US", "latitude": 34.052235, "longitude": -118.243683},
    "replace-016": {"city": "Houston", "country": "US", "latitude": 29.760427, "longitude": -95.369803},
}

template_city_data_multivendor = {
    "replace-001": {"city": "Miami", "country": "US", "latitude": 25.76168, "longitude": -80.19179},
    "replace-002": {"city": "Nashville", "country": "US", "latitude": 36.162664, "longitude": -86.781602},
    "replace-003": {"city": "Houston", "country": "US", "latitude": 29.760427, "longitude": -95.369803},
    "replace-004": {"city": "Kansas City", "country": "US", "latitude": 39.099727, "longitude": -94.578567},
}

template_city_data_wordwide = {
    "replace-001": {"city": "GrandPrairie", "country": "US", "latitude": 32.745964, "longitude": -96.997785},
    "replace-002": {"city": "Urayasu", "country": "JP", "latitude": 35.653052, "longitude": 139.901849},
    "replace-003": {"city": "SpringValley", "country": "US", "latitude": 29.791118, "longitude": -95.503158},
    "replace-004": {"city": "Katsuta", "country": "JP", "latitude": 36.394435, "longitude": 140.524243},
    "replace-005": {"city": "Diadema", "country": "BR", "latitude": -23.681347, "longitude": -46.62052},
    "replace-006": {"city": "Paradise", "country": "US", "latitude": 36.115086, "longitude": -115.173414},
    "replace-007": {"city": "CapeCoral", "country": "US", "latitude": 26.605943, "longitude": -81.980677},
    "replace-008": {"city": "Planaltina", "country": "BR", "latitude": -15.457154, "longitude": -47.608902},
    "replace-009": {"city": "Paulista", "country": "BR", "latitude": -7.934007, "longitude": -34.868407},
    "replace-010": {"city": "VoltaRedonda", "country": "BR", "latitude": -22.521856, "longitude": -44.104013},
    "replace-011": {"city": "Fayette", "country": "US-Lexington", "latitude": 29.838164, "longitude": -96.955969},
    "replace-012": {"city": "Fontana", "country": "US", "latitude": 34.092233, "longitude": -117.435048},
    "replace-013": {"city": "Barreiras", "country": "BR", "latitude": -12.144003, "longitude": -44.996741},
    "replace-014": {"city": "Kawanishi", "country": "JP", "latitude": 34.869914, "longitude": 135.414701},
    "replace-015": {"city": "Hollywood", "country": "US", "latitude": 34.098003, "longitude": -118.329523},
    "replace-016": {"city": "Oceanside", "country": "US", "latitude": 33.19587, "longitude": -117.379483},
    "replace-017": {"city": "Chandler", "country": "US", "latitude": 33.306203, "longitude": -111.841185},
    "replace-018": {"city": "Mesa", "country": "US", "latitude": 33.415101, "longitude": -111.831455},
    "replace-019": {"city": "Petrolina", "country": "BR", "latitude": -9.381733, "longitude": -40.496887},
    "replace-020": {"city": "Campinas", "country": "BR", "latitude": -22.90556, "longitude": -47.06083},
    "replace-021": {"city": "EastChattanooga", "country": "US", "latitude": 35.065351, "longitude": -85.249123},
    "replace-022": {"city": "DuquedeCaxias", "country": "BR", "latitude": -22.789623, "longitude": -43.309929},
    "replace-023": {"city": "Glendale", "country": "US", "latitude": 34.146942, "longitude": -118.247847},
    "replace-024": {"city": "Limeira", "country": "BR", "latitude": -22.561507, "longitude": -47.401766},
    "replace-025": {"city": "Betim", "country": "BR", "latitude": -19.968056, "longitude": -44.198333},
    "replace-026": {"city": "Rio Grande", "country": "BR", "latitude": 37.566822, "longitude": -106.383216},
    "replace-027": {"city": "Vila Velha", "country": "BR", "latitude": -20.329704, "longitude": -40.292017},
    "replace-028": {"city": "Caucaia", "country": "BR", "latitude": -3.730056, "longitude": -38.659308},
    "replace-029": {"city": "Hialeah", "country": "US", "latitude": 25.857596, "longitude": -80.278106},
    "replace-030": {"city": "Nossa Senhora do Socorro", "country": "BR", "latitude": -10.855311, "longitude": -37.126486},
    "replace-031": {"city": "Sunrise Manor", "country": "US", "latitude": 36.183087, "longitude": -115.027964},
    "replace-032": {"city": "Lakewood", "country": "US", "latitude": 39.708574, "longitude": -105.084669},
    "replace-033": {"city": "Greensboro", "country": "US", "latitude": 36.072635, "longitude": -79.791975},
    "replace-034": {"city": "Itabuna", "country": "BR", "latitude": -14.793173, "longitude": -39.275034},
    "replace-035": {"city": "Garland", "country": "US", "latitude": 32.912624, "longitude": -96.638883},
    "replace-036": {"city": "Barueri", "country": "BR", "latitude": -23.511218, "longitude": -46.876461},
    "replace-037": {"city": "Plano", "country": "US", "latitude": 33.013676, "longitude": -96.69251},
    "replace-038": {"city": "Corona", "country": "US", "latitude": 33.875295, "longitude": -117.566445},
    "replace-039": {"city": "Lages", "country": "BR", "latitude": -27.816566, "longitude": -50.325883},
    "replace-040": {"city": "East Hampton", "country": "US", "latitude": 40.963387, "longitude": -72.18476},
    "replace-041": {"city": "Governador Valadares", "country": "BR", "latitude": -18.85395, "longitude": -41.945875},
    "replace-042": {"city": "Cachoeiro de Itapemirim", "country": "BR", "latitude": -20.848084, "longitude": -41.11129},
    "replace-043": {"city": "Chula Vista", "country": "US", "latitude": 32.640054, "longitude": -117.084196},
    "replace-044": {"city": "Santa Clarita", "country": "US", "latitude": 34.391664, "longitude": -118.542586},
    "replace-045": {"city": "Lancaster", "country": "US", "latitude": 40.03813, "longitude": -76.305669},
    "replace-046": {"city": "Campina Grande", "country": "BR", "latitude": -7.224674, "longitude": -35.877129},
    "replace-047": {"city": "Logan City", "country": "AU", "latitude": -27.642413, "longitude": 153.113104},
    "replace-048": {"city": "Long Beach", "country": "US", "latitude": 33.769016, "longitude": -118.191604},
    "replace-049": {"city": "Rio Claro", "country": "BR", "latitude": -22.410011, "longitude": -47.560393},
    "replace-050": {"city": "Yonkers", "country": "US", "latitude": 40.93121, "longitude": -73.898747},
}

deploy_data_z = {"z": -1}

