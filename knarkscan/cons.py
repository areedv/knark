"""
Module holding constants
"""

from addict import Dict

DEFAULT_CONFIG_FILE = "/config/config.yaml"
DEFAULT_LOG_LEVEL = "INFO"

# Default configuration when file has none
DEFAULT_CONFIG = Dict(mqtt=dict(port=1883, tls=False))
