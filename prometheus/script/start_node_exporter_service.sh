#!/bin/bash

filepath=$(readlink -f "$0")
dirpath=$(dirname "$filepath")

sudo cp ${dirpath}/node_exporter.service /etc/systemd/system/node_exporter.service

sudo systemctl daemon-reload
sudo systemctl start node_exporter
sudo systemctl enable node_exporter