from authlib.integrations.flask_client import OAuth
from .config import (
    GITHUB_OAUTH_CLIENT_ID,
    GITHUB_OAUTH_CLIENT_SECRET,
    GITHUB_OAUTH_ACCESS_TOKEN_URL,
    GITHUB_OAUTH_AUTHORIZE_URL,
    GITHUB_OAUTH_API_BASE_URL,
)

oauth = OAuth()
oauth.register(
    name='github',
    client_id=GITHUB_OAUTH_CLIENT_ID,
    client_secret=GITHUB_OAUTH_CLIENT_SECRET,
    access_token_url=GITHUB_OAUTH_ACCESS_TOKEN_URL,
    access_token_params=None,
    authorize_url=GITHUB_OAUTH_AUTHORIZE_URL,
    authorize_params=None,
    api_base_url=GITHUB_OAUTH_API_BASE_URL,
    # client_kwargs={'scope': 'user:email'},
)