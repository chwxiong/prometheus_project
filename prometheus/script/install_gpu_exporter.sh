#!/bin/bash
set -x

# https://github.com/utkuozdemir/nvidia_gpu_exporter
gpu_exporter_version=1.2.0

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

# wget https://github.com/utkuozdemir/nvidia_gpu_exporter/releases/download/v${VERSION}/nvidia_gpu_exporter_${VERSION}_linux_x86_64.tar.gz
tar -xvzf ../pkg/nvidia_gpu_exporter_${gpu_exporter_version}_linux_${deb_arch}.tar.gz
sudo chown autowise:autowise nvidia_gpu_exporter
sudo cp nvidia_gpu_exporter /usr/local/bin/
sudo cp LICENSE /usr/local/bin/