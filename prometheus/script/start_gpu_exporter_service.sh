#!/bin/bash

filepath=$(readlink -f "$0")
dirpath=$(dirname "$filepath")

sudo cp ${dirpath}/nvidia_gpu_exporter.service /etc/systemd/system/nvidia_gpu_exporter.service

sudo systemctl daemon-reload
sudo systemctl start nvidia_gpu_exporter
sudo systemctl enable nvidia_gpu_exporter