import json
import paho.mqtt.client as mqtt
import threading
from time import sleep
import sys


global_count = []
obj = {}
range_RSU = 0
check = []
done = 0

def on_connect(client, userdata, flags, rc):
    global obj
    print("Connected with result code "+str(rc))
    obj = client.subscribe("vanetza/out/cam")
    print(obj)


def on_message(client, userdata, msg):
    global obj
    
    #print('Topic: ' + msg.topic)
    #print('Message: ' + msg.payload.decode('utf-8'))

    obj = json.loads(msg.payload.decode('utf-8'))


def generate(ovus, size, i):
    global global_count
    global range_RSU
    global obj
    global check
    global done
    print("HERE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(obj)
    if str(obj) != "(<MQTTErrorCode.MQTT_ERR_SUCCESS: 0>, 1)" and obj != {}:
                        if obj["heading"] not in global_count[i]:
                            global_count[i].append(obj["heading"])
                        else:
                            if ovus != len(global_count[i]) and global_count[i] != 0:  
                                if check[i] > 10000 and done == 0: 
                                    done = 1  
                                    with open('examples/in_denm.json') as f:
                                            m = json.load(f)
                                            m["situation"]["eventType"]["causeCode"] = 94
                                            m = json.dumps(m)
                                            client.publish("vanetza/in/denm",m)
                                    sleep(1)
                                    f.close()
                                else:
                                    check[i] = check[i]+1
    if ovus == len(global_count[i]):
                            check[i] = 0 
    if done == 1:
        print("Error detected!!!!!")



client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

total_RSU = 2
total_ovu = 3

total_RSU_latitude = [2, 4]
total_RSU_longitude = [2, 4]
range_RSU = 2
for gh in range(total_RSU):
    check.append(0)

client.connect("192.168.98.20", 1883, 60) # Criar um client para cada RSU

sleep(10)
if not global_count:
    global_count = [[] for _ in range(total_RSU)]
  

threading.Thread(target=client.loop_forever).start()

while True:
    for i in range(total_RSU):
        generate(total_ovu, total_RSU, i)
