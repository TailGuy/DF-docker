import os
import time
import datetime
import logging
import csv
from typing import List, Dict, Any, cast
from tomlkit import document, table, aot, comment, nl, integer, boolean

logger: logging.Logger = logging.getLogger("telegraf_manager.telegraf_mqtt_config_generator")

MQTT_TOPIC_EXCLUSION_CHARS: List[str] = [
    "+",    # Single-level wildcard character - illegal in topic names
    "#",    # Multi-level wildcard character - illegal in topic names
    "*",    # SMF wildcard character - causes interoperability issues
    ">",    # SMF wildcard character - causes interoperability issues
    "$",    # When used at start of topic - reserved for server implementation
    "!",    # When used at start of topic - causes interoperability issues in SMF (topic exclusions)
    # " "     # Space character - avoid as best practice to prevent parsing issues
]

class TelegrafMQTTConfigGenerator:
    """
    Generates Telegraf configuration for MQTT inputs from a CSV file,
    with proper MQTT topic validation and sanitization to ensure compatibility.
    Exports MQTT data to InfluxDB.
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
        self._total_nodes_processed: int = 0
        self._topics_sanitized: int = 0
    
    def validate_mqtt_topic(self, topic_name: str) -> bool:
        """
        Validates an MQTT topic name against character restrictions.
        Returns True if valid, False otherwise.
        """
        # Check for reserved characters
        if any(char in topic_name for char in MQTT_TOPIC_EXCLUSION_CHARS):
            return False
        
        # Check for leading $ (allowed only for system topics)
        if topic_name.startswith("$") and not (
            topic_name.startswith("$SYS/") or 
            topic_name.startswith("$share/") or
            topic_name.startswith("$noexport/")
        ):
            return False
        
        # Check length restriction (250 bytes max per Solace docs)
        if len(topic_name.encode('utf-8')) > 250:
            return False
        
        # Check for level count restriction (128 levels max per Solace docs)
        if len(topic_name.split('/')) > 128:
            return False
            
        return True
    
    def sanitize_mqtt_topic(self, topic_name: str) -> str:
        """
        Sanitizes an MQTT topic name by replacing restricted characters.
        """
        # Replace restricted characters
        sanitized_name: str = topic_name
        for char in MQTT_TOPIC_EXCLUSION_CHARS:
            sanitized_name = sanitized_name.replace(char, '_')
        
        # Handle leading $ if not a system topic
        if sanitized_name.startswith("$") and not (
            sanitized_name.startswith("$SYS/") or 
            sanitized_name.startswith("$share/") or
            sanitized_name.startswith("$noexport/")
        ):
            sanitized_name = "_" + sanitized_name[1:]
            
        return sanitized_name
    
    def generate_telegraf_config(self) -> None:
        """
        Process the CSV file of MQTT inputs and generate a Telegraf configuration
        with proper MQTT topic validation/sanitization and InfluxDB output settings.
        """
        # Check if CSV file exists
        if not os.path.exists(self.csv_file_path):
            logger.error(f"Error: CSV file '{self.csv_file_path}' not found.")
            return
        
        # Read nodes from CSV file
        nodes: List[Dict[str, str]] = []
        try:
            logger.info(f"Reading nodes from CSV file: {self.csv_file_path}")
            with open(self.csv_file_path, 'r', encoding='utf-8') as csvfile:
                reader: csv.DictReader[str] = csv.DictReader(csvfile)
                for row in reader:
                    # Ensure required columns exist
                    if 'MQTTInputName' in row:
                        mqtt_input_name: str = row['MQTTInputName']
                        
                        # Generate MQTT topic name using the MQTTInputName and validate/sanitize it
                        mqtt_topic: str = f"telegraf/opcua/{mqtt_input_name}"
                        if not self.validate_mqtt_topic(mqtt_topic):
                            original_topic: str = mqtt_topic
                            mqtt_topic = self.sanitize_mqtt_topic(mqtt_topic)
                            self._topics_sanitized += 1
                            logger.warning(f"MQTT topic '{original_topic}' contains restricted characters. "
                                          f"Using sanitized topic: '{mqtt_topic}'")
                        
                        nodes.append({
                            'mqtt_input_name': mqtt_input_name,
                            'mqtt_topic': mqtt_topic
                        })
                        self._total_nodes_processed += 1
                    else:
                        missing_keys = [key for key in ['MQTTInputName'] if key not in row]
                        logger.warning(f"Skipping row missing required keys: {missing_keys}. Row: {row}")
        except csv.Error as e:
            logger.error(f"CSV parsing error: {e}", exc_info=True)
            return
        except Exception as e:
            logger.error(f"Unexpected error reading CSV: {e}", exc_info=True)
            return
        
        if not nodes:
            logger.warning("No valid MQTT inputs found in CSV file.")
            return
        
        # Create TOML document
        doc = document()
        doc.add(comment(f"# Generated at {datetime.datetime.now().isoformat()}"))
        doc.add(comment("# Telegraf Configuration for MQTT Inputs"))
        doc.add(comment("# Generated from CSV file"))
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
        agent.add("omit_hostname", boolean("true"))
        doc.add("agent", agent)
        doc.add(nl())
        
        # Add inputs section
        doc.add(comment("###############################################################################"))
        doc.add(comment("#                            INPUT PLUGINS                                    #"))
        doc.add(comment("###############################################################################"))
        doc.add(nl())
        doc.add(comment("# Read data from MQTT topics"))
        
        inputs = table()
        mqtt_aot: List[Any] = cast(List[Any], aot())
        for node in nodes:
            mqtt_consumer = table()
            mqtt_consumer.add("servers", [self.mqtt_broker])
            mqtt_consumer.add("topics", [node['mqtt_topic']])
            mqtt_consumer.add("name_override", "opcua")
            mqtt_consumer.add("topic_tag", "mqtt_topic")
            mqtt_consumer.add("data_format", "value")
            mqtt_consumer.add("data_type", "float")
            mqtt_aot.append(mqtt_consumer)
        inputs.add("mqtt_consumer", mqtt_aot)
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
        influxdb_v2.add("bucket", "mqttinput")
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
        logger.info("Starting Telegraf configuration generation...")
        
        try:
            # Generate the Telegraf configuration
            self.generate_telegraf_config()
            
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        finally:
            total_duration: float = time.time() - self._start_time
            logger.info(f"Process finished. Total time: {total_duration:.2f} seconds.")
            logger.info("--- Generation Summary ---")
            logger.info(f"Total nodes processed: {self._total_nodes_processed}")
            logger.info(f"MQTT topics sanitized: {self._topics_sanitized}")
            logger.info(f"Configuration file: {self.output_file_path}")
            logger.info("-------------------------")