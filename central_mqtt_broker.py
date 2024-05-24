import paho.mqtt.client as mqtt
import json
import sys
import yaml

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("vanetza/out/cam")
    client.subscribe("vanetza/out/denm")

def on_message(client, userdata, message):
    #print("Received message '" + str(message.payload) + "' on topic '"
          #+ message.topic + "' with QoS " + str(message.qos))
    
    msg = json.loads(message)
    if((msg['stationID'] == 4) and (msg['receiverID'] in [1,2,3])): 
        print("Received message '" + str(message.payload) + "' on topic '"
        + message.topic + "' with QoS " + str(message.qos))

def get_ips_from_docker_compose(filename):
    with open(filename, 'r') as file:
        docker_config = yaml.safe_load(file)
        rsu_ips = [docker_config['services'][service]['networks']['vanetzalan0']['ipv4_address'] for service in docker_config['services'] if service.startswith('rsu')]
        central_broker_ip = "192.168.98.100" #docker_config['services']['central_broker']['networks']['vanetzalan0']['ipv4_address']
        return rsu_ips, central_broker_ip

num_rsus = int(sys.argv[1])

rsu_ips, central_broker_ip = get_ips_from_docker_compose('docker-compose.yml')

rsu_clients = []
rsu_ids = list(range(1, num_rsus + 1))
for rsu_id, rsu_ip in zip(rsu_ids, rsu_ips):
    rsu_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    rsu_client.on_connect = on_connect
    rsu_client.on_message = on_message
    rsu_client.connect(rsu_ip, 1883)
    rsu_client.loop_start()
    rsu_clients.append(rsu_client)

central_broker = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
central_broker.on_connect = on_connect
central_broker.on_message = on_message
central_broker.connect(central_broker_ip, 1883)
central_broker.loop_start()

for rsu_client in rsu_clients:
    rsu_client.publish("vanetza/in/cam", "Message to cam topic")
    rsu_client.publish("vanetza/in/denm", "Message to denm topic")

central_broker.publish("#", "Message to central broker")

while True:
    pass