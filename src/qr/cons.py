"""
Module holding constants
"""

from addict import Dict

DEFAULT_CONFIG_FILE = './conf.yaml'

# Default configuration when file has none
DEFAULT_CONFIG = Dict(
        mqtt=dict(
            port=1883,
            tls=False
        )
)

