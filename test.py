# type: ignore
import csv
import random
import time
import paho.mqtt.client as mqtt

# MQTT broker details
broker = "localhost"  # or "localhost" if running locally
port = 1883

# Path to nodes-test.csv
csv_file = "nodes-test.csv"

# Read MQTT input names from CSV
topics = []
with open(csv_file, newline='') as f:
    reader = csv.reader(f)
    next(reader)  # Skip header "MQTTInputName"
    for row in reader:
        if row:
            input_name = row[0]
            topic = f"telegraf/opcua/{input_name}"
            topics.append(topic)

# Connect to MQTT broker
client = mqtt.Client()
client.connect(broker, port, 60)
client.loop_start()

print(f"Publishing to topics: {topics}")

try:
    while True:
        for topic in topics:
            value = random.uniform(0, 100)  # Random float between 0 and 100
            client.publish(topic, value)
            print(f"Published {value} to {topic}")
        time.sleep(5)  # Publish every 5 seconds
except KeyboardInterrupt:
    print("Stopping publisher")
finally:
    client.loop_stop()
    client.disconnect()