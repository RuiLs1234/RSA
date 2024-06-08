import json
import paho.mqtt.client as mqtt
import threading
from time import sleep
import sys
import yaml
import re
import ast
import math

obu_clients = []
first_carriage_coord = []
lost_obus = []

def on_connect(client, userdata, flags, rc, properties):
    client.subscribe("vanetza/out/cam")
    client.subscribe("vanetza/out/denm")

def on_message(client, userdata, message):
    client_id = client._client_id.decode('utf-8')
    msg = message.payload.decode('utf-8')
    obj = json.loads(msg)

    global obu1_id, lost_obus, num_rsus
    if message.topic == "vanetza/out/cam" and obj["stationID"] == int(obu1_id) and client_id == "obu1":
        first_carriage_coord[0] = float(obj["latitude"])
        first_carriage_coord[1] = float(obj["longitude"])
    if message.topic == "vanetza/out/cam" and str(obj["driveDirection"]) != "FORWARD":
        index = obj["stationID"] - num_rsus - 1
        if 0 <= index < num_obus not in lost_obus: 
            lost_obus.append(index)
            lost_obus = list(set(lost_obus))
        print(lost_obus)

def generate():
    global num_obus, obu1_id, lost_obus
    if first_carriage_coord != []:
        for i in range(num_obus):
            if i not in lost_obus:
                with open('examples/in_cam.json') as f:
                    m = json.load(f)
                    m["stationID"] = int(obu1_id) + i
                    m["latitude"] = float(first_carriage_coord[0]) - (i * 0.0002)
                    m["longitude"] = float(first_carriage_coord[1])
                    m = json.dumps(m)
                    obu_clients[i].publish("vanetza/in/cam", m)
                f.close()
                sleep(0.1)
    
def get_ips_from_docker_compose(filename):
    with open(filename, 'r') as file:
        docker_config = yaml.safe_load(file)
        obu_ips = [docker_config['services'][service]['networks']['vanetzalan0']['ipv4_address'] for service in docker_config['services'] if service.startswith('obu')]
        return obu_ips

def get_obu1_id(filename):
    with open(filename, 'r') as file:
        docker_config = yaml.safe_load(file)
        for env_var in docker_config['services']['obu1']['environment']:
            if env_var.startswith('VANETZA_STATION_ID='):
                return env_var.split('=')[1]

def main():
    if len(sys.argv) != 5:
        print("Usage: script.py <num_rsus> <num_obus> <OBU start coordinates> <OBU final coordinates")
        sys.exit(1)

    global num_rsus
    num_rsus = int(sys.argv[1])
    global num_obus
    num_obus = int(sys.argv[2])
    obu1 = sys.argv[3]
    obu1_coord = re.sub(r'[^\d,.-]', '', obu1)
    global first_carriage_coord
    first_carriage_coord = obu1_coord.split(',')
    final_coordinates = sys.argv[4]
    final_coordinates = ast.literal_eval(final_coordinates)

    obu_ips = get_ips_from_docker_compose('docker-compose.yml')
    global obu1_id
    obu1_id = get_obu1_id('docker-compose.yml')

    obu_ids = list(range(1, num_obus + 1))
    for obu_id, obu_ip in zip(obu_ids, obu_ips):
        obu_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"obu{obu_id}") 
        obu_client.on_connect = on_connect
        obu_client.on_message = on_message
        obu_client.connect(obu_ip, 1883)
        obu_client.loop_start()
        obu_clients.append(obu_client)
        print(f"obu {obu_id} connected to {obu_ip}")

    try:
        while not (math.isclose(final_coordinates[0], float(first_carriage_coord[0]), abs_tol=0.001) and
                   math.isclose(final_coordinates[1], float(first_carriage_coord[1]), abs_tol=0.001)):
            generate()
            print(first_carriage_coord)
        for client in obu_clients:
            client.disconnect()
            client.loop_stop()
        return
    except KeyboardInterrupt:
        for client in obu_clients:
            client.disconnect()
            client.loop_stop()

if __name__ == "__main__":
    main()