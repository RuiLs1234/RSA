import json
import paho.mqtt.client as mqtt
import threading
from time import sleep
import sys


global_count = []
obj = {}


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
    

def generate(obj, ovus, latitude, longitude, size):
        global global_count
        if obj["accEngaged"] == "Hello part" or obj["accEngaged"] == "Hello":  
            i = 0
            while i < size:
                i = i+1
                if obj["latitude"] <= latitude[i]+2000 and latitude[i]-2000 >= obj["latitude"]:
                    if obj["longitude"] <= longitude[i]+2000 and longitude[i]-2000 >= obj["longitude"]:
                        global_count[i] = global_count[i]+1
                    
                      
        else:
            for number in global_count:
                if ovus != number and number != 0:     
                    f = open('examples/in_dem.json')
                    m = json.load(f)
                    obj["eventType"]["causeCode"] = 94
                    m = json.dumps(m)
                    client.publish("vanetza/in/dem",m)
                    f.close()
                    sleep(1)  
        

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("192.168.98.10", 1883, 60)
total_RSU = sys.argv[1]
total_ovu = sys.argv[2]
total_RSU_latitude = sys.argv[3]
total_RSU_longitude = sys.argv[4]

if global_count == []:
    i = 0
    while i < total_RSU:
        global_count.append(0)
        i = i+1



threading.Thread(target=client.loop_forever).start()

while(True):
    i = 0
    while i < total_RSU:
        i = i+1
        generate(obj, total_ovu, total_RSU_latitude, total_RSU_longitude, total_RSU)
