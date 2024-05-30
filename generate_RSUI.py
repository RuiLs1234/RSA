import json
import paho.mqtt.client as mqtt
import threading
from time import sleep
import sys
import yaml


global_count = []
obj = {}
range_RSU = 0
rsu_clients = []

def get_ips_from_docker_compose(filename):
    with open(filename, 'r') as file:
        docker_config = yaml.safe_load(file)
        rsu_ips = [docker_config['services'][service]['networks']['vanetzalan0']['ipv4_address'] for service in docker_config['services'] if service.startswith('rsu')]
        central_broker_ip = docker_config['services']['central']['networks']['vanetzalan0']['ipv4_address']
        return rsu_ips, central_broker_ip

def on_connect(client, userdata, flags, rc):
    global obj
    print("Connected with result code "+str(rc))
    obj = client.subscribe("vanetza/out/cam")
    print(obj)


def on_message(client, userdata, msg):
    global obj
    
    #print('Topic: ' + msg.topic)
    #print('Message: ' + msg.payload.decode('utf-8'))

    obj = json.loads(msg.payload.decode('utf-8'))

def generate(ovus, size):
    global global_count
    global range_RSU
    global obj
    
    if str(obj) != "(<MQTTErrorCode.MQTT_ERR_SUCCESS: 0>, 1)":
        for i in range(size):
                        if obj["heading"] not in global_count[i]:
                            global_count[i].append(obj["heading"])                                        
                        else:
                            if ovus != len(global_count[i]) and global_count[i] != 0:     
                                with open('examples/in_denm.json') as f:
                                        m = json.load(f)
                                        m["situation"]["eventType"]["causeCode"] = 94
                                        m = json.dumps(m)
                                        client.publish("vanetza/in/denm",m)
                            sleep(1)
                            f.close()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

num_rsus = int(sys.argv[1])
total_RSU = int(sys.argv[1])

rsu_ips, central_broker_ip = get_ips_from_docker_compose('docker-compose.yml')
rsu_ids = list(range(1, num_rsus + 1))
for rsu_id, rsu_ip in zip(rsu_ids, rsu_ips):
        rsu_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"rsu{rsu_id}") 
        rsu_client.on_connect = on_connect
        rsu_client.on_message = on_message
        rsu_client.connect(rsu_ip, 1883)
        rsu_client.loop_start()
        rsu_clients.append(rsu_client)
        print(f"RSU {rsu_id} connected to {rsu_ip}")
total_ovu = int(sys.argv[2])
total_RSU_latitude = list(map(float, sys.argv[3].split(',')))
total_RSU_longitude = list(map(float, sys.argv[4].split(',')))
range_RSU = float(sys.argv[5])

if not global_count:
    global_count = [[] for _ in range(total_RSU)]


threading.Thread(target=client.loop_forever).start()

try:
    while True:
        for i in range(total_RSU):
            generate(total_ovu, total_RSU)

except KeyboardInterrupt:
        for client in rsu_clients:
            client.disconnect()
            client.loop_stop()
