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
    

def generate(i, total_RSU):
    global longitude
    global latitude
    global total_RSU_latitude
    global total_RSU_longitude
    if i == 0:
        f = open('examples/in_cam.json')
        m = json.load(f)
        m["accEngaged"] = "Hello"
        m["heading"] = i
        m["latitude"] = latitude[i]
        m["longitude"] = longitude[i]
        if point_reach < total_RSU: 
            if latitude[i] < total_RSU_latitude[point_reach]:
                latitude[i] = latitude[i]+1 
            if longitude[i] < total_RSU_longitude[point_reach]:
                longitude[i] = longitude[i]+1
        if latitude[i] == total_RSU_latitude[point_reach] and longitude[i] == total_RSU_longitude[point_reach]:
            point_reach  = point_reach+1
        m = json.dumps(m)
        client.publish("vanetza/in/cam",m)
        f.close()
        sleep(1) 
    else:
        f = open('examples/in_cam.json')
        m = json.load(f)
        m["accEngaged"] = "Hello part"
        m["latitude"] = latitude[i]
        m["heading"] = i
        latitude[i] = latitude[i-1]-1
        m["longitude"] = longitude[i]
        longitude[i] = longitude[i-1]-1
        m = json.dumps(m)
        client.publish("vanetza/in/cam",m)
        f.close()
        sleep(1) 

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
total_RSU = sys.argv[1]
total_ovu = sys.argv[2]
u = 0
while u < total_ovu:    
    client.connect("192.168.98."+u+"5", 1883, 60) #Criar um client para cada RSU
    u = u+1
total_RSU_latitude = sys.argv[3]
total_RSU_longitude = sys.argv[4]

if latitude == []:
    
    set_limit_latitude = 0
    set_limit_longitude = 0
    g = 0
    while g < total_RSU:
        if total_RSU_latitude[g] > set_limit_latitude:
            set_limit_latitude = total_RSU_latitude[g]
        if total_RSU_longitude[g] > set_limit_longitude:
            set_limit_longitude = total_RSU_longitude[g]
    
    i = total_ovu
    while -1 < i:
        if set_limit_longitude < total_RSU:
            longitude.append(0)
        else:
            longitude.append(total_RSU_longitude[0]-(5+total_ovu))
            
        if set_limit_latitude < total_RSU:
            latitude.append(0)
        else:
            latitude.append(total_RSU_latitude[0]-(5+total_ovu))


threading.Thread(target=client.loop_forever).start()

while(True):
    i = 0
    while i < total_ovu:
        generate(i, total_RSU)
        i = i+1
