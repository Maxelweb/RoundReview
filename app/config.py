import os
import logging
import secrets

# ------ Environment Variables ------ 
DEBUG = os.environ.get('DEBUG') is not None or False
USER_ADMIN_NAME = os.environ.get('RR_ADMIN_NAME') or "admin"
USER_ADMIN_EMAIL = os.environ.get('RR_ADMIN_EMAIL') or "admin@system.com"
USER_DEFAULT_PASSWORD = os.environ.get('RR_DEFAULT_USER_PASSWORD') or secrets.token_hex(16)
WEBSITE_URL = os.environ.get('RR_WEBSITE_URL') or "localhost"

GITHUB_OAUTH_ENABLED = os.environ.get('GITHUB_OAUTH_ENABLED') is not None or False
GITHUB_OAUTH_CLIENT_ID = os.environ.get('GITHUB_OAUTH_CLIENT_ID') or None
GITHUB_OAUTH_CLIENT_SECRET = os.environ.get('GITHUB_OAUTH_CLIENT_SECRET') or None
GITHUB_OAUTH_ACCESS_TOKEN_URL = os.environ.get('GITHUB_OAUTH_ACCESS_TOKEN_URL') or 'https://github.com/login/oauth/access_token'
GITHUB_OAUTH_AUTHORIZE_URL = os.environ.get('GITHUB_OAUTH_AUTHORIZE_URL') or 'https://github.com/login/oauth/authorize'
GITHUB_OAUTH_API_BASE_URL = os.environ.get('GITHUB_OAUTH_API_BASE_URL') or 'https://api.github.com/'


# ------ Defaults ------ 
VERSION = "0.2.0"
USER_SYSTEM_ID = 1
USER_SYSTEM_NAME = "_SYSTEM"
USER_SYSTEM_EMAIL = "system@local"
SYSTEM_MAX_UPLOAD_SIZE_MB = 2  # Default max upload size for objects in Megabytes

# ------ Others ------ 
logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s', level=logging.DEBUG if DEBUG else logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger("roundreview-logs")
