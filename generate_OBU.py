import json
import paho.mqtt.client as mqtt
import threading
from time import sleep
import sys

global_count = []
obj = {}
latitude = []
longitude = []


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("vanetza/out/cam")
    # client.subscribe("vanetza/out/denm")
    # ...


# É chamada automaticamente sempre que recebe uma mensagem nos tópicos subscritos em cima
def on_message(client, userdata, msg):
    message = msg.payload.decode('utf-8')
    global obj
    
    print('Topic: ' + msg.topic)
    print('Message' + message)

    objt = json.loads(message)
    obj = objt

    # lat = obj["latitude"]
    # ...
    
def generate(i):
    global longitude
    global latitude
    if i == 0:
        f = open('examples/in_cam.json')
        m = json.load(f)
        m["accEngaged"] = "Hello"
        m["latitude"] = latitude[i]
        latitude[i] = latitude[i]+1
        m["longitude"] = longitude[i]
        longitude[i] = longitude[i]+1
        m = json.dumps(m)
        client.publish("vanetza/in/cam",m)
        f.close()
        sleep(1) 
    else:
        f = open('examples/in_cam.json')
        m = json.load(f)
        m["accEngaged"] = "Hello part"
        m["latitude"] = latitude[i]
        latitude[i] = latitude[i]+1
        m["longitude"] = longitude[i]
        longitude[i] = longitude[i]+1
        m = json.dumps(m)
        client.publish("vanetza/in/cam",m)
        f.close()
        sleep(1) 

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("192.168.98.10", 1883, 60)
total_ovu = sys.argv[2]
total_OVU_latitude = sys.argv[5]
total_OVU_longitude = sys.argv[6]
if latitude == []:
    i = 0
    while total_ovu > i:
        latitude.append(total_OVU_latitude[5][i])
        longitude.append(total_OVU_longitude[6][i])
        i = i+1


threading.Thread(target=client.loop_forever).start()

while(True):
    i = 0
    while i < total_ovu:
        generate(i)
        i = i+1
