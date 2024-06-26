#!/bin/bash
if [ "$#" -ne 8 ]; then
    echo "Usage: $0 <number of RSUs> <number of OBUs> <RSUs coordinates> <RSUs range in meters> \
<train velocity> <initial OBU coordinates> <end OBU coordinates> <OBU to lose>"
    exit 1
fi

num_rsus=$1
num_obus=$2
rsu_coordinates=$3
rsu_range=$4
train_velocity=$5
initial_obu_coordinates=$6
end_obu_coordinates=$7
obu_to_lose=$8

if [ "$obu_to_lose" -gt "$num_obus" ] || [ "$obu_to_lose" -le 1 ]; then
    echo "OBU to lose must be between 2 and number of OBUs"
    exit 1
fi

if ! sudo docker network ls | grep -q vanetzalan0; then
    sudo docker network create vanetzalan0 --subnet 192.168.98.0/24
fi

create_config_script="create_config.py"
central_mqtt_broker_script="central_mqtt_broker.py"
init_simulation_script="init_simulation.py"
rsu_script="RSU.py"
obu_script="OBU.py"

if [ ! -f "$create_config_script" ] || [ ! -f "$central_mqtt_broker_script" ] || [ ! -f "$init_simulation_script" ] || [ ! -f "$rsu_script" ] || [ ! -f "$obu_script" ]; then
    echo "One or more Python scripts are missing"
    exit 1
fi

python3 "$create_config_script" "$num_rsus" "$num_obus" "$rsu_coordinates"

gnome-terminal -- bash -c "python3 $central_mqtt_broker_script; exec bash"
gnome-terminal -- bash -c "python3 $rsu_script $num_rsus $num_obus ; exec bash"
gnome-terminal -- bash -c "python3 $obu_script $num_rsus $num_obus $initial_obu_coordinates $end_obu_coordinates; exec bash"
sleep 2
gnome-terminal -- bash -c "python3 $init_simulation_script $num_rsus $num_obus $rsu_range $train_velocity $initial_obu_coordinates $end_obu_coordinates $obu_to_lose; exec bash"

# Example command to run this script
# sudo ./run.sh 3 3 [[39.982034,-8.0000],[39.991017,-8.0000],[40.0000,-8.0000]] 450 70 [39.978,-8] [40.005,-8] 3