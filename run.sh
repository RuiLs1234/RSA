if [ "$#" -ne 7 ]; then
    echo "Usage: $0 <number of RSUs> <number of OBUs> <train velocity> <initial first OBU coordinates> <OBU to lose> <OBU lose coordinates>"
    exit 1
fi
if [ $5 >= $2] || [ $5 <= 1 ]; then
    echo "OBU to lose must be between 2 and number of OBUs - 1"
    exit 1
fi
sudo docker network create vanetzalan0 --subnet 192.168.98.0/24
python3 /Downloads/vanetza-master/create_config.py $1 $2
sleep 1
sudo docker-compose up
python3 /Downloads/vanetza-master/central_mqtt_broker.py $1
sleep 2
python3 /Downloads/vanetza-master/generate_RSUI.py 
for i in $(seq 1 $2);
    python3 /Downloads/vanetza-master/generate_OBU{$i}.py
done
