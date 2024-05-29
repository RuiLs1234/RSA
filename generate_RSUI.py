import json
import paho.mqtt.client as mqtt
import threading
from time import sleep
import sys


global_count = []
obj = {}
range_RSU = 0

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("vanetza/out/cam")
    # client.subscribe("vanetza/out/denm")
    # ...


# É chamada automaticamente sempre que recebe uma mensagem nos tópicos subscritos em cima
def on_message(client, userdata, msg):
    global obj
    
    print('Topic: ' + msg.topic)
    print('Message' + msg.payload.decode('utf-8'))

    objt = json.loads(msg.payload.decode('utf-8'))
    obj = objt

    # lat = obj["latitude"]
    # ...
    

def generate(obj, ovus, latitude, longitude, size):
        global global_count
        global range_RSU
        if obj["accEngaged"] == "Hello part" or obj["accEngaged"] == "Hello":  
            for i in range(size):
                if latitude[i] - range_RSU <= obj["latitude"] <= latitude[i] + range_RSU:
                    if longitude[i] - range_RSU <= obj["longitude"] <= longitude[i] + range_RSU:
                        if obj["heading"] not in global_count[i]:
                            global_count[i].append(obj["heading"])
                    
                      
        else:
            for number in global_count:
                if ovus != len(number) and len(number) != 0:     
                    with open('examples/in_dem.json') as f:
                        m = json.load(f)
                        obj["eventType"]["causeCode"] = 94
                        m = json.dumps(m)
                        client.publish("vanetza/in/dem",m)
                    sleep(1)
        f.close()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

total_RSU = int(sys.argv[1])
total_ovu = int(sys.argv[2])
total_RSU_latitude = list(map(float, sys.argv[3].split(',')))
total_RSU_longitude = list(map(float, sys.argv[4].split(',')))
range_RSU = float(sys.argv[5])

if not global_count:
    global_count = [[] for _ in range(total_RSU)]

for u in range(total_RSU):    
    client.connect("192.168.98." + str(u) + "0", 1883, 60) #Criar um client para cada RSU

threading.Thread(target=client.loop_forever).start()

while True:
    for i in range(total_RSU):
        generate(obj, total_ovu, total_RSU_latitude, total_RSU_longitude, total_RSU)