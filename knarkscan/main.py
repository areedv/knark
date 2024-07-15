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

    parser.add_argument(
        "-l",
        "--log-level",
        help="Set log level, one of "
        + "NOTSET, DEBUG, INFO, WARNING, ERROR or CRITICAL. "
        + "This argument overrides whatever set in the config file",
    )
    return parser.parse_args()


q = Queue()
exit_worker = threading.Event()
args = process_cmdargs()
conf = KnarkConfig(args.config_file)
log_level = args.log_level
log_level_source = "command line argument"
if not log_level:
    log_level = conf.of.client.log_level
    log_level_source = args.config_file
numeric_level = getattr(logging, log_level.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError(f"Invalid log level: '{log_level}' found in '{log_level_source}'")
logger = logging.getLogger("knarkscan")
logger.setLevel(numeric_level)
ch = logging.StreamHandler()
ch.setLevel(numeric_level)
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
        logger.debug(f"Got admin request '{payload}'")
        q.put({"stream_url": "admin", "payload": payload, "cam": None})
    else:
        camera = topic_stream(message.topic)
        stream_url = conf.of.client.video_stream_base_url + camera
        q.put({"stream_url": stream_url, "payload": payload, "cam": camera})


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        client.connected_flag = True
        logger.info("Client connected")
        client.subscribe(conf.of.client.subscribe_root_topic)
        client.subscribe(conf.of.client.subscribe_admin_topic)
    else:
        client.bad_connection_flag = True


def on_disconnect(client, userdata, flags, reason_code, properties):
    logger.info("Disconnecting")
    logger.debug(f"DisConnected reason code: '{str(reason_code)}'")
    exit_worker.set()
    client.loop_stop()


def worker(conf, client):
    instances = threading.local()
    instances.value = {}
    logger.debug(f"worker: started with {threading.active_count()} threads")
    while True:
        if exit_worker.is_set():
            logger.debug(f"worker: exit requested")
            break
        if not q.empty():
            data = q.get()
            stream_url = data["stream_url"]
            payload = data["payload"]
            cam = data["cam"]
            if payload == "ON":
                logger.debug(f"worker: Notified that motion started on {cam}")
                logger.debug(
                    f"worker: {threading.active_count()} threads prior to scanning"
                )
                vs = KnarkVideoStream(stream_url, client).scan(conf, cam)
                instances.value[stream_url] = vs
                logger.debug(
                    f"worker: {threading.active_count()} threads when scanning"
                )
            if payload == "OFF":
                logger.debug(f"worker: Notified that motion ended on {cam}")
                if stream_url in instances.value:
                    instance = instances.value.pop(stream_url)
                    instance.stop()
                    logger.debug(
                        f"worker: {threading.active_count()} threads after scannig stopped"
                    )
                else:
                    logger.debug("worker: Skipped premature motion event")
            if payload == "STOP" and stream_url == "admin":
                client.disconnect()


def main():
    """
    Main entrypoint for client
    """
    logger.info("Start scanning for knark")
    logger.debug(f"main: {threading.active_count()} active threads initially")
    mqtt.Client.connected_flag = False
    mqtt.Client.bad_connection_flag = False
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=conf.of.client.id,
    )

    logger.debug(f"main: Starting worker")
    t = threading.Thread(target=worker, args=(conf, client))
    t.start()
    logger.debug(f"main: {threading.active_count()} active threads")

    client.on_log = on_log
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    logger.debug(f"main: Starting MQ client loop")
    client.loop_start()
    logger.debug(f"main: {threading.active_count()} active threads")

    try:
        client.connect(conf.of.mqtt.host, conf.of.mqtt.port)
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        exit(1)

    while not client.connected_flag:
        logger.info("Waiting for connection")
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
