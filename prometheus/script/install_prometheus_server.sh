#!/bin/bash
set -x

# https://prometheus.io/download/
prometheus_version=2.45.2

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

# wget https://github.com/prometheus/prometheus/releases/download/v${prometheus_version}/prometheus-${prometheus_version}.linux-${deb_arch}.tar.gz
tar -xvzf ../pkg/prometheus-${prometheus_version}.linux-${deb_arch}.tar.gz
# Modify the permission group of the folder to autowise:autowise
sudo chown -R autowise:autowise prometheus-${prometheus_version}.linux-${deb_arch}
cd prometheus-${prometheus_version}.linux-${deb_arch}

sudo mkdir /etc/prometheus
sudo mkdir /var/lib/prometheus
mkdir -p /home/autowise/prometheus_logs
chown -R autowise:autowise /home/autowise/prometheus_logs

sudo cp prometheus /usr/local/bin/
sudo cp promtool /usr/local/bin/
sudo cp prometheus.yml /etc/prometheus/
sudo cp -r consoles /etc/prometheus
sudo cp -r console_libraries /etc/prometheus