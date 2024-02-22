import sys

import yaml
from addict import Dict
from schema import Optional, Schema, SchemaError

import cons


class KnarkConfig:

    def _get_schema(self):
        """
        Return schema for config file.

        :return: The schemam to use when validateing the config file
        :rtype: Schema
        """

        return Schema(
            {
                "client": {
                    "id": str,
                    "subscribe_root_topic": str,
                    "publish_root_topic": str,
                    "video_stream_base_url": str,
                    "scan_snapshot": bool,
                    "scan_barcode": bool,
                    "scan_datamatrix": bool,
                    "snapshot_file_prefix": str,
                    "snapshot_path": str,
                },
                "mqtt": {
                    "host": str,
                    "port": int,
                    Optional("username", default=""): str,
                    Optional("password", default=""): str,
                },
            }
        )

    @staticmethod
    def _read_config(config_file):
        """
        Reads KNARK configuration file.

        :param str config_file: Name of configuration file
        :return str: Configuration file content
        """
        with open(config_file, "r") as file:
            conf = yaml.safe_load(file)

        return conf

    @property
    def of(self):
        """
        Return the configuration state

        :return: Configuration state
        :rtype: :class: `Dict`
        """
        return self._config

    def __init__(self, config_file):
        try:
            with open(config_file):
                config = self._read_config(config_file)
        except FileNotFoundError:
            print("File does not exist: " + config_file)
            sys.exit("Quitting due to missing configuration")

        try:
            config = self._get_schema().validate(config)
        except SchemaError as e:
            print("Configuration is not valid: " + str(e))
            sys.exit("Please fix configuration. Quitting")

        self._config = Dict(config)
