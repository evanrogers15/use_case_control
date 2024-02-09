import logging.handlers
from modules.gns3.gns3_actions import *

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

auth = ("Administrator", "versa123")

headers = {"Content-Type": "application/json"}

# region Functions: Versa API
def versa_configure_analytics_cluster(director_ip, analytics_ip, analytics_southbound_ip):
    url = f"https://{director_ip}:9182/api/config/nms/provider"
    data = {
        "analytics-cluster": {
            "name": "Analytics",
            "connector-config": {
                "port": "8443",
                "ip-address": [
                    analytics_ip
                ]
            },
            "log-collector-config": {
                "port": "1234",
                "ip-address": [
                    analytics_southbound_ip
                ]
            }
        }
    }
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Configured Analytics Cluster on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_create_provider_org(director_ip):
    url = f"https://{director_ip}:9182/nextgen/organization"
    data = {"name": "Versa-Root","uuid": "310f513a-01aa-4e91-9a53-4dae9b324839","subscriptionPlan": "Default-All-Services-Plan","id": 1,"authType": "psk","cpeDeploymentType": "SDWAN","vrfsGroups": [ { "id": 1, "vrfId": 1, "name": "Versa-Root-LAN-VR", "description": "", "enable_vpn": True }],"analyticsClusters": [ "Analytics"],"sharedControlPlane": False,"dynamicTenantConfig": { "inactivityInterval": 48},"blockInterRegionRouting": False}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Created Provider Organization on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_get_org_uuid(director_ip):
    url = f"https://{director_ip}:9182/nextgen/organization?limit=25&offset=1&uuidOnly=true"
    data = {}
    response = requests.get(url, headers=headers, auth=auth, json=data, verify=False)
    if response.status_code == 200:
        try:
            # Parse the JSON response
            json_data = response.json()
            if isinstance(json_data, list) and len(json_data) > 0:
                # Extract the UUID from the first item in the list
                uuid = json_data[0].get('uuid')
                if uuid:
                    return uuid
                else:
                    print("UUID not found in the response.")
            else:
                print("Invalid JSON response format or empty response.")
        except ValueError as e:
            print("Error parsing JSON response:", e)
    else:
        print(f"Request failed with status code: {response.status_code}")

    return None

def versa_create_overlay_prefix(director_ip):
    url = f"https://{director_ip}:9182/vnms/ipam/overlay/prefixes"
    data = {"prefix":"10.10.0.0/16","status":{"value":1,"label":"Active"}, "is_pool":True}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Created Overlay Prefix on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_create_overlay_route(director_ip, controller_southbound_ip):
    url = f"https://{director_ip}:9182/api/config/nms/routing-options/static"
    data = {"route":{"description":"Overlay-Route","destination-prefix":"10.10.0.0/16","next-hop-address":controller_southbound_ip,"outgoing-interface":"eth1"}}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Created Overlay Route on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")
    
def versa_create_controller_workflow(director_ip, controller_ip, controller_southbound_ip, isp_1_gateway, isp_1_ip, isp_2_gateway, isp_2_ip):
    url = f"https://{director_ip}:9182/vnms/sdwan/workflow/controllers/controller"
    controller_southbound_ip = f'{controller_southbound_ip}/24'
    isp_1_ip = f'{isp_1_ip}/30'
    isp_2_ip = f'{isp_2_ip}/30'

    data = { "versanms.sdwan-controller-workflow": { "controllerName": "Controller-01", "siteId": 1, "orgName": "Versa-Root", "resourceType": "Baremetal", "stagingController": True, "postStagingController": True, "baremetalController": { "serverIP": controller_ip, "controllerInterface": { "interfaceName": "vni-0/1", "unitInfoList": [ { "networkName": "Control-Network", "ipv4address": [ controller_southbound_ip ], "ipv4gateway": "", "ipv6gateway": "", "ipv4dhcp": False, "ipv6dhcp": False, "vlanId": 0, "wanStaging": True, "poolSize": 256 } ] }, "wanInterfaces": [ { "interfaceName": "vni-0/2", "unitInfoList": [ { "networkName": "ISP-1", "ipv4address": [ isp_1_ip ], "ipv4gateway": isp_1_gateway, "ipv4dhcp": False, "ipv6dhcp": False, "vlanId": 0, "wanStaging": True, "poolSize": 128, "transportDomainList": [ "Internet" ] } ] }, { "interfaceName": "vni-0/3", "unitInfoList": [ { "networkName": "ISP-2", "ipv4address": [ isp_2_ip ], "ipv4gateway": isp_2_gateway, "ipv4dhcp": False, "ipv6dhcp": False, "vlanId": 0, "wanStaging": True, "poolSize": 128, "transportDomainList": [ "Internet" ] } ] } ] }, "locationInfo": { "state": "CA", "country": "USA", "city": "San Jose", "longitude": -121.885252, "latitude": 37.33874 }, "analyticsCluster": "Analytics" }}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Created Controller Workflow on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")
        
def versa_deploy_controller(director_ip):
    url = f"https://{director_ip}:9182/vnms/sdwan/workflow/controllers/controller/deploy/Controller-01"
    data = {}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Deployed Controller on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_create_device_template(director_ip):
    url = f"https://{director_ip}:9182/vnms/sdwan/workflow/templates/template"
    data = {
        "versanms.sdwan-template-workflow": {
            "analyticsCluster": "Analytics", "bandwidth": "100", "licensePeriod": "1", "controllers": ["Controller-01"],
            "deviceFirmfactor": 6, "deviceType": "full-mesh", "diaConfig": {"loadBalance": False}, "isStaging": False,
            "lanInterfaces": [{
                                "interfaceName": "vni-0/2", "unitInfo": [{
                                    "vlanId": "0",
                                    "subOrganization": "Versa-Root",
                                    "vrfName": "Versa-Root-LAN-VR",
                                    "networkName": "LAN", "subUnit": "0",
                                    "ipv4Static": True, "ipv4Dhcp": False,
                                    "ip6Static": False, "ipv6Dhcp": False,
                                    "ipv4DhcpServer": True,
                                    "dhcpv4Profile": "DHCP",
                                    "dhcpV4Relay": False,
                                    "dhcpV4RelayAddress": "",
                                    "bandwidthDownlink": "100000",
                                    "bandwidthUplink": "100000",
                                    }]},
            ],
            "providerOrg": {"name": "Versa-Root", "nextGenFW": False, "statefulFW": False},
            "redundantPair": {"enable": False}, "routingInstances": [], "siteToSiteTunnels": [],
            "solutionTier": "Premier-Elite-SDWAN",
            "snmp": {
                "snmpV1": False, "snmpV2": True, "snmpV3": False, "community": "public", "target-source": "{$v_SNMP_TARGET_SOURCE__snmpTargetSource}"
            },
            "splitTunnels": [{"vrfName": "Versa-Root-LAN-VR", "wanNetworkName": "ISP-1", "dia": True, "gateway": False},
                             {
                                 "vrfName": "Versa-Root-LAN-VR", "wanNetworkName": "ISP-2", "dia": True,
                                 "gateway": False
                             }], "subOrgs": [], "templateName": "Edge-Template", "templateType": "sdwan-post-staging",
            "wanInterfaces": [{
                                  "pppoe": False, "interfaceName": "vni-0/0", "unitInfo": [{
                                                                                               "vlanId": "0",
                                                                                               "networkName": "ISP-1",
                                                                                               "routing": {},
                                                                                               "subUnit": "0",
                                                                                               "ipv4Static": True,
                                                                                               "ipv4Dhcp": False,
                                                                                               "ip6Static": False,
                                                                                               "ipv6Dhcp": False,
                                                                                               "transportDomains": [
                                                                                                   "Internet"],
                                                                                                "bandwidthDownlink": "100000",
                                                                                                "bandwidthUplink": "100000",
                                                                                           }]
                              }, {
                                  "pppoe": False, "interfaceName": "vni-0/1", "unitInfo": [{
                                                                                               "vlanId": "0",
                                                                                               "networkName": "ISP-2",
                                                                                               "routing": {},
                                                                                               "subUnit": "0",
                                                                                               "ipv4Static": True,
                                                                                               "ipv4Dhcp": False,
                                                                                               "ip6Static": False,
                                                                                               "ipv6Dhcp": False,
                                                                                               "transportDomains": [
                                                                                                   "Internet"],
                                                                                                "bandwidthDownlink": "100000",
                                                                                                "bandwidthUplink": "100000",
                                                                                           }]
                              }], "l2Interfaces": [], "stp": "RSTP"
        }
    }
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Created Site Device Template on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")
        
def versa_update_device_template_snmp(director_ip, snmp_trap_dst):
    url = f"https://{director_ip}:9182/api/config/devices/template/Edge-Template/config/snmp/target-source"
    data = {"target-source": "{$v_SNMP_TARGET_SOURCE__snmpTargetSource}"}
    try:
        response = requests.put(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Updated Site Device Template on Director {director_ip}")
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")
    url = f"https://{director_ip}:9182/api/config/devices/template/Edge-Template/config/snmp"

    data = {"target":{"name":"snmp_trap_destination","ip":snmp_trap_dst,"udp-port":"162","v2c":{"sec-name":"public"},"tag":["std_v2_trap"]}}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Updated Site Device Template on Director {director_ip}")
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_update_device_template_oobm_interface(director_ip):
    url = f"https://{director_ip}:9182/api/config/devices/template/Edge-Template/config/interfaces"
    data = {"management": {"name": "eth-0/0", "enabled": True, "unit": [{"name": "0", "family": {"inet": {"address": [{"name": "{$v_eth-0-0_Unit_0__address}", "prefix-length": "24", "gateway": "{$v_eth-0-0_0-OOBM-VR-IPv4__vrHopAddress}"}]}}, "enabled": True}]}
    }
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Updated Site Device Template on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_update_device_template_netflow_1(director_ip):
    # Create Netflow Collector Object
    url = f"https://{director_ip}:9182/api/config/devices/template/Edge-Template/config/orgs/org-services/Versa-Root/lef/collectors"
    data = {
        "collector": {
            "name": "Netflow", "template": "Default-LEF-Template", "transport": "udp",
            "destination-address": "{$v_Versa-Root_Netflow_Destination_Address__lefCollectorDestinationAddress}",
            "destination-port": "9995",
            "source-address": "{$v_Versa-Root_Netflow_Source_Address__lefCollectorSourceAddress}",
            "transmit-rate": "10000", "pending-queue-limit": "2048", "template-resend-interval": "60",
            "routing-instance": "Versa-Root-LAN-VR"
        }
    }
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Updated Netflow Configuration on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_update_device_template_netflow_2(director_ip):
    # Add Netflow Collector to Collectors group
    url = f"https://{director_ip}:9182/api/config/devices/template/Edge-Template/config/orgs/org-services/Versa-Root/lef/collector-groups/collector-group/Default-Collector-Group"
    data = {"collector-group":{"collector-group-name":"Default-Collector-Group","collectors":["LEF-Collector-log_collector1","Netflow"]}}
    try:
        response = requests.put(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Updated Netflow Configuration on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_update_device_template_netflow_3(director_ip):
    # Enable session logging
    url = f"https://{director_ip}:9182/api/config/devices/template/Edge-Template/config/orgs/org-services/Versa-Root/traffic-monitoring/logging-control/logging-control-profile/Default-Logging-Control"
    data = {
        "logging-control-profile": {
            "name": "Default-Logging-Control", "profile": "Default-Logging-Profile", "options": {
                "stats": {
                    "all": [None]
                }, "sessions": {
                    "all": "end"
                }
            }
        }
    }
    try:
        response = requests.put(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Updated Netflow Configuration on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_update_device_template_netflow_4(director_ip):
    # Create traffic monitoring policy for Netflow traffic
    url = f"https://{director_ip}:9182/api/config/devices/template/Edge-Template/config/orgs/org-services/Versa-Root/traffic-monitoring/policies"
    data = {"traffic-monitoring-policy-group":{"name":"netflow_policy"}}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Updated Netflow Configuration on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_update_device_template_netflow_5(director_ip):
    # Create traffic monitoring rule for Netflow traffic
    url = f"https://{director_ip}:9182/api/config/devices/template/Edge-Template/config/orgs/org-services/Versa-Root/traffic-monitoring/policies/traffic-monitoring-policy-group/netflow_policy/rules"
    data = {
        "rule": {
            "name": "netflow_traffic_rule", "rule-disable": "false", "match": {
                "source": {"zone": {}, "address": {}}, "destination": {"zone": {}, "address": {}}, "application": {}
            }, "set": {
                "performance-monitoring": {"tcp-monitoring": "disabled"},
                "lef": {"options": {"send-netflow-data": "false"}, "event": "end", "profile": "Default-Logging-Profile"}
            }
        }
    }
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Updated Netflow Configuration on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_deploy_device_template(director_ip):
    url = f"https://{director_ip}:9182/vnms/sdwan/workflow/templates/template/deploy/Edge-Template?verifyDiff=True"
    data = {}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Deployed Site Device Template on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_create_wan_network(director_ip, org_id, wan_net):
    url = f"https://{director_ip}:9182/nextgen/organization/{org_id}/wan-networks"
    data = {"name":wan_net,"transport-domains":["Internet"]}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Created WAN Network {wan_net} on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_create_app_steering_template(director_ip):
    url = f"https://{director_ip}:9182/nextgen/applicationServiceTemplate"
    data = {"name":"app-steer","organization":"Versa-Root","trafficCategories":[{"name":"Real_Time","forwardingClass":"fc_ef","lossPriority":"low","appServiceTemplateName":"app-steer","applicationServiceTemplateTrafficCategoryPaths":[{"priority":"1","path":"ISP-1"},{"priority":"2","path":"ISP-2"}],"applicationServiceTemplateTrafficCategoryActionLists":[{"actionType":"LOW_DELAY_VARIATION"},{"actionType":"LOW_LATENCY"}],"trafficCategoryIndex":0},{"name":"Business_Critical","forwardingClass":"fc_af","lossPriority":"low","appServiceTemplateName":"app-steer","applicationServiceTemplateTrafficCategoryPaths":[{"path":"ISP-1","priority":1},{"path":"ISP-2","priority":2}],"applicationServiceTemplateTrafficCategoryActionLists":[{"actionType":"LOW_PACKET_LOSS"},{"actionType":"LOW_LATENCY"}],"trafficCategoryIndex":1},{"name":"Default","forwardingClass":"fc_be","lossPriority":"low","appServiceTemplateName":"app-steer","applicationServiceTemplateTrafficCategoryPaths":[{"priority":"1","path":"ISP-1"},{"priority":"2","path":"ISP-2"}],"trafficCategoryIndex":2},{"name":"Low_Priority","forwardingClass":"fc13","lossPriority":"high","appServiceTemplateName":"app-steer","applicationServiceTemplateTrafficCategoryPaths":[{"priority":"1","path":"ISP-1"},{"priority":"2","path":"ISP-2"}],"trafficCategoryIndex":3}],"applicationServiceTemplateRules":[{"name":"Voice","description":"Voice applications rule","trafficCategoryName":"Real_Time","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[{"actionType":"LOW_DELAY_VARIATION"},{"actionType":"LOW_LATENCY"}],"applicationServiceTemplateRuleFilterLists":[{"name":"VOIP","applicationType":"PREDEFINED"}],"applicationServiceTemplateRuleGroupLists":[]},{"name":"Audio-Video-Streaming","description":"Audio video streaming applications rule","trafficCategoryName":"Real_Time","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[{"actionType":"LOW_DELAY_VARIATION"},{"actionType":"LOW_LATENCY"}],"applicationServiceTemplateRuleFilterLists":[{"name":"Audio-Video-Streaming","applicationType":"PREDEFINED"}],"applicationServiceTemplateRuleGroupLists":[]},{"name":"Google-Apps","description":"Google applications","trafficCategoryName":"Default","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[],"applicationServiceTemplateRuleFilterLists":[],"applicationServiceTemplateRuleGroupLists":[{"name":"Google-Apps","applicationType":"PREDEFINED"}]},{"name":"Conferencing-Apps","description":"Conferencing applications","trafficCategoryName":"Default","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[],"applicationServiceTemplateRuleFilterLists":[],"applicationServiceTemplateRuleGroupLists":[{"name":"GotoMeeting-Apps","applicationType":"PREDEFINED"},{"name":"Webex-Apps","applicationType":"PREDEFINED"}]},{"name":"SoftwareUpdates","description":"Software Updates","trafficCategoryName":"Default","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[],"applicationServiceTemplateRuleFilterLists":[{"name":"Software-Updates","applicationType":"PREDEFINED"}],"applicationServiceTemplateRuleGroupLists":[]},{"name":"File-Transfer","description":"File transfer applications","trafficCategoryName":"Default","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[{"actionType":"LOW_PACKET_LOSS"}],"applicationServiceTemplateRuleFilterLists":[{"name":"File-Transfer","applicationType":"PREDEFINED"}],"applicationServiceTemplateRuleGroupLists":[]},{"name":"Adobe-Apps","description":"Adobe applications","trafficCategoryName":"Default","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[{"actionType":"LOW_PACKET_LOSS"}],"applicationServiceTemplateRuleFilterLists":[],"applicationServiceTemplateRuleGroupLists":[{"name":"Adobe-Apps","applicationType":"PREDEFINED"}]},{"name":"Advertising","description":"Advertising","trafficCategoryName":"Low_Priority","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[],"applicationServiceTemplateRuleFilterLists":[{"name":"Advertising","applicationType":"PREDEFINED"}],"applicationServiceTemplateRuleGroupLists":[]},{"name":"Gaming","description":"Gaming applications","trafficCategoryName":"Low_Priority","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[],"applicationServiceTemplateRuleFilterLists":[{"name":"Gaming","applicationType":"PREDEFINED"}],"applicationServiceTemplateRuleGroupLists":[]},{"name":"P2P","description":"P2P applications","trafficCategoryName":"Low_Priority","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[],"applicationServiceTemplateRuleFilterLists":[{"name":"P2P","applicationType":"PREDEFINED"}],"applicationServiceTemplateRuleGroupLists":[]},{"name":"Social-Media","description":"Social-media applications","trafficCategoryName":"Low_Priority","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[{"urlCategory":"social_network","applicationType":"PREDEFINED"}],"applicationServiceTemplateRuleActionLists":[],"applicationServiceTemplateRuleFilterLists":[],"applicationServiceTemplateRuleGroupLists":[{"name":"Social-Media","applicationType":"PREDEFINED"},{"name":"LinkedIn-Apps","applicationType":"PREDEFINED"},{"name":"Twitter-Apps","applicationType":"PREDEFINED"}]},{"name":"ADP-Apps","description":"ADP applications","trafficCategoryName":"Business_Critical","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[{"actionType":"LOW_PACKET_LOSS"}],"applicationServiceTemplateRuleFilterLists":[],"applicationServiceTemplateRuleGroupLists":[{"name":"ADP-Apps","applicationType":"PREDEFINED"}]},{"name":"Amazon-Apps","description":"Amazon applications","trafficCategoryName":"Business_Critical","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[{"actionType":"LOW_PACKET_LOSS"}],"applicationServiceTemplateRuleFilterLists":[],"applicationServiceTemplateRuleGroupLists":[{"name":"Amazon-Apps","applicationType":"PREDEFINED"}]},{"name":"Box-Apps","description":"Box.com applications","trafficCategoryName":"Business_Critical","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[{"actionType":"LOW_PACKET_LOSS"}],"applicationServiceTemplateRuleFilterLists":[],"applicationServiceTemplateRuleGroupLists":[{"name":"Box-Apps","applicationType":"PREDEFINED"}]},{"name":"Citrix-Apps","description":"Citrix applications","trafficCategoryName":"Business_Critical","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[{"actionType":"LOW_PACKET_LOSS"}],"applicationServiceTemplateRuleFilterLists":[],"applicationServiceTemplateRuleGroupLists":[{"name":"Citrix-Apps","applicationType":"PREDEFINED"}]},{"name":"Concur-Apps","description":"Concur applications","trafficCategoryName":"Business_Critical","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[{"actionType":"LOW_PACKET_LOSS"}],"applicationServiceTemplateRuleFilterLists":[],"applicationServiceTemplateRuleGroupLists":[{"name":"Concur-Apps","applicationType":"PREDEFINED"}]},{"name":"Docusign-Apps","description":"Docusign applications","trafficCategoryName":"Business_Critical","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[{"actionType":"LOW_PACKET_LOSS"}],"applicationServiceTemplateRuleFilterLists":[],"applicationServiceTemplateRuleGroupLists":[{"name":"Docusign-Apps","applicationType":"PREDEFINED"}]},{"name":"Dropbox-Apps","description":"Dropbox applications","trafficCategoryName":"Business_Critical","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[{"actionType":"LOW_PACKET_LOSS"}],"applicationServiceTemplateRuleFilterLists":[],"applicationServiceTemplateRuleGroupLists":[{"name":"Dropbox-Apps","applicationType":"PREDEFINED"}]},{"name":"IBM-Apps","description":"IBM applications","trafficCategoryName":"Business_Critical","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[{"actionType":"LOW_PACKET_LOSS"}],"applicationServiceTemplateRuleFilterLists":[],"applicationServiceTemplateRuleGroupLists":[{"name":"IBM-Apps","applicationType":"PREDEFINED"}]},{"name":"Intuit-Apps","description":"Intuit applications","trafficCategoryName":"Business_Critical","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[{"actionType":"LOW_PACKET_LOSS"}],"applicationServiceTemplateRuleFilterLists":[],"applicationServiceTemplateRuleGroupLists":[{"name":"Intuit-Apps","applicationType":"PREDEFINED"}]},{"name":"Jira-Apps","description":"Jira applications","trafficCategoryName":"Business_Critical","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[{"actionType":"LOW_PACKET_LOSS"}],"applicationServiceTemplateRuleFilterLists":[],"applicationServiceTemplateRuleGroupLists":[{"name":"Jira-Apps","applicationType":"PREDEFINED"}]},{"name":"Office365-Apps","description":"Office365 applications","trafficCategoryName":"Business_Critical","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[{"actionType":"LOW_PACKET_LOSS"}],"applicationServiceTemplateRuleFilterLists":[],"applicationServiceTemplateRuleGroupLists":[{"name":"Office365-Apps","applicationType":"PREDEFINED"}]},{"name":"Oracle-Apps","description":"Oracle applications","trafficCategoryName":"Business_Critical","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[{"actionType":"LOW_PACKET_LOSS"}],"applicationServiceTemplateRuleFilterLists":[],"applicationServiceTemplateRuleGroupLists":[{"name":"Oracle-Apps","applicationType":"PREDEFINED"}]},{"name":"SAP-Apps","description":"SAP applications","trafficCategoryName":"Business_Critical","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[{"actionType":"LOW_PACKET_LOSS"}],"applicationServiceTemplateRuleFilterLists":[],"applicationServiceTemplateRuleGroupLists":[{"name":"SAP-Apps","applicationType":"PREDEFINED"}]},{"name":"Salesforce-Apps","description":"Salesforce applications","trafficCategoryName":"Business_Critical","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[{"actionType":"LOW_PACKET_LOSS"}],"applicationServiceTemplateRuleFilterLists":[],"applicationServiceTemplateRuleGroupLists":[{"name":"Salesforce-Apps","applicationType":"PREDEFINED"}]},{"name":"Zendesk-Apps","description":"Zendesk applications","trafficCategoryName":"Business_Critical","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[{"actionType":"LOW_PACKET_LOSS"}],"applicationServiceTemplateRuleFilterLists":[],"applicationServiceTemplateRuleGroupLists":[{"name":"Zendesk-Apps","applicationType":"PREDEFINED"}]},{"name":"Zoho-Apps","description":"Zoho applications","trafficCategoryName":"Business_Critical","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[{"actionType":"LOW_PACKET_LOSS"}],"applicationServiceTemplateRuleFilterLists":[],"applicationServiceTemplateRuleGroupLists":[{"name":"Zoho-Apps","applicationType":"PREDEFINED"}]},{"name":"SaaS-Applications","description":"SaaS applications","trafficCategoryName":"Business_Critical","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[{"actionType":"LOW_PACKET_LOSS"}],"applicationServiceTemplateRuleFilterLists":[{"name":"SaaS-Applications","applicationType":"PREDEFINED"}],"applicationServiceTemplateRuleGroupLists":[]},{"name":"Database","description":"Database applications","trafficCategoryName":"Business_Critical","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[{"actionType":"LOW_PACKET_LOSS"}],"applicationServiceTemplateRuleFilterLists":[{"name":"Database","applicationType":"PREDEFINED"}],"applicationServiceTemplateRuleGroupLists":[]},{"name":"Business-Traffic","description":"Business applications","trafficCategoryName":"Business_Critical","applicationServiceTemplateRuleApplicationLists":[],"applicationServiceTemplateRuleServiceLists":[],"applicationServiceTemplateRuleMatches":[],"applicationServiceTemplateRulePaths":[],"applicationServiceTemplateRuleUrlCategoryLists":[],"applicationServiceTemplateRuleActionLists":[{"actionType":"LOW_PACKET_LOSS"}],"applicationServiceTemplateRuleFilterLists":[{"name":"Business-Traffic","applicationType":"PREDEFINED"}],"applicationServiceTemplateRuleGroupLists":[]}]}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Created Application Steering Workflow Template on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_deploy_app_steering_template(director_ip):
    url = f"https://{director_ip}:9182/nextgen/applicationServiceTemplate/deploy/app-steer"
    data = {}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Deployed Application Steering Workflow Template on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_create_device_group(director_ip):
    url = f"https://{director_ip}:9182/nextgen/deviceGroup"
    data = {"device-group":{"name":"Sites","dg:organization":"Versa-Root","dg:enable-2factor-auth":False,"dg:ca-config-on-branch-notification":False,"dg:enable-staging-url":False,"template-association":[{"organization":"Versa-Root","category":"DataStore","name":"Versa-Root-DataStore"},{"organization":"Versa-Root","category":"Main","name":"Edge-Template"}, {"organization":"Versa-Root","category":"Application Steering","name":"app-steer"}],"dg:poststaging-template":"Edge-Template"}}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Created Device Group on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_create_dhcp_profile(director_ip):
    url = f"https://{director_ip}:9182/api/config/devices/template/Versa-Root-DataStore/config/orgs/org-services/Versa-Root/dhcp/dhcp4-options-profiles"
    data = {"dhcp4-options-profile":{"name":"DHCP","domain-name":"demo.local","dns-server":["8.8.8.8"]}}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Created DHCP Profile on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_deploy_device_workflow(director_ip, site_name):
    url = f"https://{director_ip}:9182/vnms/sdwan/workflow/devices/device/deploy/{site_name}"
    data = {}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Deployed Site Device Workflow on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_create_site_device_workflow(director_ip, vr_1_route_ip, lan_ip, lan_dhcp_base, site_name, site_id, device_serial_number, device_country, device_city, isp_1_ip, isp_1_gateway, isp_2_ip, isp_2_gateway, tvi_0_2_ip, tvi_0_3_ip, latitude, longitude, mgmt_gateway, mgmt_address):
    url = f"https://{director_ip}:9182/vnms/sdwan/workflow/devices/device"
    lan_dhcp_start = lan_dhcp_base + ".51"
    lan_dhcp_end = lan_dhcp_base + ".100"
    lan_ip_no_mask = lan_ip.split('/')[0]
    # snmp_address = mgmt_address_temp
    data = {
        "versanms.sdwan-device-workflow": {
            "deviceName": site_name, "siteId": site_id, "orgName": "Versa-Root", "serialNumber": device_serial_number,
            "deviceGroup": "Sites", "licensePeriod": 1, "deploymentType": "physical", "locationInfo": {
                "country": device_country, "longitude": longitude, "latitude": latitude, "city": device_city
            }, "postStagingTemplateInfo": {
                "templateName": "Edge-Template", "templateData": {
                    "device-template-variable": {
                        "template": "Edge-Template", "variable-binding": {
                            "attrs": [{"name": "{$v_Site_Id__siteSiteID}", "value": site_id, "isAutogeneratable": True},
                            {
                              "name": "{$v_Chassis_Id__sitesChassisId}", "value": device_serial_number,
                              "isAutogeneratable": True
                            }, {
                              "name": "{$v_Versa-Root-Control-VR_1_Local_address__vrRouterAddress}",
                              "value": vr_1_route_ip, "isAutogeneratable": True, "isOverwritten": False
                            }, {
                              "name": "{$v_longitude__Idlongitude}", "value": longitude,
                              "isAutogeneratable": True
                            }, {
                              "name": "{$v_LAN_IPv4__staticaddress}", "value": lan_ip,
                              "isAutogeneratable": False
                            }, {
                              "name": "{$v_eth-0-0_Unit_0__address}",
                              "value": mgmt_address, "isAutogeneratable": False
                            }, {
                                "name": "{$v_eth-0-0_0-OOBM-VR-IPv4__vrHopAddress}",
                                "value": mgmt_gateway,
                                "isAutogeneratable": False
                            }, {
                              "name": "{$v_SNMP_TARGET_SOURCE__snmpTargetSource}",
                              "value": mgmt_address, "isAutogeneratable": False
                            },{
                              "name": "{$v_Versa-Root_Netflow_Source_Address__lefCollectorSourceAddress}",
                              "value": lan_ip_no_mask, "isAutogeneratable": False
                            }, {
                              "name": "{$v_Versa-Root_Netflow_Destination_Address__lefCollectorDestinationAddress}",
                              "value": "172.16.102.51", "isAutogeneratable": False
                            }, {
                              "name": "{$v_Versa-Root_Site_Name__sitesSiteName}", "value": site_name,
                              "isAutogeneratable": True
                            }, {
                              "name": "{$v_location__IdLocation}",
                              "value": f"{device_city}, {device_country}", "isAutogeneratable": True
                            }, {
                              "name": "{$v_ISP-1_IPv4__staticaddress}", "value": isp_1_ip,
                              "isAutogeneratable": False
                            }, {
                              "name": "{$v_ISP-2_IPv4__staticaddress}", "value": isp_2_ip,
                              "isAutogeneratable": False
                            }, {
                              "name": "{$v_tvi-0-2_-_Unit_0_Static_address__tunnelStaticAddress}",
                              "value": tvi_0_2_ip, "isAutogeneratable": True, "isOverwritten": False
                            }, {
                              "name": "{$v_ISP-2-Transport-VR_IPv4__vrHopAddress}", "value": isp_2_gateway,
                              "isAutogeneratable": False
                            }, {
                              "name": "{$v_ISP-1-Transport-VR_IPv4__vrHopAddress}", "value": isp_1_gateway,
                              "isAutogeneratable": False
                            }, {
                                "name": "{$v_Versa-Root_LAN-POOL-LAN_Pool_Range_Begin_IP__apRangeBegin}",
                                "value": lan_dhcp_start,
                                "isAutogeneratable": False
                            }, {
                                "name": "{$v_Versa-Root_LAN-POOL-LAN_Pool_Range_End_IP__apRangeEnd}",
                                "value": lan_dhcp_end,
                                "isAutogeneratable": False
                            }, {
                              "name": "{$v_latitude__IdLatitude}", "value": latitude,
                              "isAutogeneratable": True
                            }, {
                              "name": "{$v_Versa-Root_Controller-01_Local_auth_email_identifier__IKELIdentifier}",
                              "value": f"{site_name}@Versa-Root.com", "isAutogeneratable": True
                            }, {
                              "name": "{$v_Versa-Root-Control-VR_1_Router_ID__vrRouteId}",
                              "value": vr_1_route_ip, "isAutogeneratable": True, "isOverwritten": False
                            }, {
                              "name": "{$v_tvi-0-3_-_Unit_0_Static_address__tunnelStaticAddress}",
                              "value": tvi_0_3_ip, "isAutogeneratable": True, "isOverwritten": False
                            }, {
                              "name": "{$v_identification__IdName}", "value": site_name,
                              "isAutogeneratable": True
                            }, ]
                        }
                    }, "variableMetadata": [{
                                                "variable": "{$v_Site_Id__siteSiteID}", "group": "SDWAN",
                                                "overlay": False, "type": "INTEGER",
                                                "range": {"start": 100, "end": 16383}
                                            }, {
                                                "variable": "{$v_Chassis_Id__sitesChassisId}", "group": "SDWAN",
                                                "overlay": False, "type": "STRING"
                                            }, {
                                                "variable": "{$v_Versa-Root_Netflow_Destination_Address__lefCollectorDestinationAddress}",
                                                "group": "Others",
                                                "overlay": False
                                            },{
                                                "variable": "{$v_Versa-Root_Netflow_Source_Address__lefCollectorSourceAddress}",
                                                "group": "LEF",
                                                "overlay": True,
                                                "type": "IPV4"
                                            }, {
                                                "variable": "{$v_SNMP_TARGET_SOURCE__snmpTargetSource}", "group": "SNMP", "overlay": False,
                                                "type": "IPV4"
                                            }, {
                                                "variable": "{$v_eth-0-0_0-OOBM-VR-IPv4__vrHopAddress}", "group": "Virtual Routers",
                                                "overlay": False, "type": "IPV4_IPV6"
                                            }, {
                                                "variable": "{$v_Versa-Root-Control-VR_1_Local_address__vrRouterAddress}",
                                                "group": "Virtual Routers", "overlay": True, "type": "IPV4"
                                            }, {
                                                "variable": "{$v_longitude__Idlongitude}", "group": "SDWAN",
                                                "overlay": False, "type": "FLOAT",
                                                "floatRange": {"start": -180, "end": 180}
                                            }, {
                                                "variable": "{$v_LAN_IPv4__staticaddress}", "group": "Interfaces",
                                                "overlay": False, "type": "IPV4_MASK"
                                            }, {
                                                "variable": "{$v_Versa-Root_Site_Name__sitesSiteName}",
                                                "group": "SDWAN", "overlay": False, "type": "STRING"
                                            }, {
                                                "variable": "{$v_location__IdLocation}", "group": "SDWAN",
                                                "overlay": False, "type": "STRING"
                                            }, {
                                                "variable": "{$v_ISP-1_IPv4__staticaddress}", "group": "Interfaces",
                                                "overlay": False, "type": "IPV4_MASK"
                                            }, {
                                                "variable": "{$v_ISP-2_IPv4__staticaddress}", "group": "Interfaces",
                                                "overlay": False, "type": "IPV4_MASK"
                                            }, {
                                                "variable": "{$v_tvi-0-2_-_Unit_0_Static_address__tunnelStaticAddress}",
                                                "group": "Interfaces", "overlay": True, "type": "IPV4_IPV6_MASK"
                                            }, {
                                                "variable": "{$v_ISP-2-Transport-VR_IPv4__vrHopAddress}",
                                                "group": "Virtual Routers", "overlay": False, "type": "IPV4"
                                            }, {
                                                "variable": "{$v_ISP-1-Transport-VR_IPv4__vrHopAddress}",
                                                "group": "Virtual Routers", "overlay": False, "type": "IPV4"
                                            }, {
                                                "variable": "{$v_latitude__IdLatitude}", "group": "SDWAN",
                                                "overlay": False, "type": "FLOAT",
                                                "floatRange": {"start": -90, "end": 90}
                                            }, {
                                                "variable": "{$v_Versa-Root_Controller-01_Local_auth_email_identifier__IKELIdentifier}",
                                                "group": "IPSEC", "overlay": False, "type": "STRING"
                                            }, {
                                                "variable": "{$v_Versa-Root-Control-VR_1_Router_ID__vrRouteId}",
                                                "group": "Virtual Routers", "overlay": True, "type": "IPV4"
                                            }, {
                                                "variable": "{$v_tvi-0-3_-_Unit_0_Static_address__tunnelStaticAddress}",
                                                "group": "Interfaces", "overlay": True, "type": "IPV4_IPV6_MASK"
                                            }, {
                                                "variable": "{$v_identification__IdName}", "group": "SDWAN",
                                                "overlay": False, "type": "STRING"
                                            }, {
                                                "variable": "{$v_Versa-Root_Controller-01_Local_auth_email_key__IKELKey}",
                                                "group": "IPSEC", "overlay": False, "type": "STRING"
                                            }]
                }
            }, "serviceTemplateInfo": {
                "templateData": {
                    "device-template-variable": [{"device": site_name, "template": "Versa-Root-DataStore"}]
                }
            }
        }
    }
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Created Site Device Template on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

def versa_config_edge_mgmt_interface(director_ip, site_name, management_ip, management_gateway):
    url = f"https://{director_ip}:9182/api/config/devices/device/{site_name}/config/interfaces"
    data = {"management":{"name":"eth-0/0","enabled":True,"unit":[{"name":"0","family":{"inet":{"address":[{"name":management_ip,"prefix-length":"24","gateway":management_gateway}]}},"enabled":True}]}}
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, verify=False)
        response.raise_for_status()
        logging.info(f"Deploy - Configured Management interface for site {site_name} on Director {director_ip}")
        return response
    except requests.exceptions.RequestException as e:
        logging.info(f"Versa Director API Call Failed: {str(e)}")

# endregion
