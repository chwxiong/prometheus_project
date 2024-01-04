该目录为prometheus开源项目，用于机器资源性能监控、服务监测等
项目监控地址：http://10.10.12.214:3000/dashboards机器上部署监控服务步骤：
1、执行install_prometheus_server.sh、install_node_exporter.sh
2、prometheus-*/prometheus.yml中ip、端口及监控项等配置
3、执行start_node_exporter_service.sh、start_prometheus_service.sh启动监控服务
4、转至项目监控地址进行监控可视化设置
