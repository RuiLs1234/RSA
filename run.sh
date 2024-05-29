#when running the script the RSUs coordinates argument should be used like this '[[40.0000,-8.0000],[41.0000,-8.0000],[42.0000,-8.0000]]'
if [ "$#" -ne 7 ]; then
    echo "Usage: $0 <number of RSUs> <number of OBUs> <RSUs coordinates> <RSUs range in meters> <train velocity> <initial OBU coordinates> <OBU to lose> <OBU lose coordinates>"
    exit 1
fi
if [ $5 >= $2] || [ $5 <= 1 ]; then
    echo "OBU to lose must be between 2 and number of OBUs - 1"
    exit 1
fi
sudo docker network create vanetzalan0 --subnet 192.168.98.0/24
python3 /Downloads/vanetza-master/create_config.py $1 $2 $3
sleep 3
python3 /Downloads/vanetza-master/central_mqtt_broker.py $1
sleep 2
python3 /Downloads/vanetza-master/init_simulation.py $1 $2 $3 $4
python3 /Downloads/vanetza-master/generate_RSUI.py
python3 /Downloads/vanetza-master/generate_OBU.py
