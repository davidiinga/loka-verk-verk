import paho.mqtt.client as mqtt
import asyncio

class MQTT_Client:
    """
    Async wrapper around the paho-mqtt MQTTClient.
    """

    def __init__(
        self,
        client_id: str,
        broker: str,
        port: int = 1883,
        will_topic: str = None,
        will_message: bytes = None,
        will_retain: bool = False,
    ):
        """
        Construct a new AsyncMQTT instance.

        Parameters:
            client_id (str): The client ID to use.
            broker (str): The address of the broker to connect to.
            port (int): The port to connect to the broker on.
            will_topic (str): The topic to publish the last will message to if set.
            will_message (bytes): The last will message to publish if set.
            will_retain (bool): Whether the last will message should be retained by the broker.
        """
        self.client = mqtt.Client(client_id = client_id)
        self.callbacks = {}
        self.callback_buffer = []
        self.loop_task = None

        if will_topic and will_message:
            self.client.will_set(will_topic, will_message, retain=will_retain)

        self.client.on_message = self._on_rx
        self.client.on_connect = self._on_connect

        self.broker = broker
        self.port = port

    def _on_connect(self, client, userdata, flags, rc):
        print(f"Connected to MQTT broker with result code {rc}")

    def connect(self):
        """
        Connect to the MQTT broker.
        """
        print("MQTT connecting")
        self.client.connect(self.broker, self.port)
        self.client.loop_start()
        print("MQTT connected")

    def publish(self, topic: str, message: bytes, qos: int = 0, retain: bool = False):
        """
        Publish a message to a given topic.

        Parameters:
            topic (str): The topic to publish to.
            message (bytes): The message to publish.
            qos (int): The quality of service level to use.
            retain (bool): Whether the message should be retained by the broker.
        """
        print(f"Publishing message to topic '{topic}': {message}")
        self.client.publish(topic, message, qos=qos, retain=retain)

    def subscribe(self, topic: str, callback_fn, qos: int = 0):
        """
        Subscribe to a given topic and register a callback function to be called when a message is received.

        Parameters:
            topic (str): The topic to subscribe to.
            callback_fn (callable[[str, bytes] Awaitable[Any]]): The callback function to call when a message is received.
            qos (int): The quality of service level to use.
        """
        print(f"Subscribing to topic '{topic}'")
        if topic not in self.callbacks:
            self.callbacks[topic] = []

        self.callbacks[topic].append(callback_fn)
        self.client.subscribe(topic, qos=qos)

    async def poll(self, ignore_errors: bool = True):
        """
        Poll for new messages and call the appropriate callback functions.

        Parameters:
            ignore_errors (bool): Whether to ignore any exceptions that occur while processing messages.
        """
        while True:
            while self.callback_buffer:
                topic, message = self.callback_buffer.pop(0)
                if topic in self.callbacks:
                    for callback in self.callbacks[topic]:
                        try:
                            await callback(topic, message)
                        except Exception as e:
                            print(f"Error in MQTT callback for topic '{topic}': {e}")
                            if not ignore_errors:
                                raise e
            await asyncio.sleep(0.1)

    async def start(self, interval: float = 1.0, ignore_errors: bool = True):
        """
        Start a background task that polls for new messages at a given interval. 

        Parameters:
            interval (float): The interval at which to poll for new messages.
            ignore_errors (bool): Whether to ignore any exceptions that occur while processing messages.
        """
        if self.loop_task:
            raise RuntimeError("The MQTT client is already running.")

        async def poll_loop():
            while True:
                await self.poll(ignore_errors)
                await asyncio.sleep(interval)

        self.loop_task = asyncio.create_task(poll_loop())
        return self.loop_task

    def _on_rx(self, client, userdata, msg):
        """
        Internal callback handler for each message received.
        If we have callbacks registered for the topic push the message to the callback buffer.

        Parameters:
            msg (MQTTMessage): The message received.
        """
        topic_str = msg.topic
        message = msg.payload
        print(f"Received message on topic '{topic_str}': {message}")
        if topic_str in self.callbacks:
            self.callback_buffer.append((topic_str, message))



async def main():
    client = MQTT_Client("Paho-test-client", "10.201.48.114")
    client.connect()

    await client.start()

    while True:
        await asyncio.sleep(1) 

if __name__ == "__main__":
    asyncio.run(main())
