"""
Client interface to :class: KnarkConfig class
"""
import argparse
import paho.mqtt.client as mqtt
import time
from conf import KnarkConfig
from cons import DEFAULT_CONFIG, DEFAULT_CONFIG_FILE

def on_message(client, userdata, message):
    print("message received ", str(message.payload.decode("utf-8")))
    print("message topic = ", message.topic)
    print("message qos ", message.qos)
    print("message retain flag ", message.retain)

def process_cmdargs():
    """
    Process command line arguments

    :return: Processed parameters
    :rtype: argparse.Namespace
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
            '-c', '--config-file',
            default=DEFAULT_CONFIG_FILE,
            help="Path to configuration file (default: '%(default)s')"
    )
    return parser.parse_args()

def main():
    """
    Main entrypoint for client
    """
    args = process_cmdargs()
    conf = KnarkConfig(args.config_file)
    
    client = mqtt.Client("p2")
    client.on_message = on_message
    client.connect(conf.of.mqtt.host, conf.of.mqtt.port)
    client.loop_start()
    client.subscribe('hnikt/test')
    client.publish('hnikt/test', 'yes')
    time.sleep(4)
    client.loop_stop()

    print('DEFAULT_CONFIG: '+ str(DEFAULT_CONFIG))
    print('mqtt_host: '+ str(conf.of.mqtt.host))
    print('mqtt_port: '+ str(conf.of.mqtt.port))

if __name__ == "__main__":
    main()

