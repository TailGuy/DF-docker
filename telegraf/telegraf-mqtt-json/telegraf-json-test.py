import paho.mqtt.client as mqtt
import json
import random
import time

# Connect to local MQTT broker
client = mqtt.Client()
client.connect("127.0.0.1", 1883, 60)

# Publish loop
while True:
    # Generate data for plant1
    data1 = {
        "cooler": {
            "temperature": random.uniform(10, 15),
            "value2": random.uniform(0, 10)
        },
        "heater": {
            "temperature": random.uniform(20, 25),
            "value2": random.uniform(0, 10)
        }
    }
    client.publish("PythonTestInputTemperatureControl", json.dumps(data1))

    # Generate data for plant2
    data2 = {
        "Volume": random.uniform(50, 100),
    }
    client.publish("PythonTestInputWaterTank", json.dumps(data2))

    time.sleep(5)