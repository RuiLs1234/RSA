if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <number of RSUs> <number of carriages>"
    exit 1
fi
docker network create vanetzalan0 --subnet 192.168.98.0/24
python3 /Downloads/vanetza-master/create_config.py $1 $2
sleep 1
docker-compose up
python3 /Downloads/vanetza-master/central_mqtt_broker.py $1
sleep 4
docker-compose exec rsu1 unblock 6e:06:e0:03:00:04
sleep 3
docker-compose exec rsu1 block 6e:06:e0:03:00:04
sleep 1
docker-compose exec rsu2 unblock 6e:06:e0:03:00:04
sleep 3
docker-compose exec rsu2 block 6e:06:e0:03:00:04
sleep 1
docker-compose exec rsu3 unblock 6e:06:e0:03:00:04
sleep 3
