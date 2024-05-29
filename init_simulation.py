import random
import time
import paho.mqtt.client as mqtt
import json
from geopy import distance
from geopy.distance import geodesic
import sys
import yaml
import ast

rsu_clients = []
obu_clients = []

def on_connect(client, userdata, flags, rc, properties):
    print("Connected with result code " + str(rc))

def on_message(client, userdata, message):
    msg = message.payload.decode('utf-8')
    obj = json.loads(msg)

def is_in_range(obu_lat, obu_lon, coordinates):
    for c in coordinates:
        if (distance.distance((obu_lat, obu_lon), (c[0], c[1])).meters) <= rsu_range:
            return True
    return False

def generate_random_path(start, end, num_points=10):
    path = [start]
    for _ in range(num_points - 2):
        mid_lat = random.uniform(min(start[0], end[0]), max(start[0], end[0]))
        mid_lon = random.uniform(min(start[1], end[1]), max(start[1], end[1]))
        path.append((mid_lat, mid_lon))
    path.append(end)
    return path

#need to fix this function, the obu is going back and forth
def simulate_obu_movement(start, end, speed=500, step_delay=1):
    path = generate_random_path(start, end)
    current_pos = start
    
    for waypoint in path:
        while geodesic(current_pos, waypoint).meters > speed:
            direction_lat = waypoint[0] - current_pos[0]
            direction_lon = waypoint[1] - current_pos[1]
            distance = geodesic(current_pos, waypoint).meters
            move_lat = speed * (direction_lat / distance)
            move_lon = speed * (direction_lon / distance)
            current_pos = (current_pos[0] + move_lat, current_pos[1] + move_lon)
            
            rsu_in_range = is_in_range(current_pos[0], current_pos[1], rsus_coordinates)
            if rsu_in_range:
                print(f"OBU at {current_pos} is within range of RSU at {rsu_in_range}")
                #unblock the obu<->rsu with docker-compose exec
                #publish_to_rsu(rsu_in_range, current_pos)
            else:
                print(f"OBU at {current_pos} is not in range of any RSU")
                #block the obu<->rsu with docker-compose exec
                
            time.sleep(step_delay)
        
        current_pos = waypoint
        rsu_in_range = is_in_range(current_pos[0], current_pos[1], rsus_coordinates)
        if rsu_in_range:
            print(f"OBU at {current_pos} is within range of RSU at {rsu_in_range}")
            #publish_to_rsu(rsu_in_range, current_pos)
        else:
            print(f"OBU at {current_pos} is not in range of any RSU")

    print(f"OBU reached final destination at {end}")

def get_ips_from_docker_compose(filename):
    with open(filename, 'r') as file:
        docker_config = yaml.safe_load(file)
        rsu_ips = [docker_config['services'][service]['networks']['vanetzalan0']['ipv4_address'] for service in docker_config['services'] if service.startswith('rsu')]
        obu_ips = [docker_config['services'][service]['networks']['vanetzalan0']['ipv4_address'] for service in docker_config['services'] if service.startswith('obu')]
        return rsu_ips, obu_ips

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

# MQTT publish function to update OBUs latitude and longitude, probably need to change the topic to CAM
def publish_to_rsu(client, rsu_id, position):
    topic = f"obu_position"
    payload = {
        "position": {
            "lat": position[0],
            "lon": position[1]
        }
    }
    client.publish(topic, json.dumps(payload))

def main():
    if len(sys.argv) != 4:
        print("Usage: script.py <num_rsus> <num_obus> <RSUs range>")
        sys.exit(1)
    num_rsus = int(sys.argv[1])
    num_obus = int(sys.argv[2])
    global rsu_range
    rsu_range = int(sys.argv[3])
    
    global rsus_coordinates
    rsus_coordinates = get_rsu_coordinates('docker-compose.yml')

    rsu_ips, obu_ips = get_ips_from_docker_compose('docker-compose.yml')
    
    rsu_ids = list(range(1, num_rsus + 1))
    for rsu_id, rsu_ip in zip(rsu_ids, rsu_ips):
        rsu_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"rsu{rsu_id}") 
        rsu_client.on_connect = on_connect
        rsu_client.on_message = on_message
        rsu_client.connect(rsu_ip, 1883)
        rsu_client.loop_start()
        rsu_clients.append(rsu_client)
        print(f"RSU {rsu_id} connected to {rsu_ip}")

    obu_ids = list(range(1, num_obus + 1))
    for obu_id, obu_ip in zip(obu_ids, obu_ips):
        obu_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"obu{obu_id}") 
        obu_client.on_connect = on_connect
        obu_client.on_message = on_message
        obu_client.connect(obu_ip, 1883)
        obu_client.loop_start()
        obu_clients.append(obu_client)
        print(f"obu {obu_id} connected to {obu_ip}")

    start_position = (40.0, -8.0)
    end_position = (40.2, -8.0)
    simulate_obu_movement(start_position, end_position, speed=500, step_delay=1)  # Speed in meters per step

    try:
        while True:
            pass
    except KeyboardInterrupt:
        for client in rsu_clients:
            client.disconnect()
            client.loop_stop()

        for client in obu_clients:
            client.disconnect()
            client.loop_stop()

if __name__ == "__main__":
    main()
