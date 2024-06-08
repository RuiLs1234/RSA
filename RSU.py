import json
import paho.mqtt.client as mqtt
import threading
from time import sleep
import sys
import yaml
from geopy import distance
import asyncio
import websockets

rsu_clients = []
seq_number = 0
last_carriages_coord = []
lost_obus = []
warned = False

def on_connect(client, userdata, flags, rc, properties=None):
    client.subscribe("vanetza/out/cam")
    client.subscribe("vanetza/out/denm")

def on_message(client, userdata, message):
    current_rsu = 1
    client_id = client._client_id.decode('utf-8')
    msg = message.payload.decode('utf-8')
    obj = json.loads(msg)
    global num_obus, num_rsus, lost_obus, last_carriages_coord

    if message.topic == "vanetza/out/cam" and str(obj["driveDirection"]) != "FORWARD":
        index = obj["stationID"] - num_obus - 1
        if 0 <= index < num_obus:
            last_carriages_coord[index][0] = float(obj["latitude"])
            last_carriages_coord[index][1] = float(obj["longitude"])
            if index not in lost_obus:
                lost_obus.append(index)
                lost_obus = list(set(lost_obus))
        current_rsu = obj["receiverID"]
        
    if message.topic == "vanetza/out/cam" and obj["stationID"] != -1:
        index = obj["stationID"] - num_rsus - 1
        if 0 <= index < num_obus and index not in lost_obus:
            last_carriages_coord[index] = [obj["latitude"], obj["longitude"]]

    if message.topic == "vanetza/out/denm":
        if obj["fields"]["denm"]["situation"]["eventType"]["causeCode"] == 94:
            pass

    if is_obu_lost():
        generate(current_rsu)

def generate(rsu_id):
    global seq_number, num_obus, lost_obus
    with open('examples/in_denm.json') as f:
        m = json.load(f)
    m["management"]["actionID"]["sequenceNumber"] = seq_number
    for i in range(len(lost_obus)):
        coordinates = last_carriages_coord[lost_obus[i]]
        if coordinates:
            m["management"]["eventPosition"]["latitude"] = coordinates[0]
            m["management"]["eventPosition"]["longitude"] = coordinates[1]
    m["management"]["stationType"] = 15
    m["situation"]["eventType"]["causeCode"] = 94
    m["situation"]["eventType"]["subCauseCode"] = len(lost_obus)
    m = json.dumps(m)
    rsu_clients[rsu_id-1].publish("vanetza/in/denm", m)
    seq_number += 1
    num_obus -= len(lost_obus)

def get_ips_from_docker_compose(filename):
    with open(filename, 'r') as file:
        docker_config = yaml.safe_load(file)
        rsu_ips = [docker_config['services'][service]['networks']['vanetzalan0']['ipv4_address'] for service in docker_config['services'] if service.startswith('rsu')]
        return rsu_ips

def is_obu_lost():
    global num_obus, last_carriages_coord, warned
    for i in range(num_obus):
        if last_carriages_coord[i] is not None:
            for j in range(num_obus):
                if i != j and last_carriages_coord[j] is not None and (i == j - 1 or i == j + 1):
                    if distance.distance(last_carriages_coord[i], last_carriages_coord[j]).meters > 100 and not warned:
                        warned = True
                        return True
    return False

async def send_coordinates(websocket, path):
    try:
        while True:
            if all(coord is not None for coord in last_carriages_coord):
                coordinates = [
                    {'lat': float(last_carriages_coord[0][0]), 'lng': float(last_carriages_coord[0][1])},
                    {'lat': float(last_carriages_coord[1][0]), 'lng': float(last_carriages_coord[1][1])},
                    {'lat': float(last_carriages_coord[2][0]), 'lng': float(last_carriages_coord[2][1])}
                ]
                await websocket.send(json.dumps(coordinates))
            await asyncio.sleep(1)
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed: {e}")

def main():
    if len(sys.argv) != 3:
        print("Usage: script.py <num_rsus> <num_obus>")
        sys.exit(1)

    global num_rsus
    num_rsus = int(sys.argv[1])
    global num_obus
    num_obus = int(sys.argv[2])
    global last_carriages_coord
    last_carriages_coord = [None] * num_obus

    rsu_ips = get_ips_from_docker_compose('docker-compose.yml')

    rsu_ids = list(range(1, num_rsus + 1))
    for rsu_id, rsu_ip in zip(rsu_ids, rsu_ips):
        rsu_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"rsu{rsu_id}")
        rsu_client.on_connect = on_connect
        rsu_client.on_message = on_message
        rsu_client.connect(rsu_ip, 1883)
        rsu_client.loop_start()
        rsu_clients.append(rsu_client)
        print(f"RSU {rsu_id} connected to {rsu_ip}")

    start_server = websockets.serve(send_coordinates, "localhost", 8765)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

    try:
        while True:
            pass

    except KeyboardInterrupt:
        for client in rsu_clients:
            client.disconnect()
            client.loop_stop()

if __name__ == "__main__":
    main()
