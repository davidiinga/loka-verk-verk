import asyncio
from umqtt.robust import MQTTClient


class AsyncMQTT:
    """
    Async wrapper around the umqtt.simple MQTTClient
    """

    # MQTTClient instance
    client: MQTTClient
    callbacks: dict[str, list]
    callback_buffer: list[tuple[str, bytes]]
    loop_task: asyncio.Task | None

    def __init__(
        self,
        client_id: str,
        broker: str,
        port: int = 0,
        will_topic: str | None = None,
        will_message: bytes | None = None,
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
        self.client = MQTTClient(client_id,  broker, port, keepalive=20)
        self.callbacks = {}
        self.callback_buffer = []
        self.loop_task = None

        if will_topic and will_message:
            self.client.set_last_will(will_topic, will_message, retain=will_retain)

        self.client.set_callback(self._on_rx)
        

    def connect(self):
        """
        Connect to the MQTT broker.
        """
        print("MQTT connecting")
        self.client.connect()
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
        # Check for new messages
        # This will call the _on_rx callback for each message received.
        while self.client.check_msg() is not None:

            # Process any message in the callback buffer.
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

    def _on_rx(self, topic: bytes, message: bytes):
        """
        Internal callback handler for each message received.
        If we have callbacks registered for the topic push the message to the callback buffer.

        Parameters:
            topic (str): The topic the message was published to.
            message (bytes): The contents of the message that was published.
        """
        topic_str = topic.decode("utf-8")
        print(f"Received message on topic '{topic_str}': {message}")
        if topic_str in self.callbacks:
            self.callback_buffer.append((topic_str, message))

