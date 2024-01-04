#!/bin/bash
set -x

version=10.2.3

# install grafana
sudo apt-get install -y adduser libfontconfig1 musl
wget https://dl.grafana.com/oss/release/grafana_${version}_amd64.deb
sudo dpkg -i grafana_10.2.3_amd64.deb

# start grafana service
sudo systemctl start grafana-server
sudo systemctl enable grafana-server

