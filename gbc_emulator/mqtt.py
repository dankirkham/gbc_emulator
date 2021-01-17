import json
import threading
import time
import paho.mqtt.client as mqtt

TOPIC = "gbc_emulator"

class Mqtt(threading.Thread):
    def __init__(self, host, port=1883):
        super().__init__()
        self.daemon = True

        self.callbacks = {}

        self.connected = False

        # Set up MQTT client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.connect(host, port, 60)

    def run(self):
        while True:
            self.client.loop()
            time.sleep(0.001)

    def publish(self, topic, message):
        self.client.publish(TOPIC + "/" + topic, json.dumps(message))

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, _, __, rc):
        print("Connected to MQTT with result code " + str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(TOPIC + "/#")

        self.connected = True

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, _, __, msg):
        if msg.topic in self.callbacks:
            message = json.loads(msg.payload)
            for callback in self.callbacks[msg.topic]:
                callback(message)

    def on(self, topic, callback):
        if topic not in self.callbacks:
            self.callbacks[TOPIC + "/" + topic] = []
        self.callbacks[TOPIC + "/" + topic].append(callback)

if __name__ == "__main__":
    print("Starting standalone MQTT agent...")
    mqtt_client = Mqtt("127.0.0.1")

    mqtt_client.on("gbc_emulator/monitor", print)

    mqtt_client.start()

    while True:
        pass
