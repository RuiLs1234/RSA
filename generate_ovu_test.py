import json
import paho.mqtt.client as mqtt
import threading
from time import sleep

# Global variables to store coordinates and state
global_count = []
obj = {}
latitude = [0, 0, 0]
longitude = [0, 0, 0]
total_RSU_latitude = []
total_RSU_longitude = []
point_reach = 0

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("vanetza/out/cam")

def on_message(client, userdata, msg):
    global obj

    print('Topic: ' + msg.topic)
    print('Message' + msg.payload.decode('utf-8'))

    objt = json.loads(msg.payload.decode('utf-8'))
    obj = objt

def generate(i, total_RSU, do_not_do):
    global longitude
    global latitude
    global point_reach
    global total_RSU_latitude
    global total_RSU_longitude

    if i == 0 and do_not_do != i:
        with open('examples/in_cam.json') as f:
            m = json.load(f)
            m["heading"] = i
            m = json.dumps(m)
            client.publish("vanetza/in/cam", m)
            sleep(1)
        f.close()
    elif do_not_do != i:
        with open('examples/in_cam.json') as f:
            m = json.load(f)
            m["heading"] = i
            m = json.dumps(m)
            client.publish("vanetza/in/cam", m)
            sleep(1)
        f.close()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

total_RSU = 2
total_ovu = 3

client.connect("192.168.98.10", 1883, 60)

total_RSU_latitude = [2, 4]
total_RSU_longitude = [2, 4]
do_not_do = 1

# Start MQTT client loop in a separate thread
threading.Thread(target=client.loop_forever).start()

while True:
    i = 0
    while i < total_ovu:
        generate(i, total_RSU, do_not_do)
        i = i+1





