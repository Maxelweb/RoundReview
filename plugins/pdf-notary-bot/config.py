import os
import logging

# ------ ENVIRONMENTS ------ 
DEBUG = os.environ.get('DEBUG') is not None or False
API_KEY = os.environ.get('API_KEY') or None
API_BASE_URL = os.environ.get('API_BASE_URL') or None
PLUGIN_KEY_PASSPHRASE = os.environ.get('PLUGIN_KEY_PASSPHRASE') or None
PLUGIN_KEY_PATH = os.environ.get('PLUGIN_KEY_PATH') or "/certs/key.pem"
PLUGIN_CERT_PATH = os.environ.get('PLUGIN_CERT_PATH') or "/certs/cert.pem"
PLUGIN_SIGN_IMAGE_PATH = os.environ.get('PLUGIN_SIGN_IMAGE_PATH') or None

# ------ Defaults ------ 

PLUGIN_SIGNED_PDFS_FOLDER = os.environ.get('PLUGIN_SIGNED_PDFS_FOLDER') or "/signed_pdfs"
PLUGIN_BASE_URL = os.environ.get('PLUGIN_BASE_URL') or "localhost"
PLUGIN_VERSION = "0.1.0"
PLUGIN_NAME = "pdf_notary_bot"

# ------ Others ------ 
logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s', level=logging.DEBUG if DEBUG else logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(f"roundreview-{PLUGIN_NAME}")
