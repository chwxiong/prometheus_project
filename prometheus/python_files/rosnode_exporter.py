# -*- coding: utf-8 -*-
import atexit
import os
import platform
import random
import re
import subprocess
import sys
import time
import rosnode
import logging
import prometheus_client
import nvitop
import psutil
import pynvml
from nvitop import Device, GpuProcess
from prometheus_client import Info, Gauge, Counter
from prometheus_client.core import CollectorRegistry, InfoMetricFamily, GaugeMetricFamily, CounterMetricFamily
from flask import Response, Flask
from psutil import *
import rospy
from jtop import jtop
try:
    from xmlrpc.client import ServerProxy
except ImportError:
    from xmlrpclib import ServerProxy


if platform.machine().startswith("aarch"):
    with jtop() as jetson:
        if jetson.ok():
            jetson.gpu.set_scaling_3D = True


app = Flask(__name__)

REGISTRY = CollectorRegistry(auto_describe=False)


ignore_node = ("/rosout", "/planning_vis_node", "/snapshot_encoder_node", "/runtimectrl", "/aw_simulation_vehicle", "/fake_hdmap"
               "/traffic_light_restorer", "/obstacle_restorer_node", "/evaluation_node", "/offline_eva_node", "/resource_monitor_node")

class RosNodeCollector(object):
    def __init__(self):
        # init gpu
        if platform.machine().startswith("aarch"):
            rospy.logwarn("This is arm platform, default monitor Integrate GPU")
            self.arch = "aarch"
        elif platform.machine().startswith("x86"):
            rospy.logwarn("This is X86 platform, default monitor GPU INDEX 0")
            self.arch = "x86"        

    def collect(self):
        node_list = []
        try:
            node_list = rosnode.get_node_names()
            node_list = [node for node in node_list if node not in ignore_node]
            logging.info(f"[rosnode monitor] node list: {node_list}")
        except Exception as e:
            timens = time.time()
            logging.error(f"[rosnode monitor][{timens}] failed to get node list! Error: {e}")
            node_list = []
        master = rospy.get_master()
        for node in node_list:
            if node.startswith("/play") or node.startswith("/rosout") or node.startswith("/rviz") or node.startswith("rostopic") or node.startswith("/record"):
                continue
            node_api = rosnode.get_api_uri(master, node)[2]
            try:
                resp = ServerProxy(node_api).getPid('/NODEINFO')
                pid = resp[2]
                for metric in self.collect_metrics_for_node(node, pid):
                    yield metric
            except Exception as e:
                logging.error(f"[cpu monitor] failed to node {node} monitor info ! {e}")
    
    def collect_metrics_for_node(self, name, pid):
        self.name = name
        self.pid = pid
        try:
            self.proc = psutil.Process(self.pid)
        except Exception as e:
            timens = time.time()
            logging.error(f"[rosnode monitor][{timens}] failed to get info of node {self.name} {self.pid}! Error: {e}")
            return
        if self.proc.is_running():
            #proc info
            ## cpu percent
            cpu_gauge = GaugeMetricFamily(f"rosnode_cpu", f"cpu percent of rosnode {self.name}", labels=['cpu'])
            try:
                cpu_percent = self.proc.cpu_percent()
            except Exception as e:
                timens = time.time()
                logging.error(f"[rosnode monitor][{timens}] failed to get cpu_percent of node {self.name} {self.pid}! Error: {e}")
                cpu_percent = 0
            cpu_gauge.add_metric([f"{self.name}_cpu_percent"], cpu_percent)
            ## cpu times
            try:
                cpu_times = self.proc.cpu_times()
                cpu_time = cpu_times.user + cpu_times.system + cpu_times.children_user + cpu_times.children_system
            except Exception as e:
                timens = time.time()
                logging.error(f"[rosnode monitor][{timens}] failed to get cpu_times of node {self.name} {self.pid}! Error: {e}")
                cpu_time = 0
            cpu_gauge.add_metric([f"{self.name}_cpu_time"], cpu_time)
            yield cpu_gauge
            ## IO
            io_gauge = GaugeMetricFamily(f"rosnode_io", f"io of rosnode {self.name}", labels=['io'])
            try:
                io_read_counter = self.proc.io_counters[0]
            except Exception as e:
                timens = time.time()
                logging.error(f"[rosnode monitor][{timens}] failed to get io_read_counter of node {self.name} {self.pid}! Error: {e}")
                io_read_counter = 0 
            io_gauge.add_metric([f"{self.name}_io_read_counter"], io_read_counter)
            try:
                io_write_counter = self.proc.io_counters[1]
            except Exception as e:
                timens = time.time()
                logging.error(f"[rosnode monitor][{timens}] failed to get io_write_counter of node {self.name} {self.pid}! Error: {e}")
                io_write_counter = 0
            io_gauge.add_metric([f"{self.name}_io_write_counter"], io_write_counter)
            yield io_gauge
            ## memory
            mem_gauge = GaugeMetricFamily(f"rosnode_memory", f"memory of rosnode {self.name}", labels=['memory'])
            try:  
                mem_cmd = os.popen("sudo grep VmRSS /proc/%d/status" % self.pid).readline()
                VmRSS = re.findall(r"\d+", mem_cmd)[0]
            except Exception as e:
                timens = time.time()
                logging.error(f"[rosnode monitor][{timens}] failed to get VmRSS of node {self.name} {self.pid}! Error: {e}")
                VmRSS = 0
            mem_gauge.add_metric([f"{self.name}_VmRSS"], VmRSS)
            try:
                mem_cmd = os.popen("sudo grep VmSize /proc/%d/status" % self.pid).readline()
                peak_mem = re.findall(r"\d+", mem_cmd)[0]
            except Exception as e:
                timens = time.time()
                logging.error(f"[rosnode monitor][{timens}] failed to get VmSize of node {self.name} {self.pid}! Error: {e}")
                peak_mem = 0
            mem_gauge.add_metric([f"{self.name}_VmSize"], peak_mem)
            yield mem_gauge
            ## gpu
            gpu_gauge = GaugeMetricFamily(f"rosnode_gpu", f"gpu of rosnode {self.name}", labels=['gpu'])
            try:
                if self.arch == "x86":
                    for device in self.GPU_device:
                        processes = device.processes()  # type: Dict[int, GpuProcess]
                        processes = nvitop.GpuProcess.take_snapshots(processes.values(), failsafe=True)
                        # sorted_pids = sorted(processes)
                        for snapshot in processes:
                            if self.pid == snapshot.pid:
                                gpu_memory_used = snapshot.gpu_memory_human[:-3]
                elif self.arch == "aarch":
                    for procs in jetson.processes:
                        if self.pid == procs[0]:
                            snapshot.gpu_memory_human[:-3] = procs[8] / 1024
            except Exception as e:
                timens = time.time()
                logging.error(f"[rosnode monitor][{timens}] failed to get gpu_memory_used of node {self.name} {self.pid}! Error: {e}")
                gpu_memory_used = 0
            gpu_gauge.add_metric([f"{self.name}_gpu_memory_used"], gpu_memory_used)
            yield gpu_gauge

            
@app.route("/metrics")
def metrics():
    REGISTRY.register(RosNodeCollector())
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
        port = get_free_port(9102)
    app.run(host=host, port=port, debug=True)