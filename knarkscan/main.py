"""
Client interface to classes :class: KnarkConfig and :class:
KnarkVideoStream.
"""

import argparse
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


def on_log(client, userdata, level, buf):
    print("LOG: ", buf)


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
    camera = topic_stream(message.topic)
    stream_url = conf.of.client.video_stream_base_url + camera
    q.put({"stream_url": stream_url, "payload": payload})
    print(f"Got payload {payload} on topic {message.topic}")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.connected_flag = True
        print("Client connected :-)")
        client.subscribe(conf.of.client.subscribe_root_topic)
    else:
        client.bad_connection_flag = True


def on_disconnect(client, userdata, rc=0):
    print("Disconnecting ;-o")
    # logging.debug("DisConnected result code " + str(rc))
    exit_worker.set()
    client.loop_stop()


def worker(conf):
    instances = threading.local()
    instances.value = {}
    while True:
        if not q.empty():
            data = q.get()
            stream_url = data["stream_url"]
            payload = data["payload"]
            if payload == "ON":
                print("Motion detected!")
                vs = KnarkVideoStream(stream_url).scan(conf)
                instances.value[stream_url] = vs
            if payload == "OFF":
                print("Stopped detecting motion!")
                if stream_url in instances.value:
                    instance = instances.value.pop(stream_url)
                    instance.stop()
                else:
                    print("Skipping None-existing instance")
            # print(f"All instances: {instances.value}")

        if exit_worker.is_set():
            break


def main():
    """
    Main entrypoint for client
    """

    t = threading.Thread(target=worker, args=(conf,))
    t.start()

    mqtt.Client.connected_flag = False
    mqtt.Client.bad_connection_flag = False
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    # client = mqtt.Client(conf.of.client.id)

    # client.on_log = on_log
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.loop_start()
    try:
        client.connect(conf.of.mqtt.host, conf.of.mqtt.port)
    except:
        print("Connection failed: ")
        exit(1)

    while not client.connected_flag:
        print("Waiting for connection")
        time.sleep(1)

    # time.sleep(180)
    #
    # exit_worker.set()
    # t.join()
    #
    # client.loop_stop()


if __name__ == "__main__":
    main()
