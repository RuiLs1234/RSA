import random
import time
import paho.mqtt.client as mqtt
import json
from geopy import distance
from geopy.distance import geodesic
import sys
import yaml
import ast
import subprocess

obu_clients = []
simulation = None
disaster_struck = 0

def on_connect(client, userdata, flags, rc, properties):
    client_id = client._client_id.decode('utf-8')

def on_message(client, userdata, message):
    msg = message.payload.decode('utf-8')
    obj = json.loads(msg)

def is_in_range(obu_lat, obu_lon, coordinates):
    in_range = []
    for c in coordinates:
        if (distance.distance((obu_lat, obu_lon), (c[0], c[1])).meters) <= rsu_range:
            for idx in range(num_rsus):
                if c[0] == rsus_coordinates[idx][0] and c[1] == rsus_coordinates[idx][1]:
                    in_range.append(f'rsu{idx+1}')
            return [True, in_range]
    return [False, None]

def generate_random_path(start, end, num_points=10):
    path = [start]
    i = 1
    while i < num_points - 2:
        mid_lat = random.uniform(start[0], end[0])
        mid_lon = random.uniform(start[1], end[1])
        if abs(mid_lat) > abs(path[i-1][0]) or abs(mid_lon) > abs(path[i-1][1]):
            path.append((mid_lat, mid_lon))
            i = i + 1
    path.append(end)
    global disaster_coordinate
    disaster_coordinate = (
        random.uniform(start[0], end[0]),
        random.uniform(start[1], end[1]),
    )
    return path

def simulate_obu_movement(start, end, speed, step_delay=1):
    path = generate_random_path(start, end)
    global current_pos, disaster_struck, lost_obu_id
    current_pos = start
    unblocked_rsus = set()
    obu_mac_addresses = get_mac_addresses('docker-compose.yml', 'obu')
    for waypoint in path:
        while geodesic(current_pos, waypoint).meters > speed:
            direction_lat = waypoint[0] - current_pos[0]
            direction_lon = waypoint[1] - current_pos[1]
            distance = geodesic(current_pos, waypoint).meters
            move_lat = speed * (direction_lat / distance)
            move_lon = speed * (direction_lon / distance)
            current_pos = (current_pos[0] + move_lat, current_pos[1] + move_lon)
            generate_cam(current_pos)
            if (disaster_struck == 0):
                if disaster_coordinate[0] > start[0] and current_pos[0] >= disaster_coordinate[0] or disaster_coordinate[0] < start[0] and current_pos[0] <= disaster_coordinate[0]:
                    generate_cam_for_lost_obu(current_pos)
                    block_obu_to_obu_communication() 
                if disaster_coordinate[1] > start[1] and current_pos[1] >= disaster_coordinate[1] or disaster_coordinate[1] < start[1] and current_pos[1] <= disaster_coordinate[1]:
                    generate_cam_for_lost_obu(current_pos)
                    block_obu_to_obu_communication()
            rsu_in_range = is_in_range(current_pos[0], current_pos[1], rsus_coordinates)
            if rsu_in_range[0]:
                new_unblocked_rsus = set(rsu_in_range[1])
                for rsu in new_unblocked_rsus:
                    if rsu not in unblocked_rsus:
                        print(f"OBU at {current_pos} is within range of RSU {rsu}")
                        for obu_mac_address in obu_mac_addresses:
                            if int(obu_mac_address[-1]) != lost_obu_id:
                                command = ["docker-compose", "exec", rsu, "unblock", obu_mac_address]
                                try:
                                    subprocess.run(command, check=True)
                                    print(f"Successfully unblocked MAC address {obu_mac_address} on {rsu}")
                                except subprocess.CalledProcessError as e:
                                    print(f"Failed to run command {command}: {e}")
                    
                unblocked_rsus.clear()
                unblocked_rsus.update(new_unblocked_rsus)
            else:
                new_unblocked_rsus = set()
                print(f"OBU at {current_pos} is not in range of any RSU")

            for rsu in unblocked_rsus.difference(new_unblocked_rsus):
                print(f"OBU at {current_pos} is not in range of RSU {rsu}")
                for obu_mac_address in obu_mac_addresses:
                    if int(obu_mac_address[-1]) != lost_obu_id:
                        command = ["docker-compose", "exec", rsu, "block", obu_mac_address]
                        try:
                            subprocess.run(command, check=True)
                            print(f"Successfully blocked MAC address {obu_mac_address} on {rsu}")
                        except subprocess.CalledProcessError as e:
                            print(f"Failed to run command {command}: {e}")
            unblocked_rsus = new_unblocked_rsus

            time.sleep(step_delay)

    print(f"OBU reached final destination at {end}")
    return

def get_ips_from_docker_compose(filename):
    with open(filename, 'r') as file:
        docker_config = yaml.safe_load(file)
        obu_ips = [docker_config['services'][service]['networks']['vanetzalan0']['ipv4_address'] for service in docker_config['services'] if service.startswith('obu')]
        return obu_ips

def get_rsu_coordinates(filename):
    with open(filename, 'r') as file:
        docker_config = yaml.safe_load(file)
        rsu_coordinates = []
        for service in docker_config['services']:
            if service.startswith('rsu'):
                lat = None
                lon = None
                for env_var in docker_config['services'][service]['environment']:
                    if env_var.startswith('VANETZA_LATITUDE='):
                        lat = float(env_var.split('=')[1])
                    elif env_var.startswith('VANETZA_LONGITUDE='):
                        lon = float(env_var.split('=')[1])
                if lat is not None and lon is not None:
                    rsu_coordinates.append((lat, lon))
        
    return rsu_coordinates

def get_mac_addresses(filename, serv):
    with open(filename, 'r') as file:
        docker_config = yaml.safe_load(file)
        mac_addresses = []
        for service in docker_config['services']:
            if service.startswith(serv):
                mac_address = None
                for env_var in docker_config['services'][service]['environment']:
                    if env_var.startswith('VANETZA_MAC_ADDRESS='):
                        mac_address = (env_var.split('=')[1])
                if mac_address is not None:
                    mac_addresses.append(mac_address)
        
    return mac_addresses

def block_obu_to_obu_communication():
    obu_mac_addresses = get_mac_addresses('docker-compose.yml', 'obu')
    global disaster_struck
    disaster_struck = 1
    for i in range(1, num_obus + 1):
        service_name = f'obu{i}'
        for mac_address in obu_mac_addresses:
            if int(mac_address[-1]) - num_rsus != i and int(mac_address[-1]) - num_rsus == lost_obu_id:
                command = [
                    "docker-compose", "exec", service_name,
                    "block", mac_address
                ]
                try:
                    subprocess.run(command, check=True)
                    print(f"Successfully blocked MAC address {mac_address} on {service_name}")
                except subprocess.CalledProcessError as e:
                    print(f"Failed to run command {command}: {e}")
            if service_name == f'obu{lost_obu_id}' and int(mac_address[-1]) - num_rsus != lost_obu_id:
                command = [
                    "docker-compose", "exec", service_name,
                    "block", mac_address
                ]
                try:
                    subprocess.run(command, check=True)
                    print(f"Successfully blocked MAC address {mac_address} on {service_name}")
                except subprocess.CalledProcessError as e:
                    print(f"Failed to run command {command}: {e}")
    return 

def generate_cam(current_pos):
    with open('docker-compose.yml', 'r') as file:
        docker_config = yaml.safe_load(file)
        for env_var in docker_config['services']['obu1']['environment']:
            if env_var.startswith('VANETZA_STATION_ID='):
                stationID = (env_var.split('=')[1])

    global simulation
    with open('examples/in_cam.json') as f:
        m = json.load(f)
        m["stationID"] = int(stationID)
        m["latitude"] = current_pos[0]
        m["longitude"] = current_pos[1]
        m = json.dumps(m)
        simulation.publish("vanetza/in/cam",m)
    f.close()
    time.sleep(0.2)

def generate_cam_for_lost_obu(current_pos):
    obu_mac_addresses = get_mac_addresses('docker-compose.yml', 'obu')
    global num_rsus, rsus_coordinates
    in_range = is_in_range(current_pos[0], current_pos[1], rsus_coordinates)
    if in_range[0]:
        for _ in range(3):
            print("HELP!")
            for mac_address in obu_mac_addresses:
                if int(mac_address[-1]) - num_rsus >= lost_obu_id:
                    client = obu_clients[int(mac_address[-1]) - num_rsus - 1]
                    f = open('examples/in_cam.json')
                    m = json.load(f)
                    m["stationID"] = int(mac_address[-1])
                    m["latitude"] = current_pos[0]
                    m["longitude"] = current_pos[1]
                    m["driveDirection"] = str("STOP")
                    m = json.dumps(m)
                    client.publish("vanetza/in/cam",m)
                    simulation.publish("vanetza/in/cam", m)
                    f.close()

def main():
    if len(sys.argv) != 8:
        print("Usage: script.py <num_rsus> <num_obus> <RSUs range> <OBU velocity> <OBU start coordinates> <OBU end coordinates> <OBU to lose>")
        sys.exit(1)
    global num_rsus
    num_rsus = int(sys.argv[1])
    global num_obus
    num_obus = int(sys.argv[2])
    global rsu_range
    rsu_range = int(sys.argv[3])
    train_velocity = int(sys.argv[4])
    start_position = sys.argv[5]
    start_position = ast.literal_eval(start_position)
    end_position = sys.argv[6]
    end_position = ast.literal_eval(end_position)
    global lost_obu_id
    lost_obu_id = int(sys.argv[7])

    global rsus_coordinates
    rsus_coordinates = get_rsu_coordinates('docker-compose.yml')

    obu_ips = get_ips_from_docker_compose('docker-compose.yml')

    obu_ids = list(range(1, num_obus + 1))
    for obu_id, obu_ip in zip(obu_ids, obu_ips):
        obu_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"obu{obu_id}") 
        obu_client.on_connect = on_connect
        obu_client.on_message = on_message
        obu_client.connect(obu_ip, 1883)
        obu_client.loop_start()
        obu_clients.append(obu_client)
        print(f"obu {obu_id} connected to {obu_ip}")

    global simulation
    simulation = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="simulation")
    simulation.on_connect = on_connect
    simulation.on_message = on_message
    simulation.connect("192.168.98.6", 1883)
    simulation.loop_start()
    print("Simulation client connected")

    simulate_obu_movement(start_position, end_position, ((train_velocity*1000)/3600), step_delay=0.5)  # Speed in meters per step

    try:
        while True:
            pass
    except KeyboardInterrupt:
        for client in obu_clients:
            client.disconnect()
            client.loop_stop()

        simulation.disconnect()
        simulation.loop_stop()

if __name__ == "__main__":
    main()
