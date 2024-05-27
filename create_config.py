import yaml
import subprocess
import sys

def generate_mac_address(idx, base_mac='6e:06:e0:03'):
    """Generate a MAC address based on the index."""
    return f'{base_mac}:{idx:02x}'

def generate_ipv4_address(idx, base_ip='192.168.98'):
    """Generate an IPv4 address based on the index."""
    return f'{base_ip}.{10 + idx * 10}'

def block_communications(rsu_service_name, mac_addresses):
    for mac_address in mac_addresses:
        command = [
            "docker-compose", "exec", rsu_service_name,
            "iptables", "-A", "INPUT", "-m", "mac", "--mac-source", mac_address, "-j", "DROP"
        ]
        subprocess.run(command)

def create_rsu_obu_config(num_rsus, num_obus):

    f = open("./docker-compose.yml", 'r')
    docker_compose_yml = yaml.load(f, Loader=yaml.FullLoader)
    
    del[docker_compose_yml['services']]

    services = {}
    
    for idx in range(1, num_rsus + 1):
        rsu_service_name = f'rsu{idx}'
        rsu_mac_address = generate_mac_address(idx)
        services[rsu_service_name] = {
            'hostname': rsu_service_name,
            'restart': 'always',
            'image': 'code.nap.av.it.pt:5050/mobility-networks/vanetza:latest',
            'cap_add': ['NET_ADMIN'],
            'environment': [
                f'VANETZA_STATION_ID={idx}',
                'VANETZA_STATION_TYPE=15',
                f'VANETZA_MAC_ADDRESS={rsu_mac_address}',
                'VANETZA_INTERFACE=br0',
                'START_EMBEDDED_MOSQUITTO=true',
                'SUPPORT_MAC_BLOCKING=true'
            ],
            'networks': {
                'vanetzalan0': {
                    'ipv4_address': generate_ipv4_address(idx)
                }
            }
        }
        block_communications(rsu_service_name, [rsu_mac_address] + [generate_mac_address(obu_idx) for obu_idx in range(1, num_obus + 1)])
    
    for idx in range(1, num_obus + 1):
        obu_service_name = f'obu{idx}'
        obu_mac_address = generate_mac_address(num_rsus + idx)
        services[obu_service_name] = {
            'hostname': obu_service_name,
            'restart': 'always',
            'image': 'code.nap.av.it.pt:5050/mobility-networks/vanetza:latest',
            'cap_add': ['NET_ADMIN'],
            'environment': [
                f'VANETZA_STATION_ID={num_rsus + idx}',
                'VANETZA_STATION_TYPE=0',
                f'VANETZA_MAC_ADDRESS={obu_mac_address}',
                'VANETZA_INTERFACE=br0',
                'START_EMBEDDED_MOSQUITTO=true',
                'SUPPORT_MAC_BLOCKING=true'
            ],
            'networks': {
                'vanetzalan0': {
                    'ipv4_address': generate_ipv4_address(num_rsus + idx)
                }
            }
        }
    
    docker_compose = {
        'version': '2.4',
        'services': services,
        'networks': {
            'vanetzalan0': {
                'external': True
            }
        }
    }

    return docker_compose

def write_docker_compose_file(config, filename='docker-compose.yml'):
    with open(filename, 'w') as file:
        yaml.dump(config, file, default_flow_style=False)

num_rsus = int(sys.argv[1])
num_obus = int(sys.argv[2])

config = create_rsu_obu_config(num_rsus, num_obus)
write_docker_compose_file(config)
