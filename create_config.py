import yaml
import subprocess
import sys
import time
import ast

def generate_mac_address(idx, base_mac='6e:06:e0:03:00'):
    """Generate a MAC address based on the index."""
    return f'{base_mac}:{idx:02x}'

def generate_ipv4_address(idx, base_ip='192.168.98'):
    """Generate an IPv4 address based on the index."""
    return f'{base_ip}.{idx * 10}'

def block_communications(service_name, mac_addresses):
    for mac_address in mac_addresses:
        if mac_address[-1] != service_name[-1]:
            command = [
                "docker-compose", "exec", service_name,
                "block", mac_address
            ]
            try:
                subprocess.run(command, check=True)
                print(f"Successfully blocked MAC address {mac_address} on {service_name}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to run command {command}: {e}")

def wait_for_container(service_name):
    """Wait until the container is fully running."""
    while True:
        command = [
            "docker-compose", "ps", "-q", service_name
        ]
        container_id = subprocess.run(command, capture_output=True, text=True).stdout.strip()
        if container_id:
            command = [
                "docker", "inspect", "-f", "{{.State.Running}}", container_id
            ]
            status = subprocess.run(command, capture_output=True, text=True).stdout.strip()
            if status == "true":
                break
        time.sleep(1)

def create_rsu_obu_config(num_rsus, num_obus, rsu_coordinates):
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
                'SUPPORT_MAC_BLOCKING=true',
                'VANETZA_IGNORE_OWN_MESSAGES',
                f'VANETZA_LATITUDE={rsu_coordinates[idx-1][0]}',
                f'VANETZA_LONGITUDE={rsu_coordinates[idx-1][1]}'
            ],
            'networks': {
                'vanetzalan0': {
                    'ipv4_address': generate_ipv4_address(idx)
                }
            },
            'volumes': [
            	'./tools/socktap/config.ini:/config.ini'
            ]
        }
    
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
                'SUPPORT_MAC_BLOCKING=true',
                'VANETZA_IGNORE_OWN_MESSAGES'
            ],
            'networks': {
                'vanetzalan0': {
                    'ipv4_address': generate_ipv4_address(num_rsus + idx)
                }
            },
            'volumes': [
            	'./tools/socktap/config.ini:/config.ini'
            ]
        }
        
    services["central"] = {
    	'hostname': 'central',
    	'restart': 'always',
            'image': 'code.nap.av.it.pt:5050/mobility-networks/vanetza:latest',
            'cap_add': ['NET_ADMIN'],
            'environment': [
                'VANETZA_STATION_ID=0',
                'VANETZA_STATION_TYPE=0',
                'VANETZA_MAC_ADDRESS=6e:06:e0:03:00:00',
                'VANETZA_INTERFACE=br0',
                'START_EMBEDDED_MOSQUITTO=true',
                'SUPPORT_MAC_BLOCKING=true',
                'VANETZA_IGNORE_OWN_MESSAGES'
            ],
            'networks': {
                'vanetzalan0': {
                    'ipv4_address': '192.168.98.5'
                }
            },
            'volumes': [
            	'./tools/socktap/config.ini:/config.ini'
            ]
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
        yaml.dump(config, file, default_flow_style=False, sort_keys=False)

def main():
    if len(sys.argv) != 4:
        print("Usage: script.py <num_rsus> <num_obus> <RSUs coordinates")
        sys.exit(1)

    num_rsus = int(sys.argv[1])
    num_obus = int(sys.argv[2])
    rsu_coordinates = sys.argv[3]
    rsu_coordinates = ast.literal_eval(rsu_coordinates)
    
    config = create_rsu_obu_config(num_rsus, num_obus, rsu_coordinates)
    write_docker_compose_file(config)
    
    subprocess.run(["docker-compose", "up", "-d"], check=True)

    for idx in range(1, num_rsus + 1):
        rsu_service_name = f'rsu{idx}'
        wait_for_container(rsu_service_name)
        mac_addresses = [generate_mac_address(obu_idx) for obu_idx in range(1, num_obus + num_rsus + 1)]
        block_communications(rsu_service_name, mac_addresses)

if __name__ == "__main__":
    main()
