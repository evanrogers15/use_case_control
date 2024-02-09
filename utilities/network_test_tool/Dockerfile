FROM gns3/ubuntu:focal

RUN apt-get update && apt-get install -y snmp iperf3 nuttcp iptables
RUN apt-get update && apt-get install -y python3-pip
RUN pip install --no-cache-dir --pre scapy[basic]

COPY netflow_forwarder_single.py /home/scripts/netflow_forwarder_single.py
COPY netflow_forwarder_dual.py /home/scripts/netflow_forwarder_dual.py
COPY traffic_generator.py /home/scripts/traffic_generator.py
COPY startup.sh /home/scripts/startup.sh
RUN chmod +x /home/scripts/startup.sh

WORKDIR /home

CMD ["/bin/bash", "/home/scripts/startup.sh"]
