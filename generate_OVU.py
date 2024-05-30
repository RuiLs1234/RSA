import json
import paho.mqtt.client as mqtt
import threading
from time import sleep
import sys

global_count = []
obj = {}
latitude = []
longitude = []
total_RSU_latitude = []
total_RSU_longitude = []
point_reach = 0

def get_ips_from_docker_compose(filename):
    with open(filename, 'r') as file:
        docker_config = yaml.safe_load(file)
        rsu_ips = [docker_config['services'][service]['networks']['vanetzalan0']['ipv4_address'] for service in docker_config['services'] if service.startswith('rsu')]
        central_broker_ip = docker_config['services']['central']['networks']['vanetzalan0']['ipv4_address']
        return rsu_ips, central_broker_ip

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("vanetza/out/cam")
    # client.subscribe("vanetza/out/denm")
    # ...

def on_message(client, userdata, msg):
    global obj
    
    print('Topic: ' + msg.topic)
    print('Message' + msg.payload.decode('utf-8'))

    objt = json.loads(msg.payload.decode('utf-8'))
    obj = objt

def generate(i, total_RSU):
    global longitude
    global latitude
    global point_reach
    global total_RSU_latitude
    global total_RSU_longitude

    if i == 0 and do_not_do != i:
        with open('examples/in_cam.json') as f:
            m = json.load(f)
            m["driveDirection"] = "Forward"
            m["heading"] = i
            m["latitude"] = latitude[i]
            m["longitude"] = longitude[i]

            if point_reach < total_RSU:
                if latitude[i] < total_RSU_latitude[point_reach]:
                    latitude[i] += 1
                if longitude[i] < total_RSU_longitude[point_reach]:
                    longitude[i] += 1

            if latitude[i] == total_RSU_latitude[point_reach] and longitude[i] == total_RSU_longitude[point_reach] and point_reach != total_RSU-1:
                point_reach += 1

            m = json.dumps(m)
            client.publish("vanetza/in/cam", m)
            sleep(1)
    elif do_not_do != i:
        with open('examples/in_cam.json') as f:
            m = json.load(f)
            m["driveDirection"] = "Follow"
            m["latitude"] = latitude[i]
            m["heading"] = i
            m["longitude"] = longitude[i]

            # Follow the previous coordinate
            latitude[i] = latitude[i-1] - 1
            longitude[i] = longitude[i-1] - 1

            m = json.dumps(m)
            client.publish("vanetza/in/cam", m)
            sleep(1)



total_RSU = int(sys.argv[1])
total_ovu = int(sys.argv[2])

rsu_ips, central_broker_ip = get_ips_from_docker_compose('docker-compose.yml')

global central_broker
client = mqtt.Client()
client.connect(central_broker_ip, 1883)
client.on_connect = on_connect
client.on_message = on_message




total_RSU_latitude = list(map(float, sys.argv[3].split(',')))
total_RSU_longitude = list(map(float, sys.argv[4].split(',')))
do_not_do = sys.argv[6]

for i in range(total_ovu):
    latitude.append(0)
    longitude.append(0)

threading.Thread(target=client.loop_forever).start()

while True:
    for i in range(total_ovu):
        generate(i, total_RSU)