import logging.handlers

from modules.gns3.gns3_actions import *
from modules.gns3.gns3_dynamic_data import *

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# region Functions: Viptela API
class Authentication:
    def get_jsessionid(self, vmanage_api_ip):
        api = "/j_security_check"
        base_url = f"https://{vmanage_api_ip}"
        url = base_url + api
        payload = {'j_username': viptela_username, 'j_password': viptela_password}
        response = requests.post(url=url, data=payload, verify=False)
        try:
            cookies = response.headers["Set-Cookie"]
            jsessionid = cookies.split(";")
            return jsessionid[0]
        except:
            # logging.info("No valid JSESSION ID returned\n")
            exit()

    def get_token(self, jsessionid, vmanage_api_ip):
        headers = {'Cookie': jsessionid}
        base_url = f"https://{vmanage_api_ip}"
        api = "/dataservice/client/token"
        url = base_url + api
        response = requests.get(url=url, headers=headers, verify=False)
        if response.status_code == 200:
            return response.text
        else:
            return None

def vmanage_create_auth(vmanage_api_ip):
    vmanage_auth = Authentication()
    jsessionid = vmanage_auth.get_jsessionid(vmanage_api_ip)
    token = vmanage_auth.get_token(jsessionid, vmanage_api_ip)
    if token is not None:
        vmanage_headers = {'Content-Type': "application/json", 'Cookie': jsessionid, 'X-XSRF-TOKEN': token}
    else:
        vmanage_headers = {'Content-Type': "application/json", 'Cookie': jsessionid}
    return vmanage_headers

def vmanage_set_cert_type(vmanage_api_ip, vmanage_headers):
    url = f"https://{vmanage_api_ip}/dataservice/settings/configuration/certificate"
    catype = "enterprise"
    response_data = {'certificateSigning': catype}
    try:
        response = requests.post(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                 timeout=20)
        response.raise_for_status()
        logging.info(f"Deploy - Set certificate authority type for vManage {vmanage_api_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(response.content)
        logging.info(f"vManage not available: {str(e)}")

def vmanage_set_cert(vmanage_api_ip, vmanage_headers, cert):
    url = f"https://{vmanage_api_ip}/dataservice/settings/configuration/certificate/enterpriserootca"
    response_data = {'enterpriseRootCA': cert}
    try:
        response = requests.put(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                timeout=20)
        response.raise_for_status()
        logging.info(f"Deploy - Uploaded new root certificate to vManage {vmanage_api_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(response.content)
        logging.info(f"vManage not available: {str(e)}")

def vmanage_install_cert(vmanage_api_ip, vmanage_headers, cert):
    url = f"https://{vmanage_api_ip}/dataservice/certificate/install/signedCert"
    response_data = {'enterpriseRootCA': cert}
    try:
        response = requests.post(url, data=cert, headers=vmanage_headers, verify=False, timeout=20)
        response.raise_for_status()
        logging.info(f"Deploy - Installed device certificate for vManage {vmanage_api_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(response.content)
        logging.info(f"vManage not available: {str(e)}")

def vmanage_forcesync_rootcert(vmanage_api_ip, vmanage_headers):
    url = f"https://{vmanage_api_ip}/dataservice/certificate/forcesync/rootCert"
    response_data = {}
    try:
        response = requests.post(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                 timeout=20)
        response.raise_for_status()
        logging.info(f"Deploy - Forced root certificate sync on vManage {vmanage_api_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(response.content)
        logging.info(f"vManage not available: {str(e)}")

def vmanage_sync_rootcertchain(vmanage_api_ip, vmanage_headers):
    url = f"https://{vmanage_api_ip}/dataservice/system/device/sync/rootcertchain"
    response_data = {}
    try:
        response = requests.get(url, headers=vmanage_headers, verify=False, timeout=20)
        response.raise_for_status()
        logging.info(f"Deploy - Synced root certificate chain for vManage {vmanage_api_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(response.content)
        logging.info(f"vManage not available: {str(e)}")

def vmanage_set_vbond(vmanage_api_ip, vmanage_headers, vbond_ip):
    url = f"https://{vmanage_api_ip}/dataservice/settings/configuration/device"
    response_data = {'domainIp': vbond_ip, 'port': '12346'}
    try:
        response = requests.post(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                 timeout=20)
        response.raise_for_status()
        logging.info(f"Deploy - Set vBond {vbond_ip} for vManage {vmanage_api_ip} in configuration settings")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"vManage not available: {str(e)}")

def vmanage_set_org(vmanage_api_ip, vmanage_headers):
    url = f"https://{vmanage_api_ip}/dataservice/settings/configuration/organization"
    response_data = {'org': org_name}
    try:
        response = requests.post(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                 timeout=20)
        response.raise_for_status()
        logging.info(f"Deploy - Set organization for vManage {vmanage_api_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"vManage not available: {str(e)}")

def vmanage_push_certs(vmanage_api_ip, vmanage_headers):
    url = f"https://{vmanage_api_ip}/dataservice/certificate/vedge/list?action=push"
    response_data = {}
    try:
        response = requests.post(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                 timeout=20)
        response.raise_for_status()
        logging.info(f"Deploy - Pushed vEdge certificates to control devices for vManage {vmanage_api_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"vManage not available: {str(e)}")

def vmanage_set_device(vmanage_api_ip, vmanage_headers, vdevice_ip, vdevice_personality):
    url = f"https://{vmanage_api_ip}/dataservice/system/device"
    response_data = {"deviceIP": vdevice_ip, "username": viptela_username, "password": viptela_password,
                     "personality": vdevice_personality, "generateCSR": "true", }
    try:
        response = requests.post(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                 timeout=35)
        if response.status_code == requests.codes.ok:
            logging.info(f"Deploy - {vdevice_personality} with address {vdevice_ip} set successfully on vManage {vmanage_api_ip}")
        else:
            logging.info(f"Deploy - Failed to add {vdevice_personality} device. ")
            logging.info("Response: {}".format(response.text))
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"vManage not available: {str(e)}")

def vmanage_generate_csr(vmanage_api_ip, vmanage_headers, vdevice_ip, vdevice_personality):
    url = f"https://{vmanage_api_ip}/dataservice/certificate/generate/csr"
    response_data = {"deviceIP": vdevice_ip}
    try:
        response = requests.post(url, data=json.dumps(response_data), headers=vmanage_headers, verify=False,
                                 timeout=20)
        response.raise_for_status()
        result = util_extract_csr(response)
        logging.info(f"Deploy - Generated CSR for {vdevice_personality} on vManage {vmanage_api_ip}")
        return result[0]['deviceCSR']
    except requests.exceptions.RequestException as e:
        logging.info(f"vManage not available: {str(e)}")

# endregion
