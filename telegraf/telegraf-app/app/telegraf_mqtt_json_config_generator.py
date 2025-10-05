import os
import time
import datetime
import logging
import csv
from typing import List, Dict, Any, cast, DefaultDict
from collections import defaultdict
from tomlkit import document, table, aot, comment, nl, integer, boolean, string

logger: logging.Logger = logging.getLogger("telegraf_manager.telegraf_mqtt_json_config_generator")

class TelegrafMqttJsonConfigGenerator:
    """
    Generates Telegraf configuration for MQTT topics with JSON payloads from a CSV file.
    The CSV specifies how to map JSON paths to InfluxDB field names.
    """
    def __init__(self,
                 csv_file_path: str,
                 output_file_path: str,
                 mqtt_broker: str = "tcp://mosquitto:1883",
                 influxdb_url: str = "http://influxdb:8086") -> None:

        if not csv_file_path:
            raise ValueError("CSV file path cannot be empty.")
        if not output_file_path:
            raise ValueError("Output file path cannot be empty.")

        self.csv_file_path: str = csv_file_path
        self.output_file_path: str = output_file_path
        self.mqtt_broker: str = mqtt_broker
        self.influxdb_url: str = influxdb_url
        self._start_time: float = 0.0
        self._total_rows_processed: int = 0
        self._total_topics_configured: int = 0

    def generate_telegraf_config(self) -> None:
        """
        Process the CSV file of MQTT JSON inputs and generate a Telegraf configuration.
        """
        if not os.path.exists(self.csv_file_path):
            logger.error(f"Error: CSV file '{self.csv_file_path}' not found.")
            return

        # Group rows by MQTTInputName
        topics_data: DefaultDict[str, List[Dict[str, str]]] = defaultdict(list)
        try:
            logger.info(f"Reading MQTT JSON mappings from CSV file: {self.csv_file_path}")
            with open(self.csv_file_path, 'r', encoding='utf-8') as csvfile:
                reader: csv.DictReader[str] = csv.DictReader(csvfile)
                for row in reader:
                    if all(key in row and row[key] for key in ['MQTTInputName', 'JsonPath', 'FieldName']):
                        topics_data[row['MQTTInputName']].append({
                            'path': row['JsonPath'],
                            'rename': row['FieldName']
                        })
                        self._total_rows_processed += 1
                    else:
                        missing_keys = [key for key in ['MQTTInputName', 'JsonPath', 'FieldName'] if key not in row or not row[key]]
                        logger.warning(f"Row missing or has empty required columns {missing_keys}: {row}")
            
            self._total_topics_configured = len(topics_data)
            logger.info(f"Successfully processed {self._total_rows_processed} field mappings for {self._total_topics_configured} topics from CSV.")

        except Exception as e:
            logger.error(f"Error reading or processing CSV file: {e}", exc_info=True)
            return

        # Generate Telegraf configuration using tomlkit
        doc = document()

        timestamp: str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Add header comments
        doc.add(comment(f"Generated at {timestamp}"))
        doc.add(comment("Telegraf Configuration for MQTT to InfluxDB with JSON Parsing"))
        doc.add(comment("Generated from CSV file"))
        doc.add(nl())

        # Add agent section
        doc.add(comment("###############################################################################"))
        doc.add(comment("#                            AGENT SETTINGS                                   #"))
        doc.add(comment("###############################################################################"))

        agent = table()
        agent.add("interval", "10s")
        agent.add("round_interval", boolean("true"))
        agent.add("metric_batch_size", integer(1000))
        agent.add("metric_buffer_limit", integer(10000))
        agent.add("collection_jitter", "0s")
        agent.add("flush_interval", "10s")
        agent.add("flush_jitter", "0s")
        agent.add("precision", "")
        agent.add("hostname", "")
        agent.add("omit_hostname", boolean("false"))
        doc.add("agent", agent)
        doc.add(nl())

        # Add inputs section
        doc.add(comment("###############################################################################"))
        doc.add(comment("#                            INPUT PLUGINS                                    #"))
        doc.add(comment("###############################################################################"))
        doc.add(nl())
        doc.add(comment("# Read and parse JSON data from MQTT topics"))
        
        inputs = table()
        mqtt_consumer_aot: List[Any] = cast(List[Any], aot())

        for topic_name, fields in topics_data.items():
            doc.add(nl())
            doc.add(comment(f"# Configuration for {topic_name} topic"))
            
            mqtt_consumer = table()
            mqtt_consumer.add("servers", [self.mqtt_broker])
            mqtt_consumer.add("topics", [topic_name])
            mqtt_consumer.add("data_format", "json_v2")

            json_v2_config = table()
            json_v2_config.add("measurement_name", "mqtt")

            json_fields_aot: List[Any] = cast(List[Any], aot())
            for field_map in fields:
                field_table = table()
                field_table.add("path", field_map['path'])
                field_table.add("rename", field_map['rename'])
                field_table.add("type", "float") # Assuming float type
                json_fields_aot.append(field_table)
            
            json_v2_config.add("field", json_fields_aot)
            mqtt_consumer.add("json_v2", [json_v2_config])

            tags = table()
            tags.add("MQTTInputName", topic_name)
            mqtt_consumer.add("tags", tags)
            
            mqtt_consumer_aot.append(mqtt_consumer)

        inputs.add("mqtt_consumer", mqtt_consumer_aot)
        doc.add("inputs", inputs)
        doc.add(nl())
        
        # Add outputs section
        doc.add(comment("###############################################################################"))
        doc.add(comment("#                            OUTPUT PLUGINS                                   #"))
        doc.add(comment("###############################################################################"))
        doc.add(nl())

        outputs = table()

        # InfluxDB output
        doc.add(comment("# --- InfluxDB v2 Output ---"))
        influxdb_v2_aot: List[Any] = cast(List[Any], aot())
        influxdb_v2 = table()
        influxdb_v2.add("urls", [self.influxdb_url]).comment("Replace with your InfluxDB URL")
        influxdb_v2.add("token", "$DOCKER_INFLUXDB_INIT_ADMIN_TOKEN").comment("Replace with your InfluxDB Token or env var")
        influxdb_v2.add("organization", "$DOCKER_INFLUXDB_INIT_ORG").comment("Replace with your InfluxDB Org or env var")
        influxdb_v2.add("bucket", "jsontest") # As per example
        influxdb_v2_aot.append(influxdb_v2)
        outputs.add("influxdb_v2", influxdb_v2_aot)
        doc.add("outputs", outputs)

        # Write configuration to file
        try:
            logger.info(f"Writing Telegraf configuration to {self.output_file_path}")
            with open(self.output_file_path, 'w', encoding='utf-8') as f:
                f.write(doc.as_string())
            logger.info(f"Configuration successfully written to {self.output_file_path}")
        except Exception as e:
            logger.error(f"Error writing configuration file: {e}", exc_info=True)

    def run(self) -> None:
        """
        Orchestrates the entire process of generating the Telegraf configuration.
        """
        self._start_time = time.time()
        logger.info("Starting Telegraf MQTT JSON configuration generation...")

        try:
            self.generate_telegraf_config()
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        finally:
            total_duration: float = time.time() - self._start_time
            logger.info(f"Process finished. Total time: {total_duration:.2f} seconds.")
            logger.info("--- Generation Summary ---")
            logger.info(f"Total rows processed: {self._total_rows_processed}")
            logger.info(f"Total topics configured: {self._total_topics_configured}")
            logger.info(f"Configuration file: {self.output_file_path}")
            logger.info("-------------------------")