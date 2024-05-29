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
    global total_RSU_latitude
    global total_RSU_longitude

    if i == 0:
        with open('examples/in_cam.json') as f:
            m = json.load(f)
            m["accEngaged"] = "Hello"
            m["heading"] = i
            m["latitude"] = latitude[i]
            m["longitude"] = longitude[i]
            
            if point_reach < total_RSU: 
                if latitude[i] < total_RSU_latitude[point_reach]:
                    latitude[i] = latitude[i] + 1 
                if longitude[i] < total_RSU_longitude[point_reach]:
                    longitude[i] = longitude[i] + 1
            
            if latitude[i] == total_RSU_latitude[point_reach] and longitude[i] == total_RSU_longitude[point_reach]:
                point_reach = point_reach + 1
            
            m = json.dumps(m)
            client.publish("vanetza/in/cam", m)
            sleep(1)
    else:
        with open('examples/in_cam.json') as f:
            m = json.load(f)
            m["accEngaged"] = "Hello part"
            m["latitude"] = latitude[i]
            m["heading"] = i
            latitude[i] = latitude[i-1] - 1
            m["longitude"] = longitude[i]
            longitude[i] = longitude[i-1] - 1
            m = json.dumps(m)
            client.publish("vanetza/in/cam", m)
            sleep(1)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

total_RSU = int(sys.argv[1])
total_ovu = int(sys.argv[2])

u = 0
while u < total_ovu:    
    client.connect("192.168.98." + str(u) + "5", 1883, 60) #Criar um client para cada RSU
    u = u + 1

total_RSU_latitude = list(map(float, sys.argv[3].split(',')))
total_RSU_longitude = list(map(float, sys.argv[4].split(',')))

if not latitude:
    set_limit_latitude = max(total_RSU_latitude)
    set_limit_longitude = max(total_RSU_longitude)
    
    for g in range(total_ovu):
        if set_limit_longitude < total_RSU:
            longitude.append(0)
        else:
            longitude.append(total_RSU_longitude[0] - (5 + total_ovu))
            
        if set_limit_latitude < total_RSU:
            latitude.append(0)
        else:
            latitude.append(total_RSU_latitude[0] - (5 + total_ovu))

threading.Thread(target=client.loop_forever).start()

while True:
    for i in range(total_ovu):
        generate(i, total_RSU)
