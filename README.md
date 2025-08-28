# DF-docker
This is a Docker Compose-based project that automates the deployment of a data historian and protocol bridge for transforming OPC UA data to MQTT. It integrates time-series storage, monitoring, and visualization tools to support Industrial IoT (IIoT) applications, enabling real-time data collection, protocol conversion, and system oversight.

> [!NOTE]
> Make sure to set up your environment variables before running the docker compose script

## Gettting started

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
