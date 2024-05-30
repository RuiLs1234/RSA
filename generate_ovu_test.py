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

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

total_RSU = 2
total_ovu = 3

client.connect("192.168.98.10", 1883, 60)

total_RSU_latitude = [2, 4]
total_RSU_longitude = [2, 4]
do_not_do = 0

# Start MQTT client loop in a separate thread
threading.Thread(target=client.loop_forever).start()

while True:
    for i in range(total_ovu):
        generate(i, total_RSU, do_not_do)





