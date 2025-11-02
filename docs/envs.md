# Round Review - Environment Variables

> [!WARNING]
> The documentation is under creation and it will be subject to frequent changes


## Round Review (app)

> [!NOTE]
> Copy the environment file inside `envs/template.rr-app.env` and create `envs/rr-app.env`

| Variable name | Description | Default | Required to change |
|---|---|---|---|
| `RR_APP_NAME` | Application display name visible in the homepage | "Round Review" | No |
| `RR_ADMIN_NAME` | Default administrator username | "admin" | No - Note that you cannot change the name afterwards |
| `RR_ADMIN_EMAIL` | Default administrator email | "admin@system.com" | No — you can change to a real admin email afterwards |
| `RR_DEFAULT_USER_PASSWORD` | Default password for created users (used when not provided) | Random password (generated at runtime) | No |
| `DEBUG` | Enable debug logging and development mode | None (unset) | No — let empty in production and `1` or `True` in development |


### Github OAuth App

> [!NOTE]
> You can enable Github Authentication for your users using the environment variables in this section.

| Variable name | Description | Default | Required to change|
|---|---|---|---|
| `GITHUB_OAUTH_ENABLED` | Enable GitHub OAuth login | False | Yes - `True` if you want to enable GitHub login; otherwise keep False |
| `GITHUB_OAUTH_CLIENT_ID` | GitHub OAuth app client ID | None | Yes - if `GITHUB_OAUTH_ENABLED` = True |
| `GITHUB_OAUTH_CLIENT_SECRET` | GitHub OAuth app client secret | None | Yes - if `GITHUB_OAUTH_ENABLED` = True |
| `GITHUB_OAUTH_ACCESS_TOKEN_URL` | OAuth access token endpoint | https://github.com/login/oauth/access_token | No — change only for GitHub enterprise/custom endpoints |
| `GITHUB_OAUTH_AUTHORIZE_URL` | OAuth authorize endpoint | https://github.com/login/oauth/authorize | No — change only for GitHub enterprise/custom endpoints |
| `GITHUB_OAUTH_API_BASE_URL` | GitHub API base URL | https://api.github.com/ | No — change only for GitHub enterprise/custom endpoints |

## PDF Notary Bot (plugin)

> [!NOTE]
> Copy the environment file inside `envs/template.rr-pdf-notary-bot.env` and create `envs/rr-pdf-notary-bot.env`

| Variable name | Description | Default | Required to change |
|---|---|---|---|
| `API_KEY` | API key of a RoundReview user (used to authenticate plugin calls to the app) | None | Yes — required for operation; keep it secret |
| `API_BASE_URL` | RoundReview application API endpoint the plugin calls | "http://roundreview_app:8080/api" | Yes — set to your app's reachable API URL (internally via Docker or externally) |
| `PLUGIN_BASE_URL` | Public/base URL where the plugin is served; it is used to create the URL in the reviews. | "http://localhost:8081" | Yes - change this to the reachable base url + port (no forward slash) |
| `PLUGIN_KEY_PASSPHRASE` | Passphrase for the plugin private key (if any) | None | No - if your key certificate is NOT encrypted; keep it secret |
| `PLUGIN_KEY_PATH` | Filesystem path to private key used for signing | /certs/key.pem | No — ensure path matches your container/host path |
| `PLUGIN_CERT_PATH` | Filesystem path to certificate used for signing | /certs/cert.pem | No — ensure path matches your container/host path |
| `PLUGIN_SIGN_IMAGE_PATH` | Optional image used to stamp signed PDFs | None | Optional — set if you want a visible signature image and change it according to your container/host path (e.g. `/certs/sign.png`) |
| `PLUGIN_SIGNED_PDFS_FOLDER` | Folder where signed PDFs are stored | /signed_pdfs | No — change it according to your container/host path |
| `DEBUG` | Enable debug logging and development mode for the plugin | None (unset) | No — let empty in production and `1` or `True` in development |