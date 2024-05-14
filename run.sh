docker network create vanetzalan0 --subnet 192.168.98.0/24
docker-compose up
#block other rsus
docker-compose exec rsu1 block 6e:06:e0:03:00:02
docker-compose exec rsu1 block 6e:06:e0:03:00:03
#block obus
docker-compose exec rsu1 block 6e:06:e0:03:00:04
docker-compose exec rsu1 block 6e:06:e0:03:00:05
docker-compose exec rsu1 block 6e:06:e0:03:00:06

#block other rsus
docker-compose exec rsu1 block 6e:06:e0:03:00:01
docker-compose exec rsu1 block 6e:06:e0:03:00:03
#block obus
docker-compose exec rsu1 block 6e:06:e0:03:00:04
docker-compose exec rsu1 block 6e:06:e0:03:00:05
docker-compose exec rsu1 block 6e:06:e0:03:00:06

#block other rsus
docker-compose exec rsu1 block 6e:06:e0:03:00:01
docker-compose exec rsu1 block 6e:06:e0:03:00:02
#block obus
docker-compose exec rsu1 block 6e:06:e0:03:00:04
docker-compose exec rsu1 block 6e:06:e0:03:00:05
docker-compose exec rsu1 block 6e:06:e0:03:00:06

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
