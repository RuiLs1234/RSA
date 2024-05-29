import paho.mqtt.client as mqtt
import json
import sys
import yaml
import time

rsu_clients = []
central_broker = None
processed_messages = set()

def on_connect(client, userdata, flags, rc, properties=None):
    client_id = client._client_id.decode('utf-8')
    print(f"Connected to {client_id} with result code {rc}")
    #if client_id == "central_broker":
    client.subscribe("vanetza/out/denm")
    #    print(f"{client_id} subscribed to vanetza/out/denm")
    #else:
    #    client.subscribe("vanetza/out/denm")
    #    print(f"{client_id} subscribed to trainInfo")

def on_message(client, userdata, message):
    msg = message.payload.decode('utf-8')
    obj = json.loads(msg)
    
    if message.topic == "vanetza/out/denm":
        sequence_number = obj['fields']['denm']['management']['actionID']['sequenceNumber']
        if not sequence_number in processed_messages:
            print(f"Received DENM from {client._client_id.decode('utf-8')}")
            forward_denm_to_rsus(obj)
            processed_messages.add(sequence_number)
        else:
            return
            
def forward_denm_to_rsus(data):
    payload = data['fields']['denm']        
    result = central_broker.publish("vanetza/in/denm", json.dumps(payload, indent=4))
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"Successfully published to denm")
    else:
        print(f"Failed to publish to denm with result code {result.rc}")

def get_ips_from_docker_compose(filename):
    with open(filename, 'r') as file:
        docker_config = yaml.safe_load(file)
        rsu_ips = [docker_config['services'][service]['networks']['vanetzalan0']['ipv4_address'] for service in docker_config['services'] if service.startswith('rsu')]
        central_broker_ip = docker_config['services']['central']['networks']['vanetzalan0']['ipv4_address']
        return rsu_ips, central_broker_ip

def main():
    if len(sys.argv) != 2:
        print("Usage: script.py <num_rsus>")
        sys.exit(1)

    num_rsus = int(sys.argv[1])

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

    global central_broker
    central_broker = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="central_broker")
    central_broker.on_connect = on_connect
    central_broker.on_message = on_message
    central_broker.connect(central_broker_ip, 1883)
    central_broker.loop_start()
    print("Central broker connected")

    try:
        while True:
            pass
    except KeyboardInterrupt:
        for client in rsu_clients + [central_broker]:
            client.disconnect()
            client.loop_stop()

if __name__ == "__main__":
    main()
