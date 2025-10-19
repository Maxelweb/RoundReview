import os
import logging

# ------ ENVIRONMENTS ------ 
DEBUG = os.environ.get('DEBUG') is not None or False

# ------ Defaults ------ 

PLUGIN_VERSION = "0.1.0"
PLUGIN_NAME = "example_bot"

# ------ Others ------ 
logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s', level=logging.DEBUG if DEBUG else logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(f"roundreview-{PLUGIN_NAME}")
