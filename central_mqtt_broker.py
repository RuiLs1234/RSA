"""import json
import paho.mqtt.publish as publish
import time

broker_address = "localhost"
broker_port = 1883

rsu_topic = ["vanetza/out/cam","vanetza/out/denm"]

f = open('examples/in_cam.json')
    m = json.load(f)
    m["latitude"] = 0
    m["longitude"] = 0
    m = json.dumps(m)
    client.publish("vanetza/in/cam",m)
    f.close()

rsus = [
    {"ip": "192.168.98.10", "topic": rsu_topic[0], "message": rsu_message},
    {"ip": "192.168.98.20", "topic": rsu_topic[0], "message": rsu_message},
    {"ip": "192.168.98.30", "topic": rsu_topic[0], "message": rsu_message}
]

while True:
    try:
        for rsu in rsus:
            publish.single(rsu["topic"], rsu["message"], hostname=broker_address, port=broker_port)
            print(f"Message '{rsu['message']}' published to topic '{rsu['topic']}' from RSU with IP '{rsu['ip']}'")
        time.sleep(5)  # Adjust the delay between messages as needed
    except Exception as e:
        print(f"Error: {e}")"""
import json
import paho.mqtt.publish as publish
import time
import paho.mqtt.client as mqtt
import threading

broker_address = "localhost"
broker_port = 1883
rsu_topic = ["vanetza/out/cam","vanetza/out/denm"]
rsus = [
    {"ip": "192.168.98.10", "topic": rsu_topic[0], "message": "HELLO"},
    {"ip": "192.168.98.20", "topic": rsu_topic[0], "message": "HELLO"},
    {"ip": "192.168.98.30", "topic": rsu_topic[0], "message": "HELLO"}
]

def connect_and_subscribe(ip, topic):
    def on_message(client, userdata, message):
        print(f"Received message from RSU at {ip}: {message.payload.decode()}")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    client.on_message = on_message

    client.connect(broker_address, broker_port)
    client.subscribe(topic)
    client.loop_forever()

threads = []
for rsu in rsus:
    thread = threading.Thread(target=connect_and_subscribe, args=(rsu['ip'], rsu['topic']))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()
