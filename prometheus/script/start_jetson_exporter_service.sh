#!/bin/bash
set -x

filepath=$(readlink -f "$0")
dirpath=$(dirname "$filepath")

sudo cp ${dirpath}/../python_files/nvidia_jetson_exporter.py /usr/local/bin/

sudo cp ${dirpath}/jetson_gpu_exporter.service /etc/systemd/system/

# Default localhost and 9102 port
host_param=$1
port_param=$2
if [ -n "$host_param" ];
then
  if [ -n "$port_param" ];
  then
    sudo sed -i "s|ExecStart=python3 /usr/local/bin/nvidia_jetson_exporter.py|ExecStart=python3 /usr/local/bin/nvidia_jetson_exporter.py $host_param $port_param|" /etc/systemd/system/jetson_gpu_exporter.service
  else
    sudo sed -i "s|ExecStart=python3 /usr/local/bin/nvidia_jetson_exporter.py|ExecStart=python3 /usr/local/bin/nvidia_jetson_exporter.py $host_param|" /etc/systemd/system/jetson_gpu_exporter.service
  fi
fi


sudo systemctl daemon-reload
sudo systemctl start jetson_gpu_exporter
sudo systemctl enable jetson_gpu_exporter