# -*- coding: utf-8 -*-
import atexit
import logging
import random
import subprocess
import sys
import nvitop
import psutil
import pynvml
from nvitop import Device, GpuProcess
import prometheus_client
from prometheus_client import Info, Gauge, Counter
from prometheus_client.core import CollectorRegistry, InfoMetricFamily, GaugeMetricFamily, CounterMetricFamily
from flask import Response, Flask
from psutil import *
from jtop import jtop
import platform

app = Flask(__name__)

REGISTRY = CollectorRegistry(auto_describe=False)
_info_data = None
update_count = 0
def _update_info_data(_jetson):
    global _info_data
    if _info_data is None:
        _info_data = {
            "board_machine": _jetson.board["platform"]["Machine"],
            "board_system": _jetson.board["platform"]["System"],
            "board_distribution": _jetson.board["platform"]["Distribution"],
            "board_release": _jetson.board["platform"]["Release"],
            "board_python": _jetson.board["platform"]["Python"],
            "hardware_model": _jetson.board["hardware"]["Model"],
            "hardware_module": _jetson.board["hardware"]["Module"],
            "hardware_jetpack": _jetson.board["hardware"]["Jetpack"],
            "hardware_l4t": _jetson.board["hardware"]["L4T"],
            "hardware_soc": _jetson.board["hardware"]["SoC"],
            "hardware_cuda_arch_bin": _jetson.board["hardware"]["CUDA Arch BIN"],
            "hardware_serial_number": _jetson.board["hardware"]["Serial Number"],
            "hardware_cuda": _jetson.board["libraries"]["CUDA"],
            "hardware_opencv": _jetson.board["libraries"]["OpenCV"]
        }
        global update_count
        update_count += 1
        logging.info(f"Update info data {update_count} times")


class CustomCollector(object):
    def __init__(self):
        atexit.register(self.cleanup)
        self._jetson = jtop()
        self._jetson.start()      

    def cleanup(self):
        logging.info("Closing jetson-stats connection...")
        self._jetson.close()     

    def update_info_data(self):
        _update_info_data(self._jetson)  # 调用全局的更新函数

    def collect(self):
        if self._jetson.ok():
            self._jetson.set_scaling_3D = True
            global _info_data
            if _info_data is None:
                self.update_info_data()
                ## board info
                i_board = InfoMetricFamily('jetson_info_board', 'Board sys info', labels=['board_info'])
                i_board.add_metric(['info'], {
                    'machine': _info_data["board_machine"],
                    'system': _info_data["board_system"],
                    'distribution': _info_data["board_distribution"],
                    'release': _info_data["board_release"],
                    'python': _info_data["board_python"]
                })
                yield i_board
                ## hardware info
                i_hardware = InfoMetricFamily('jetson_info_hardware', 'Board hardware info', labels=['board_hw'])
                i_hardware.add_metric(['hardware'], {
                    'model': _info_data["hardware_model"],
                    'module': _info_data["hardware_module"],
                    'jetpack': _info_data["hardware_jetpack"],
                    'l4t': _info_data["hardware_l4t"],
                    'soc': _info_data["hardware_soc"],
                    'cuda_arch_bin': _info_data["hardware_cuda_arch_bin"],
                    'serial_number': _info_data["hardware_serial_number"],
                    'cuda': _info_data["hardware_cuda"],
                    'opencv': _info_data["hardware_opencv"]
                })
                yield i_hardware
            ## cpu usage info
            g_cpu = GaugeMetricFamily('jetson_usage_cpu', 'CPU % schedutil', labels=['cpu'])
            for idx, cpu in enumerate(self._jetson.cpu['cpu']):
                g_cpu.add_metric([f'cpu_{idx}'], self._jetson.cpu['cpu'][idx]['user'] + self._jetson.cpu['cpu'][idx]['system']) # user + system
            yield g_cpu
            ## gpu usage info
            g_gpu = GaugeMetricFamily('jetson_usage_gpu', 'GPU % schedutil', labels=['gpu'])
            g_gpu.add_metric(['gpu_utilization'], self._jetson.stats["GPU"])
            yield g_gpu
            ## RAM usage info
            g_ram = GaugeMetricFamily('jetson_usage_ram', 'Memory usage', labels=['ram'])
            # g_ram.add_metric(['used_ram_percentage'], self._jetson.stats['RAM']) # RAM used / total
            # g_ram.add_metric(['swap_ram_percentage'], self._jetson.stats['SWAP'])
            g_ram.add_metric(['total_ram'], self._jetson.memory['RAM']['tot'])
            g_ram.add_metric(['used_ram'], self._jetson.memory['RAM']['used'])
            g_ram.add_metric(['total_swap'], self._jetson.memory['SWAP']['tot'])
            g_ram.add_metric(['used_swap'], self._jetson.memory['SWAP']['used'])
            yield g_ram
            ## Disk usage info
            g_disk = GaugeMetricFamily('jetson_usage_disk', 'Disk usage', labels=['disk'])
            g_disk.add_metric(['used'], self._jetson.disk['used'])
            g_disk.add_metric(['total'], self._jetson.disk['total'])
            g_disk.add_metric(['available'], self._jetson.disk['available'])
            g_disk.add_metric(['available_no_root'], self._jetson.disk['available_no_root'])
            yield g_disk
            ## Fan usage info
            g_fan = GaugeMetricFamily('jetson_usage_fan', 'Fan speed', labels=['fan'])
            g_fan.add_metric(['speed'], self._jetson.fan['speed'] if "speed" in self._jetson.fan else 0)
            yield g_fan
            ## Sensor temperature info
            g_temp = GaugeMetricFamily('jetson_usage_temp', 'Temperature', labels=['temperature'])
            g_temp.add_metric(['cpu'], self._jetson.temperature['CPU']["temp"])
            g_temp.add_metric(['gpu'], self._jetson.temperature['GPU']["temp"])
            g_temp.add_metric(['Tboard'], self._jetson.temperature['Tboard']["temp"])
            yield g_temp
            ## Power usage info
            g_power = GaugeMetricFamily('jetson_usage_power', 'Power usage', labels=['power'])
            g_power.add_metric(['total_power'], self._jetson.power['tot']["power"])
            yield g_power

@app.route("/metrics")
def metrics():
    return Response(prometheus_client.generate_latest(REGISTRY), mimetype="text/plain")

@app.route("/")
def index():
    return "<h1>Customized Exporter</h1><br> <a href='/metrics'>Metrics</a>"

def get_free_port(port=None):
    if port is None:
        port = random.randint(9000, 9200)
    bussy_ports = subprocess.Popen("netstat -ntl |grep -v Active| grep -v Proto|awk '{print $4}'|awk -F: '{print $NF}'", stdout=subprocess.PIPE, shell=True)
    busy_port_list = bussy_ports.stdout.read().decode().split("\n")
    if port not in busy_port_list:
        return port
    else:
        port = random.randint(9000, 9200)
        get_free_port(port)


if __name__ == "__main__":
    args = sys.argv
    if len(args) > 1:
        host = args[1]
    else:
        host = 'localhost'
    if len(args) > 2:
        port = get_free_port(args[2])
    else:
        port = get_free_port(9101)
    REGISTRY.register(CustomCollector())
    app.run(host=host, port=port, debug=True)