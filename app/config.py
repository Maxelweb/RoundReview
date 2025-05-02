import os
import logging

DEBUG = False
VERSION = "v0.1.0"
USER_SYSTEM_ID = 1
USER_SYSTEM_NAME = "_SYSTEM"
USER_SYSTEM_EMAIL = "system@local"
USER_ADMIN_NAME = os.environ.get('RR_ADMIN_NAME') or "admin"
USER_ADMIN_EMAIL = os.environ.get('RR_ADMIN_EMAIL') or "admin@system.com"
USER_DEFAULT_PASSWORD = os.environ.get('RR_DEFAULT_USER_PASSWORD') or "changeme!"
WEBSITE_URL = os.environ.get('RR_WEBSITE_URL') or "localhost"

logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s', level=logging.DEBUG if DEBUG else logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger("roundreview-logs")
