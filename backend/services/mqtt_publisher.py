"""
MQTT event publisher for external integrations
"""
import logging
import json
import threading
from typing import Dict, Optional
import paho.mqtt.client as mqtt
from backend.config.config import get_config

logger = logging.getLogger(__name__)


class MQTTPublisher:
    def __init__(self):
        self.config = get_config()
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.lock = threading.Lock()
        
        if self.config.mqtt.enabled:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize MQTT client"""
        try:
            self.client = mqtt.Client()
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            
            broker = self.config.mqtt.broker
            port = self.config.mqtt.port
            
            logger.info(f"Connecting to MQTT broker: {broker}:{port}")
            self.client.connect_async(broker, port, 60)
            self.client.loop_start()
        
        except Exception as e:
            logger.error(f"Error initializing MQTT client: {e}")
            self.client = None

    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when client connects"""
        if rc == 0:
            self.connected = True
            logger.info("Connected to MQTT broker")
        else:
            self.connected = False
            logger.error(f"Failed to connect to MQTT broker: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback for when client disconnects"""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection: {rc}")

    def publish_event(self, event: Dict):
        """Publish event to MQTT"""
        if not self.config.mqtt.enabled or not self.client or not self.connected:
            return

        try:
            camera_id = event.get('camera_id')
            rule_type = event.get('rule_type')
            
            # Topic: sentinelsight/events/{camera_id}/{rule_type}
            topic = f"{self.config.mqtt.topic_prefix}/events/{camera_id}/{rule_type}"
            
            # Payload
            payload = {
                'event_id': event.get('id'),
                'camera_id': camera_id,
                'timestamp': event.get('timestamp').isoformat() if event.get('timestamp') else None,
                'rule_type': rule_type,
                'object_type': event.get('object_type'),
                'confidence': event.get('confidence'),
                'priority': event.get('priority'),
                'status': event.get('status'),
                'metadata': event.get('metadata')
            }
            
            # Publish
            result = self.client.publish(
                topic,
                json.dumps(payload),
                qos=self.config.mqtt.qos
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published event {event.get('id')} to MQTT: {topic}")
            else:
                logger.warning(f"Failed to publish event to MQTT: {result.rc}")
        
        except Exception as e:
            logger.error(f"Error publishing event to MQTT: {e}")

    def publish_camera_status(self, camera_id: int, status: str, fps: float = 0.0):
        """Publish camera status update"""
        if not self.config.mqtt.enabled or not self.client or not self.connected:
            return

        try:
            topic = f"{self.config.mqtt.topic_prefix}/status/{camera_id}"
            payload = {
                'camera_id': camera_id,
                'status': status,
                'fps': fps,
                'timestamp': None  # Will be set by receiver
            }
            
            self.client.publish(topic, json.dumps(payload), qos=self.config.mqtt.qos)
        
        except Exception as e:
            logger.error(f"Error publishing camera status to MQTT: {e}")

    def is_connected(self) -> bool:
        """Check if MQTT client is connected"""
        return self.connected

    def disconnect(self):
        """Disconnect MQTT client"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")


# Global MQTT publisher instance
_mqtt_publisher = None


def get_mqtt_publisher() -> MQTTPublisher:
    """Get global MQTT publisher instance"""
    global _mqtt_publisher
    if _mqtt_publisher is None:
        _mqtt_publisher = MQTTPublisher()
    return _mqtt_publisher
