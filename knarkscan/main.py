"""
Client interface to classes :class: KnarkConfig and :class:
KnarkVideoStream.
"""

import argparse
import logging
import threading
import time
from queue import Queue

import paho.mqtt.client as mqtt
from conf import KnarkConfig
from cons import DEFAULT_CONFIG_FILE
from stream import KnarkVideoStream


def process_cmdargs():
    """
    Process command line arguments

    :return: Processed parameters
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config-file",
        default=DEFAULT_CONFIG_FILE,
        help="Path to configuration file (default: '%(default)s')",
    )
    return parser.parse_args()


q = Queue()
exit_worker = threading.Event()
args = process_cmdargs()
conf = KnarkConfig(args.config_file)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


def on_log(client, userdata, level, buf):
    logger.log(level, buf)


def topic_stream(topic):
    sep = "/"
    levels = topic.split(sep)
    # list start index is 0, stream is the one below the top level
    stream_level = len(levels) - 2
    if stream_level < 0:
        stream_level = 0

    return levels[stream_level]


def on_message(client, userdata, message):
    payload = str(message.payload.decode("utf-8"))
    if message.topic == conf.of.client.subscribe_admin_topic:
        q.put({"stream_url": "admin", "payload": payload, "cam": None})
    else:
        camera = topic_stream(message.topic)
        stream_url = conf.of.client.video_stream_base_url + camera
        q.put({"stream_url": stream_url, "payload": payload, "cam": camera})
        # print(f"Got payload {payload} on topic {message.topic}")
        client.publish(conf.of.client.publish_root_topic, f"{camera} said '{payload}'")


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        client.connected_flag = True
        print("Client connected :-)")
        client.subscribe(conf.of.client.subscribe_root_topic)
        client.subscribe(conf.of.client.subscribe_admin_topic)
    else:
        client.bad_connection_flag = True


def on_disconnect(client, userdata, flags, reason_code, properties):
    print("Disconnecting ;-o")
    # logging.debug("DisConnected result code " + str(rc))
    exit_worker.set()
    client.loop_stop()


def worker(conf, client):
    instances = threading.local()
    instances.value = {}
    while True:
        if exit_worker.is_set():
            break
        if not q.empty():
            data = q.get()
            stream_url = data["stream_url"]
            payload = data["payload"]
            cam = data["cam"]
            if payload == "ON":
                logger.info("Motion detected!")
                vs = KnarkVideoStream(stream_url, client).scan(conf, cam)
                instances.value[stream_url] = vs
            if payload == "OFF":
                logger.info("Stopped detecting motion!")
                if stream_url in instances.value:
                    instance = instances.value.pop(stream_url)
                    instance.stop()
                else:
                    print("Skipping None-existing instance")
            if payload == "STOP" and stream_url == "admin":
                client.disconnect()


def main():
    """
    Main entrypoint for client
    """
    # logger = logging.getLogger(__name__)
    # logger.setLevel(logging.INFO)
    # ch = logging.StreamHandler()
    # ch.setLevel(logging.INFO)
    # formatter = logging.Formatter(
    #     "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    # )
    # ch.setFormatter(formatter)
    # logger.addHandler(ch)

    logger.info("Start scanning for knark")

    mqtt.Client.connected_flag = False
    mqtt.Client.bad_connection_flag = False
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=conf.of.client.id,
    )

    t = threading.Thread(target=worker, args=(conf, client))
    t.start()

    client.on_log = on_log
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    client.loop_start()

    try:
        client.connect(conf.of.mqtt.host, conf.of.mqtt.port)
    except Exception as e:
        print(f"Connection failed: {e}")
        exit(1)

    while not client.connected_flag:
        print("Waiting for connection")
        time.sleep(1)

    # client.loop_forever()
    # time.sleep(60)
    # exit_worker.set()
    # t.join()
    # client.loop_stop()
    # client.disconnect()
    #


if __name__ == "__main__":
    main()
