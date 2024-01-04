#!/bin/bash

prometheus_version=2.45.2
node_exporter_version=1.7.0

filepath=$(readlink -f "$0")
dirpath=$(dirname "$filepath")

sudo cp ${dirpath}/prometheus-*/prometheus.yml /etc/prometheus/prometheus.yml

sudo cp ${dirpath}/prometheus.service /etc/systemd/system/prometheus.service

sudo systemctl daemon-reload

sudo systemctl start prometheus
sudo systemctl enable prometheus
