#!/bin/bash
set -x

# https://prometheus.io/download/
node_exporter_version=1.7.0

filepath=$(readlink -f "$0")
dirpath=$(dirname "$filepath")

arch=$(arch)
deb_arch=""
if [[ $arch =~ "aarch64" ]];then
    deb_arch=arm64
elif [[ $arch =~ "x86_64" ]];then
    deb_arch=amd64
else
    echo "wrong arch!"
    exit 1
fi

#wget https://github.com/prometheus/node_exporter/releases/download/v${node_exporter_version}/node_exporter-${node_exporter_version}.linux-${deb_arch}.tar.gz

tar -xvzf ../pkg/node_exporter-${node_exporter_version}.linux-${deb_arch}.tar.gz
sudo chown -R autowise:autowise node_exporter-${node_exporter_version}.linux-${deb_arch}
cd node_exporter-${node_exporter_version}.linux-${deb_arch}
sudo cp node_exporter /usr/local/bin/
