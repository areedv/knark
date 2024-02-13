"""
Client interface to :class: KnarkConfig class
"""

import argparse
import time
from queue import Queue

import cv2
import imutils
import paho.mqtt.client as mqtt
from numpy import asarray
from PIL import Image
from pyzbar.pyzbar import decode

from conf import KnarkConfig
from cons import DEFAULT_CONFIG, DEFAULT_CONFIG_FILE

# from qr import KnarkQrDecode


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


def scanner(client, camera):
    vs = cv2.VideoCapture(0)
    print("stream url for scanner:" + client.streams[camera])
    time.sleep(2.0)
    found = set()

    while camera in client.streams:
        ret, frame = vs.read()
        # print("Class of frame:" + str(type(frame)))
        frame = imutils.resize(frame, width=1200)
        barcodes = decode(frame)
        for barcode in barcodes:
            (x, y, w, h) = barcode.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            # the barcode data is a bytes object so if we want to draw it
            # on our output image we need to convert it to a string first
            barcode_data = barcode.data.decode("utf-8")
            barcode_type = barcode.type
            # draw the barcode data and barcode type on the image
            text = "{} ({})".format(barcode_data, barcode_type)
            cv2.putText(
                frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2
            )
            # if the barcode text is currently not in our CSV file, write
            # the timestamp + barcode to disk and update the set
            if barcode_data not in found:
                client.publish(conf.of.client.publish_root_topic, barcode_data)
                found.add(barcode_data)

        cv2.imshow("Barcode scanner", frame)
    cv2.destroyAllWindows()
    vs.release()


def on_message(client, userdata, message):

    payload = str(message.payload.decode("utf-8"))
    camera = topic_stream(message.topic)
    stream_url = conf.of.client.video_stream_base_url + camera
    # print("Now on_message")
    # print("Message is: " + payload)
    # prWint("Camera is: " + camera)
    if payload == "OFF":
        if camera in client.streams:
            stream = client.streams.pop(camera)
            print("Closing and removing stream: ", stream)
        else:
            print("Cannot remove stream that does not exist")
    if payload == "ON":
        if camera in client.streams:
            print("Cannot add stream that is currently streaming")
        else:
            client.streams[camera] = stream_url
            print("Opening stream on ", camera)
            print("Current stream(s):", client.streams)
            scanner(client, camera)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.connected_flag = True
        client.subscribe(conf.of.client.subscribe_root_topic)
    else:
        client.bad_connection_flag = True


def main():
    """
    Main entrypoint for client
    """
    # args = process_cmdargs()
    mqtt.Client.connected_flag = False
    mqtt.Client.bad_connection_flag = False
    mqtt.Client.streams = {}
    client = mqtt.Client(conf.of.client.id)

    # setattr(client, "connected_flag", False)
    # setattr(client, "bad_connection_flag", False)

    # client = mqtt.Client(conf.of.client.id)
    client.on_log = on_log
    client.on_connect = on_connect
    client.on_message = on_message
    client.loop_start()
    try:
        client.connect(conf.of.mqtt.host, conf.of.mqtt.port)
    except:
        print("Connection failed")
        exit(1)

    while not client.connected_flag:
        print("Waiting for connection")
        time.sleep(1)
    client.publish(conf.of.client.publish_root_topic, "qr-code.png")

    print(str(conf.of.client.subscribe_root_topic))
    time.sleep(30)
    client.loop_stop()

    # print("DEFAULT_CONFIG: " + str(DEFAULT_CONFIG))
    # print("mqtt_host: " + str(conf.of.mqtt.host))
    # print("mqtt_port: " + str(conf.of.mqtt.port))
    #
    # print("QR data: " + str(decode.qr_data))
    # print("QR type: " + str(decode.qr_orientation))
    #


if __name__ == "__main__":
    main()
