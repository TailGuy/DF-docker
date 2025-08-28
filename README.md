# DF-docker
This is a Docker Compose-based project that automates the deployment of a data historian and protocol bridge for transforming OPC UA data to MQTT. It integrates time-series storage, monitoring, and visualization tools to support Industrial IoT (IIoT) applications, enabling real-time data collection, protocol conversion, and system oversight.

- [Prerequisites](#Prerequisites)
- [Getting Started](#getting-started)
  - [Installation](#installation)
  - [Setting up your environment variables](#setting-up-your-environment-variables)
  - [Running the docker compose script](#running-the-docker-compose-script)
  - [Usage](#usage)
- [Services](#services)

> [!NOTE]
> Make sure to set up your environment variables before running the docker compose script. [Setting up your environment variables](#setting-up-your-environment-variables)  
> Remember to set up the admin account for portainer after running the docker compose script: http://localhost:9000  
> You can check logs for applications through Grafana: http://localhost:3000/a/grafana-lokiexplore-app/

## Prerequisites
- Docker (version 20.10+ recommended)
- Docker Compose (version 2.0+ recommended)
- Git (for cloning the repository)

## Getting Started

### Installation
Clone the repository:
```
git clone --recursive https://github.com/TailGuy/DF-docker.git
```

Navigate to the directory:
```
cd DF-docker
```

### Setting up your environment variables
Create `.env` file from the template file `.envtemplate` and change all of the `changeme`  parts, such as InfluxDB credentials and tokens.
```
cp ./.envtemplate ./.env
sudo nano .env
```

### Running the docker compose script
Build and run the project in detached mode:
```
docker compose up --build -d
```

**Access portainer to set up the admin account:**
http://localhost:9000

To stop the project:
```
docker compose down
```

### Usage
Access key interfaces:
- Grafana: http://localhost:3000 (logs, dashboards and visualizations)
- Portainer: http://localhost:9000 (container management)
- FastAPI Telegraf Manager: http://localhost:7090 (Telegraf config and status)
- FastAPI Legacy App: http://localhost:7080 (Legacy app)


## Services
The `docker-compose.yml` defines the following services, each configured for monitoring, data handling, and IIoT integration:

| Service       | Description                                                                 | Ports       | Dependencies          | Volumes/Persistence          |
|---------------|-----------------------------------------------------------------------------|-------------|-----------------------|------------------------------|
| **influxdb** | Time-series database for metrics from Telegraf.                             | 8086       | None                  | influxdb-storage            |
| **telegraf** | Collects OPC UA data, forwards to InfluxDB/MQTT.                            | None       | influxdb, mosquitto   | telegraf-configs            |
| **grafana**  | Dashboards and alerts from InfluxDB/Prometheus/Loki.                        | 3000       | None                  | grafana-data, grafana-log   |
| **mosquitto**| MQTT broker for IIoT messaging.                                             | 1883       | None                  | mosquitto-data, mosquitto-log |
| **portainer-ce** | UI for Docker management.                                               | 8000, 9000, 9443 | None              | portainer-ce/data           |
| **cadvisor** | Container resource monitoring.                                              | 8080       | None                  | Host mounts (/sys, etc.)    |
| **prometheus**| Metrics querying from cAdvisor.                                           | 9090       | cadvisor              | prom-data                   |
| **loki**     | Log aggregation for Alloy.                                                  | 3100       | None                  | loki_data                   |
| **alloy**    | Log collection to Loki.                                                     | 12345      | None                  | fastapi-logs                |
| **app**      | Legacy FastAPI for MQTT to InfluxDB. [Repo](https://github.com/TailGuy/fastapi-app) | 7080 | None                  | fastapi-logs                |
| **app-telegraf** | FastAPI for Telegraf management. [Repo](https://github.com/TailGuy/telegraf-app) | 7090 | None                  | telegraf-configs            |
