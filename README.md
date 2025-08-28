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
> Make sure to set up your environment variables before running the docker compose script.

## Prerequisites
- Docker (version 20.10+ recommended)
- Docker Compose (version 2.0+ recommended)
- Git (for cloning the repository)

## Getting started

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
Create `.env` file from the template file `.envtemplate` and change all of the `changme`  parts, such as InfluxDB credentials and tokens.
```
cp ./.envtemplate ./.env
sudo nano .env
```

### Running the docker compose script
run the project
```
docker compose up --build -d
```

to stop the project run
```
docker compose down
```

### Usage
Access key interfaces:
- Grafana: http://localhost:3000
- Portainer: http://localhost:9000
- FastAPI Telegraf Manager: http://localhost:7090
- FastAPI Legacy App: http://localhost:7080


## Services
The `docker-compose.yml` defines the following services, each configured for monitoring, data handling, and IIoT integration:
- **influxdb**: Time-series database for persisting metrics and data from Telegraf and other sources.
- **telegraf**: Metrics collection agent that reads from OPC UA servers, processes data, and forwards to InfluxDB and MQTT.
- **grafana**: Visualization platform for dashboards and alerts, connected to InfluxDB, Prometheus, and Loki.
- **mosquitto**: Eclipse Mosquitto MQTT broker for lightweight messaging between services and external IIoT devices.
- **portainer-ce**: Web-based UI for managing Docker containers, images, and volumes.
- **cadvisor**: Container Advisor for analyzing and exposing resource usage and performance metrics from running containers.
- **prometheus**: Metrics storage and querying system that collects data from cAdvisor and other endpoints.
- **loki**: Grafana Loki for aggregating and querying logs from services like Alloy.
- **alloy**: Grafana Alloy agent for collecting logs from Docker and the FastAPI app, forwarding them to Loki.
- **app**: Legacy FastAPI application for data processing (e.g., MQTT to InfluxDB conversion). https://github.com/TailGuy/fastapi-app
- **app-telegraf**: FastAPI application for managing the Telegraf container, including config uploads, interval changes, and status monitoring.  https://github.com/TailGuy/telegraf-app
