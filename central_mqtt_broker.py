import paho.mqtt.client as mqtt
import json
import sys
import yaml
import time

central_broker = None
processed_messages = set()

def on_connect(client, userdata, flags, rc, properties=None):
    client.subscribe("vanetza/out/denm")

def on_message(client, userdata, message):
    msg = message.payload.decode('utf-8')
    obj = json.loads(msg)

    if message.topic == "vanetza/out/denm":
        sequence_number = obj['fields']['denm']['management']['actionID']['sequenceNumber']
        if not sequence_number in processed_messages:
            print("Received DENM")
            forward_denm_to_rsus(obj)
            processed_messages.add(sequence_number)
        else:
            return
            
def forward_denm_to_rsus(data):
    payload = data['fields']['denm']        
    result = central_broker.publish("vanetza/in/denm", json.dumps(payload, indent=4))
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"Successfully published message with topic denm")
    else:
        print(f"Failed to publish to denm with result code {result.rc}")

def get_ips_from_docker_compose(filename):
    with open(filename, 'r') as file:
        docker_config = yaml.safe_load(file)
        central_broker_ip = docker_config['services']['central']['networks']['vanetzalan0']['ipv4_address']
        return central_broker_ip

def main():
    if len(sys.argv) != 1:
        print("Usage: script.py")
        sys.exit(1)

    central_broker_ip = get_ips_from_docker_compose('docker-compose.yml')

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
        central_broker.disconnect()
        central_broker.loop_stop()

if __name__ == "__main__":
    main()
