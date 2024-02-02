"""
Client interface to :class: KnarkConfig class
"""

import argparse
import time

import paho.mqtt.client as mqtt
from PIL import Image
from numpy import asarray
from pyzbar.pyzbar import decode

from conf import KnarkConfig
from cons import DEFAULT_CONFIG, DEFAULT_CONFIG_FILE

#from qr import KnarkQrDecode


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

def on_message(client, userdata, message):

    def qr_decode(image_file):
        try:
            with open(image_file):
                img = asarray(Image.open(image_file))
                res = decode(img)
        except FileNotFoundError:
            print("Requested image file does not exist: " + image_file)
            res = list()
        
        return res
    
    res = qr_decode(str(message.payload.decode("utf-8")))
    for qr in res:
        #print(qr.data)
        client.publish("knark/qr", qr.data)

    print("message received ", str(message.payload.decode("utf-8")))
    print("message topic = ", message.topic)
    print("message qos ", message.qos)
    print("message retain flag ", message.retain)



def main():
    """
    Main entrypoint for client
    """
    args = process_cmdargs()
    conf = KnarkConfig(args.config_file)
    #decode = KnarkQrDecode("qr-code.png")


    client = mqtt.Client(conf.of.client.id)
    client.on_message = on_message
    client.connect(conf.of.mqtt.host, conf.of.mqtt.port)
    client.loop_start()
    client.subscribe(conf.of.client.topic)
    client.publish(conf.of.client.topic, "qr-code.png")
    time.sleep(2)
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
