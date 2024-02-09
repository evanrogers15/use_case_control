import requests
import urllib.request
import sys
import os
gns3_server_data = [
 {
     "GNS3 Server": "10.142.0.134",
     "Server Name": "er-test-01",
     "Server Port": "80",
     "vManage API IP": "172.16.2.2",
     "Project Name": "test111",
     "Tap Name": "tap1",
     "Use Tap": 0,
     "Site Count": 0,
     "Deployment Type": 'viptela',
     "Deployment Step": 'test',
     "Deployment Status": 'test'
 }
]

def gns3_get_image(gns3_server_data, image_type, filename):
    # Create the images directory if it doesn't exist
    if not os.path.exists('images'):
        os.makedirs('images')

    for server_record in gns3_server_data:
        server_ip, server_port, server_name, project_name, vmanage_api_ip, deployment_type, deployment_status, deployment_step = \
            server_record['GNS3 Server'], server_record['Server Port'], server_record['Server Name'], server_record[
                'Project Name'], server_record['vManage API IP'], server_record['Deployment Type'], server_record[
                'Deployment Status'], server_record['Deployment Step']
        url = f"http://{server_ip}:{server_port}/v2/compute/{image_type}/images"
        response = requests.get(url)
        for image in response.json():
            if image['filename'] == filename:
                print(f"Downloading {filename}")
                url = f'http://{server_ip}:{server_port}/v2/compute/{image_type}/images/{filename}'
                file_path = os.path.join('images', filename)
                urllib.request.urlretrieve(url, file_path)
                return 201
    return 200

versa_required_qemu_images = {"versa-director-c19c43c-21.2.3.qcow2", "versa-analytics-67ff6c7-21.2.3.qcow2", "versa-flexvnf-67ff6c7-21.2.3.qcow2"}
cisco_required_qemu_images = {"viptela-vmanage-li-20.10.1-genericx86-64.qcow2", "viptela-smart-li-20.10.1-genericx86-64.qcow2", "viptela-edge-20.10.1-genericx86-64.qcow2", "c8000v-universalk9_8G_serial.17.09.01a.qcow2"}
appneta_required_qemu_images = {"pathview-amd64-14.1.0.54901.qcow2"}
velocloud_required_qemu_images = {"edge-VC_KVM_GUEST-x86_64-4.5.0-159-R450-20220413-GA-a234e62866-updatable-ext4.qcow2"}

cisco = 0
versa = 0
appneta = 0
velocloud = 1

# for image in required_iou_images:
#    gns3_get_image(gns3_server_data, 'iou', image)
if cisco == 1:
    for image in cisco_required_qemu_images:
        gns3_get_image(gns3_server_data, 'qemu', image)

if versa == 1:
    for image in versa_required_qemu_images:
        gns3_get_image(gns3_server_data, 'qemu', image)

if appneta == 1:
    for image in appneta_required_qemu_images:
        gns3_get_image(gns3_server_data, 'qemu', image)

if velocloud == 1:
    for image in velocloud_required_qemu_images:
        gns3_get_image(gns3_server_data, 'qemu', image)

